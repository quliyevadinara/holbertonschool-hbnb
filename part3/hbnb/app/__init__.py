import click
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
jwt = JWTManager()
db = SQLAlchemy()


def create_app(config_class="config.DevelopmentConfig"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    bcrypt.init_app(app)
    jwt.init_app(app)
    db.init_app(app)
    # The Part 4 front-end is served from another origin
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Imported here because the models need the extensions defined above
    from app.api.v1.amenities import api as amenities_ns
    from app.api.v1.auth import api as auth_ns
    from app.api.v1.places import api as places_ns
    from app.api.v1.reviews import api as reviews_ns
    from app.api.v1.users import api as users_ns

    authorizations = {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Type "Bearer <access_token>"'
        }
    }
    api = Api(app, version='1.0', title='HBnB API',
              description='HBnB Application API', doc='/api/v1/',
              authorizations=authorizations, security='Bearer')

    api.add_namespace(users_ns, path='/api/v1/users')
    api.add_namespace(amenities_ns, path='/api/v1/amenities')
    api.add_namespace(places_ns, path='/api/v1/places')
    api.add_namespace(reviews_ns, path='/api/v1/reviews')
    api.add_namespace(auth_ns, path='/api/v1/auth')

    with app.app_context():
        db.create_all()

    register_commands(app)
    return app


def register_commands(app):
    @app.cli.command('create-admin')
    @click.option('--first-name', default='Admin')
    @click.option('--last-name', default='HBnB')
    @click.option('--email', prompt=True)
    @click.option('--password', prompt=True, hide_input=True,
                  confirmation_prompt=True)
    def create_admin(first_name, last_name, email, password):
        """Create an administrator account."""
        from app.services import facade

        if facade.get_user_by_email(email):
            raise click.ClickException('Email already registered')
        user = facade.create_user({
            'first_name': first_name, 'last_name': last_name,
            'email': email, 'password': password, 'is_admin': True})
        click.echo(f'Admin created: {user.id}')
