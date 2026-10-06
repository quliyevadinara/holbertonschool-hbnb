from flask_jwt_extended import (create_access_token, get_jwt_identity,
                                jwt_required)
from flask_restx import Namespace, Resource, fields

from app.services import facade

api = Namespace('auth', description='Authentication operations')

login_model = api.model('Login', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})


@api.route('/login')
class Login(Resource):
    @api.expect(login_model, validate=True)
    @api.response(200, 'Login successful, returns a JWT access token')
    @api.response(401, 'Invalid credentials')
    def post(self):
        """Authenticate a user and return a JWT token"""
        credentials = api.payload
        user = facade.get_user_by_email(credentials['email'].strip())

        if not user or not user.verify_password(credentials['password']):
            return {'error': 'Invalid credentials'}, 401

        # The identity is the user ID; is_admin is embedded as a claim
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'is_admin': user.is_admin}
        )
        return {'access_token': access_token}, 200


@api.route('/protected')
class ProtectedResource(Resource):
    @jwt_required()
    @api.response(200, 'Token is valid')
    @api.response(401, 'Missing or invalid token')
    def get(self):
        """A protected endpoint that requires a valid JWT token"""
        current_user = get_jwt_identity()
        return {'message': f'Hello, user {current_user}'}, 200
