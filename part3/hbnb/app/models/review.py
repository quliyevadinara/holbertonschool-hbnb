from sqlalchemy.orm import validates

from app import db
from app.models.base_model import BaseModel
from app.models.place import Place
from app.models.user import User


class Review(BaseModel):
    __tablename__ = 'reviews'
    # A user can review a given place only once
    __table_args__ = (db.UniqueConstraint('user_id', 'place_id'),)

    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    place_id = db.Column(db.String(36), db.ForeignKey('places.id'),
                         nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'),
                        nullable=False)

    place = db.relationship('Place', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')

    def __init__(self, text, rating, place, user):
        super().__init__()
        # Scalar fields first: if one is invalid, nothing is linked
        self.text = text
        self.rating = rating
        self.user = user
        self.place = place

    @validates('text')
    def validate_text(self, key, value):
        return self._validate_string(value, key)

    @validates('rating')
    def validate_rating(self, key, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("rating must be an integer")
        if not 1 <= value <= 5:
            raise ValueError("rating must be between 1 and 5")
        return value

    @validates('place')
    def validate_place(self, key, value):
        if not isinstance(value, Place):
            raise TypeError("place must be a Place")
        return value

    @validates('user')
    def validate_user(self, key, value):
        if not isinstance(value, User):
            raise TypeError("user must be a User")
        return value

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'rating': self.rating,
            'user_id': self.user.id,
            'place_id': self.place.id
        }
