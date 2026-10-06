import os


class Config:
    # Development default only: set SECRET_KEY in the environment in production
    SECRET_KEY = os.getenv('SECRET_KEY',
                           'hbnb-development-secret-key-change-me')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Let flask-jwt-extended answer auth errors (401/422)
    # instead of Flask-RESTx turning them into 500 errors
    PROPAGATE_EXCEPTIONS = True


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',
                                        'sqlite:///development.db')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    BCRYPT_LOG_ROUNDS = 4


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
