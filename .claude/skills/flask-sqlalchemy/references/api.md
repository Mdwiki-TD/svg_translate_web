# Professional REST API with Flask

## Complete API Structure

```python
from flask import Blueprint, jsonify, request
from app import db
from app.models import User
from sqlalchemy import or_

api = Blueprint('api', __name__)

# ===== Pagination Helper =====
def paginate_query(query, page, per_page=20):
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [item.to_dict() for item in pagination.items],
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }
```

## Complete CRUD with Pagination and Search

```python
@api.route('/users', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')

    query = User.query

    # Search
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    # Sort
    sort_column = getattr(User, sort_by, User.created_at)
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    return jsonify(paginate_query(query, page, per_page))


@api.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(User, id)
    if not user:
        return {'error': 'User not found'}, 404
    return jsonify(user.to_dict())


@api.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    errors = validate_user_data(data)
    if errors:
        return {'errors': errors}, 422

    try:
        user = User(username=data['username'], email=data['email'])
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return {'error': 'Server error'}, 500


@api.route('/users/<int:id>', methods=['PUT', 'PATCH'])
def update_user(id):
    user = db.session.get(User, id)
    if not user:
        return {'error': 'User not found'}, 404

    data = request.get_json()
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']

    db.session.commit()
    return jsonify(user.to_dict())


@api.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)
    if not user:
        return {'error': 'User not found'}, 404

    db.session.delete(user)
    db.session.commit()
    return '', 204
```

## Validation

```python
def validate_user_data(data, partial=False):
    errors = {}

    if not partial or 'username' in data:
        username = data.get('username', '')
        if not username:
            errors['username'] = 'Username is required'
        elif len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters'
        elif User.query.filter_by(username=username).first():
            errors['username'] = 'Username already exists'

    if not partial or 'email' in data:
        email = data.get('email', '')
        if not email:
            errors['email'] = 'Email is required'
        elif '@' not in email:
            errors['email'] = 'Invalid email'

    return errors
```

## Global Error Handling

```python
# in __init__.py or separate file
@app.errorhandler(404)
def not_found(e):
    return {'error': 'Resource not found'}, 404

@app.errorhandler(405)
def method_not_allowed(e):
    return {'error': 'Method not allowed'}, 405

@app.errorhandler(422)
def unprocessable(e):
    return {'error': 'Invalid data'}, 422

@app.errorhandler(500)
def server_error(e):
    return {'error': 'Server error'}, 500
```

## Flask-RESTful (The Organized Way)

```python
from flask_restful import Api, Resource, reqparse, fields, marshal_with

# Define response format
user_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String,
    'created_at': fields.DateTime(dt_format='iso8601')
}

# Parser for input validation
user_parser = reqparse.RequestParser()
user_parser.add_argument('username', type=str, required=True, help='Username is required')
user_parser.add_argument('email', type=str, required=True, help='Email is required')

class UserListResource(Resource):
    @marshal_with(user_fields)
    def get(self):
        return User.query.all()

    @marshal_with(user_fields)
    def post(self):
        args = user_parser.parse_args()
        user = User(username=args['username'], email=args['email'])
        db.session.add(user)
        db.session.commit()
        return user, 201

class UserResource(Resource):
    @marshal_with(user_fields)
    def get(self, id):
        return db.session.get(User, id) or ({'error': 'Not found'}, 404)

    def delete(self, id):
        user = db.session.get(User, id)
        if not user:
            return {'error': 'Not found'}, 404
        db.session.delete(user)
        db.session.commit()
        return '', 204

# Registration
api_ext = Api(api_blueprint)
api_ext.add_resource(UserListResource, '/users')
api_ext.add_resource(UserResource, '/users/<int:id>')
```

## Common HTTP Status Codes

| Code | Meaning       | When to Use                |
| ---- | ------------- | -------------------------- |
| 200  | OK            | Successful request         |
| 201  | Created       | New record created         |
| 204  | No Content    | Successful deletion        |
| 400  | Bad Request   | Missing or invalid data    |
| 401  | Unauthorized  | Login required             |
| 403  | Forbidden     | Insufficient permissions   |
| 404  | Not Found     | Record does not exist      |
| 409  | Conflict      | Conflict (e.g., duplicate) |
| 422  | Unprocessable | Data validation failed     |
| 500  | Server Error  | Unexpected error           |
