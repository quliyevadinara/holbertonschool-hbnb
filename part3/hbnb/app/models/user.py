import re

from sqlalchemy.orm import validates

from app import bcrypt, db
from app.models.base_model import BaseModel

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class User(BaseModel):
    __tablename__ = 'users'

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    places = db.relationship('Place', back_populates='owner')
    reviews = db.relationship('Review', back_populates='user')

    def __init__(self, first_name, last_name, email, password,
                 is_admin=False):
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.is_admin = is_admin
        self.hash_password(password)

    @validates('first_name', 'last_name')
    def validate_name(self, key, value):
        return self._validate_string(value, key, 50)

    @validates('email')
    def validate_email(self, key, value):
        if not isinstance(value, str) or not EMAIL_REGEX.match(value.strip()):
            raise ValueError("email must be a valid email address")
        return value.strip()

    @validates('is_admin')
    def validate_is_admin(self, key, value):
        if not isinstance(value, bool):
            raise TypeError("is_admin must be a boolean")
        return value

    def hash_password(self, password):
        """Hash the password with bcrypt before storing it."""
        self._validate_string(password, "password")
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        """Check a plain-text password against the stored hash."""
        return bcrypt.check_password_hash(self.password, password)

    def update(self, data):
        data = dict(data)
        password = data.pop('password', None)
        if password is not None:
            self._validate_string(password, "password")
        super().update(data)
        if password is not None:
            self.hash_password(password)

    def to_dict(self):
        """Public representation: the password is never included."""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email
        }
