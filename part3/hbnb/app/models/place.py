from sqlalchemy.orm import validates

from app import db
from app.models.amenity import Amenity
from app.models.base_model import BaseModel
from app.models.user import User

# Many-to-many link between places and amenities
place_amenity = db.Table(
    'place_amenity',
    db.Column('place_id', db.String(36), db.ForeignKey('places.id'),
              primary_key=True),
    db.Column('amenity_id', db.String(36), db.ForeignKey('amenities.id'),
              primary_key=True)
)


def _to_number(value, field):
    # bool is a subclass of int, but True/False is never a valid number here
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number")
    return float(value)


class Place(BaseModel):
    __tablename__ = 'places'

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    price = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'),
                         nullable=False)

    owner = db.relationship('User', back_populates='places')
    reviews = db.relationship('Review', back_populates='place',
                              cascade='all, delete-orphan')
    amenities = db.relationship('Amenity', secondary=place_amenity)

    def __init__(self, title, price, latitude, longitude, owner,
                 description=""):
        super().__init__()
        # Scalar fields first: if one is invalid, the owner is never linked
        self.title = title
        self.description = description
        self.price = price
        self.latitude = latitude
        self.longitude = longitude
        self.owner = owner

    @validates('title')
    def validate_title(self, key, value):
        return self._validate_string(value, key, 100)

    @validates('description')
    def validate_description(self, key, value):
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise TypeError("description must be a string")
        return value.strip()

    @validates('price')
    def validate_price(self, key, value):
        value = _to_number(value, key)
        if value <= 0:
            raise ValueError("price must be a positive number")
        return value

    @validates('latitude')
    def validate_latitude(self, key, value):
        value = _to_number(value, key)
        if not -90.0 <= value <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @validates('longitude')
    def validate_longitude(self, key, value):
        value = _to_number(value, key)
        if not -180.0 <= value <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return value

    @validates('owner')
    def validate_owner(self, key, value):
        if not isinstance(value, User):
            raise TypeError("owner must be a User")
        return value

    @validates('amenities')
    def validate_amenity(self, key, value):
        if not isinstance(value, Amenity):
            raise TypeError("amenities must be a list of Amenity")
        return value

    def add_review(self, review):
        """Add a review to the place."""
        if review not in self.reviews:
            self.reviews.append(review)

    def add_amenity(self, amenity):
        """Add an amenity to the place, ignoring duplicates."""
        if amenity not in self.amenities:
            self.amenities.append(amenity)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'owner_id': self.owner.id
        }
