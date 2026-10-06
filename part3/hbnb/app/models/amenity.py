from sqlalchemy.orm import validates

from app import db
from app.models.base_model import BaseModel


class Amenity(BaseModel):
    __tablename__ = 'amenities'

    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")

    def __init__(self, name, description=""):
        super().__init__()
        self.name = name
        self.description = description

    @validates('name')
    def validate_name(self, key, value):
        return self._validate_string(value, key, 50)

    @validates('description')
    def validate_description(self, key, value):
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise TypeError("description must be a string")
        return value.strip()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
