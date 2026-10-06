from app.models.amenity import Amenity
from app.models.base_model import BaseModel
from app.models.user import User


def _to_number(value, field):
    # bool is a subclass of int, but True/False is never a valid number here
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number")
    return float(value)


class Place(BaseModel):
    def __init__(self, title, price, latitude, longitude, owner,
                 description=""):
        super().__init__()
        self.title = title
        self.description = description
        self.price = price
        self.latitude = latitude
        self.longitude = longitude
        self.owner = owner
        self.reviews = []
        self.amenities = []

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = self._validate_string(value, "title", 100)

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise TypeError("description must be a string")
        self._description = value.strip()

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        value = _to_number(value, "price")
        if value <= 0:
            raise ValueError("price must be a positive number")
        self._price = value

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        value = _to_number(value, "latitude")
        if not -90.0 <= value <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        self._latitude = value

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        value = _to_number(value, "longitude")
        if not -180.0 <= value <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        self._longitude = value

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, value):
        if not isinstance(value, User):
            raise TypeError("owner must be a User")
        self._owner = value

    @property
    def amenities(self):
        return self._amenities

    @amenities.setter
    def amenities(self, value):
        if not isinstance(value, list) or not all(
                isinstance(amenity, Amenity) for amenity in value):
            raise TypeError("amenities must be a list of Amenity")
        self._amenities = value

    def add_review(self, review):
        """Add a review to the place."""
        self.reviews.append(review)

    def remove_review(self, review):
        if review in self.reviews:
            self.reviews.remove(review)

    def add_amenity(self, amenity):
        """Add an amenity to the place, ignoring duplicates."""
        if not isinstance(amenity, Amenity):
            raise TypeError("amenity must be an Amenity")
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
