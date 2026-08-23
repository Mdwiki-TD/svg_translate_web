# Relationships Between Tables in SQLAlchemy

## One-to-One

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile = db.relationship('Profile', backref='user', uselist=False)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))

# Usage
user.profile        # Single Profile object
profile.user        # User object
```

## One-to-Many

```python
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    products = db.relationship('Product', backref='category', lazy='dynamic')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    name = db.Column(db.String(100))
    price = db.Column(db.Float)

# Usage
category.products.all()           # All products
category.products.count()         # Product count
category.products.filter_by(price=...).all()  # Filtering (requires lazy='dynamic')
product.category                  # Category
```

## Many-to-Many

```python
# Method 1: Simple association table
enrollments = db.Table('enrollments',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    courses = db.relationship('Course', secondary=enrollments, backref='students')

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))

# Usage
student.courses.append(course)   # Enroll
student.courses.remove(course)   # Unenroll
db.session.commit()
course.students                  # All students in course
```

```python
# Method 2: Association model (when additional data needed)
class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    grade = db.Column(db.Float)

    student = db.relationship('Student', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')

# Usage
enrollment = Enrollment(student_id=1, course_id=2, grade=95.0)
db.session.add(enrollment)
db.session.commit()

# Get all courses for a student with grades
for e in student.enrollments:
    print(e.course.title, e.grade)
```

## Self-Referential

```python
# Example: User followers
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    followed = db.relationship(
        'User',
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

# Usage
user.follow(other_user)    # Follow
user.unfollow(other_user)  # Unfollow
user.followed.all()        # Who they follow
user.followers.all()       # Who follows them
```

## Lazy Loading Options

| Value        | Description                      | When to Use              |
| ------------ | -------------------------------- | ------------------------ |
| `'select'`   | Loads data on demand (default)   | Most cases               |
| `'dynamic'`  | Returns a filterable query       | When using filter/count  |
| `'joined'`   | Loads with parent table via JOIN | When frequently accessed |
| `'subquery'` | Loads via separate subquery      | Large lists              |

## Cascade — Related Records Effect

```python
# Auto-delete related records
posts = db.relationship('Post', backref='author', cascade='all, delete-orphan')

# Don't delete related records (default)
posts = db.relationship('Post', backref='author')
```
