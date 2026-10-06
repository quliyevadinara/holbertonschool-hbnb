from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.services import facade

api = Namespace('users', description='User operations')

user_model = api.model('User', {
    'first_name': fields.String(required=True,
                                description='First name of the user'),
    'last_name': fields.String(required=True,
                               description='Last name of the user'),
    'email': fields.String(required=True, description='Email of the user'),
    'password': fields.String(required=True,
                              description='Password of the user'),
    'is_admin': fields.Boolean(description='Administrator account')
})

user_update_model = api.model('UserUpdate', {
    'first_name': fields.String(description='First name of the user'),
    'last_name': fields.String(description='Last name of the user'),
    'email': fields.String(description='Email (admin only)'),
    'password': fields.String(description='Password (admin only)')
})


@api.route('/')
class UserList(Resource):
    @jwt_required()
    @api.expect(user_model, validate=True)
    @api.response(201, 'User successfully created')
    @api.response(400, 'Email already registered')
    @api.response(400, 'Invalid input data')
    @api.response(403, 'Admin privileges required')
    def post(self):
        """Register a new user (admin only)"""
        if not get_jwt().get('is_admin'):
            return {'error': 'Admin privileges required'}, 403

        user_data = api.payload
        if facade.get_user_by_email(user_data['email'].strip()):
            return {'error': 'Email already registered'}, 400

        try:
            new_user = facade.create_user(user_data)
        except (ValueError, TypeError) as e:
            return {'error': str(e)}, 400
        return new_user.to_dict(), 201

    @api.response(200, 'List of users retrieved successfully')
    def get(self):
        """Retrieve the list of all users"""
        return [user.to_dict() for user in facade.get_all_users()], 200


@api.route('/<user_id>')
class UserResource(Resource):
    @api.response(200, 'User details retrieved successfully')
    @api.response(404, 'User not found')
    def get(self, user_id):
        """Get user details by ID"""
        user = facade.get_user(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        return user.to_dict(), 200

    @jwt_required()
    @api.expect(user_update_model, validate=True)
    @api.response(200, 'User updated successfully')
    @api.response(400, 'Invalid input data')
    @api.response(403, 'Unauthorized action')
    @api.response(404, 'User not found')
    def put(self, user_id):
        """Update a user (own profile, or any user for admins)"""
        user_data = api.payload
        is_admin = get_jwt().get('is_admin', False)

        if not is_admin:
            if user_id != get_jwt_identity():
                return {'error': 'Unauthorized action'}, 403
            if 'email' in user_data or 'password' in user_data:
                return {'error': 'You cannot modify email or password.'}, 400

        if not facade.get_user(user_id):
            return {'error': 'User not found'}, 404

        email = user_data.get('email')
        if isinstance(email, str):
            existing = facade.get_user_by_email(email.strip())
            if existing and existing.id != user_id:
                return {'error': 'Email already registered'}, 400

        try:
            user = facade.update_user(user_id, user_data)
        except (ValueError, TypeError) as e:
            return {'error': str(e)}, 400
        return user.to_dict(), 200
