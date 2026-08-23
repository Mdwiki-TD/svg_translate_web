---
name: flask-sqlalchemy
description: >
    Use this skill whenever building a Flask app with a database, defining models,
    or performing CRUD operations. Trigger immediately when the user mentions Flask,
    SQLAlchemy, a database with Python, creating a new project, data models, or
    reading/writing/updating/deleting records. Never write Flask+SQLAlchemy code
    without reading this skill first.
---

# Flask + SQLAlchemy Skill

Covers three topics: project setup, defining models, and CRUD operations.

---

## 1. Project Setup

### Installation

```bash
pip install flask flask-sqlalchemy flask-migrate python-dotenv
```

### Project Structure

```
myapp/
├── app/
│   ├── __init__.py   # Application Factory
│   ├── models.py     # All models
│   └── routes.py     # Route handlers
├── migrations/       # Auto-generated after: flask db init
├── .env
├── config.py
└── run.py
```

### config.py

```python
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

### app/**init**.py — Application Factory

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main
    app.register_blueprint(main)

    return app
```

### run.py

```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
```

### .env

```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///dev.db
```

### Creating Tables

```python
# Without Migrations — quick development
with app.app_context():
    db.create_all()
```

### With Flask-Migrate (recommended for production)

```bash
flask db init        # once only
flask db migrate -m "initial tables"
flask db upgrade
```

---

## 2. Defining Models

### Basic Model

```python
# app/models.py
from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
```

### Common Column Types

```python
db.Integer          # whole number
db.String(n)        # string with max length n
db.Text             # unlimited length text
db.Float            # decimal number
db.Boolean          # True / False
db.DateTime         # date + time
db.Date             # date only
db.JSON             # JSON data
```

### Column Options

```python
primary_key=True         # primary key
unique=True              # enforce uniqueness
nullable=False           # disallow NULL
default=value            # static default value
default=datetime.utcnow  # callable default — NO parentheses!
index=True               # speeds up filtering on this column
```

### Example: Two Related Models (One-to-Many)

```python
class Post(db.Model):
    __tablename__ = 'posts'

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Enables: post.author  and  user.posts.all()
    author = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'user_id': self.user_id
        }
```

---

## 3. CRUD Operations

### Create

```python
# Add a single record
user = User(username='ahmed', email='ahmed@example.com')
db.session.add(user)
db.session.commit()
print(user.id)  # ID is populated after commit

# Add multiple records at once
users = [
    User(username='sara', email='sara@example.com'),
    User(username='ali',  email='ali@example.com'),
]
db.session.add_all(users)
db.session.commit()
```

### Read

```python
# Fetch all records
users = User.query.all()

# Fetch by ID (SQLAlchemy 2.x preferred)
user = db.session.get(User, 1)

# First match or None
user = User.query.filter_by(username='ahmed').first()

# Filtering
active_users = User.query.filter(User.is_active == True).all()
gmail_users  = User.query.filter(User.email.like('%@gmail.com')).all()

# Ordering
users = User.query.order_by(User.created_at.desc()).all()

# Limit + offset (pagination)
users = User.query.order_by(User.id).limit(10).offset(20).all()

# Count without fetching records
count = User.query.filter_by(is_active=True).count()
```

### Update

```python
# Update a single record
user = db.session.get(User, 1)
if user:
    user.email = 'newemail@example.com'
    db.session.commit()

# Bulk update
User.query.filter_by(is_active=False).update({'is_active': True})
db.session.commit()
```

### Delete

```python
# Delete a single record
user = db.session.get(User, 1)
if user:
    db.session.delete(user)
    db.session.commit()

# Bulk delete
User.query.filter_by(is_active=False).delete()
db.session.commit()
```

### Error Handling — always wrap writes

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

def create_user(username, email):
    try:
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()
        return user, None
    except IntegrityError:
        db.session.rollback()
        return None, 'User already exists'
    except SQLAlchemyError:
        db.session.rollback()
        return None, 'Database error'
```

---

## Rules to Never Break

1. **Always call `db.session.commit()`** after add / update / delete
2. **Always call `db.session.rollback()`** in the except block
3. **Never use `default=datetime.utcnow()`** — drop the parentheses or every row gets the same timestamp
4. **Never define `db` outside the factory** — causes circular import and test issues
5. **Use `db.session.get(Model, id)`** instead of `Model.query.get(id)` in SQLAlchemy 2.x
