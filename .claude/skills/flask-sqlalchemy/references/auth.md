# Complete Authentication System with Flask

## Basic Setup

```bash
pip install flask-login flask-jwt-extended werkzeug
```

## Session-Based System (For Traditional Apps)

### Model

```python
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')  # 'user', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return {'error': 'Login required'}, 401
```

### Routes

```python
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate data
    if not data.get('email') or not data.get('password'):
        return {'error': 'Email and password are required'}, 400

    if User.query.filter_by(email=data['email']).first():
        return {'error': 'Email already in use'}, 409

    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return {'message': 'Account created successfully', 'user': user.to_dict()}, 201

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()

    if not user or not user.check_password(data.get('password', '')):
        return {'error': 'Invalid credentials'}, 401

    if not user.is_active:
        return {'error': 'Account is disabled'}, 403

    login_user(user, remember=data.get('remember', False))
    return {'message': 'Login successful', 'user': user.to_dict()}

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return {'message': 'Logout successful'}

@auth.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify(current_user.to_dict())
```

---

## JWT System (For APIs and Separate Apps)

### Setup

```python
# in config.py
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

# in __init__.py
from flask_jwt_extended import JWTManager
jwt = JWTManager()
jwt.init_app(app)
```

### Routes

```python
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

@auth.route('/login', methods=['POST'])
def login_jwt():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return {'error': 'Invalid credentials'}, 401

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }

@auth.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return {'access_token': access_token}

@auth.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    return jsonify(user.to_dict())
```

---

## User Permissions (RBAC)

```python
from functools import wraps
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return {'error': 'Insufficient permissions'}, 403
        return f(*args, **kwargs)
    return decorated_function

# Usage
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    return jsonify(User.query.all())
```
