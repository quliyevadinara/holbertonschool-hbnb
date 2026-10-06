import re

from werkzeug.security import check_password_hash, generate_password_hash

from app.models.base_model import BaseModel

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class User(BaseModel):
    def __init__(self, first_name, last_name, email, password=None,
                 is_admin=False):
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.is_admin = is_admin
        self._password = None
        if password is not None:
            self.hash_password(password)

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        self._first_name = self._validate_string(value, "first_name", 50)

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        self._last_name = self._validate_string(value, "last_name", 50)

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if not isinstance(value, str) or not EMAIL_REGEX.match(value.strip()):
            raise ValueError("email must be a valid email address")
        self._email = value.strip()

    @property
    def is_admin(self):
        return self._is_admin

    @is_admin.setter
    def is_admin(self, value):
        if not isinstance(value, bool):
            raise TypeError("is_admin must be a boolean")
        self._is_admin = value

    def hash_password(self, password):
        """Store only a hash of the password, never the plain text."""
        self._validate_string(password, "password")
        self._password = generate_password_hash(password)

    def verify_password(self, password):
        if self._password is None:
            return False
        return check_password_hash(self._password, password)

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
