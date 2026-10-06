from app.models.amenity import Amenity
from app.models.place import Place
from app.models.review import Review
from app.models.user import User
from app.persistence.repository import SQLAlchemyRepository


class HBnBFacade:
    """Single entry point from the API into the business logic."""

    USER_FIELDS = ('first_name', 'last_name', 'email', 'password', 'is_admin')
    AMENITY_FIELDS = ('name', 'description')
    PLACE_FIELDS = ('title', 'description', 'price', 'latitude', 'longitude')
    REVIEW_FIELDS = ('text', 'rating')

    def __init__(self):
        self.user_repo = SQLAlchemyRepository(User)
        self.place_repo = SQLAlchemyRepository(Place)
        self.review_repo = SQLAlchemyRepository(Review)
        self.amenity_repo = SQLAlchemyRepository(Amenity)

    @staticmethod
    def _pick(data, allowed):
        return {key: value for key, value in data.items() if key in allowed}

    # ---------------------------------------------------------------- users
    def create_user(self, user_data):
        user = User(**self._pick(user_data, self.USER_FIELDS))
        self.user_repo.add(user)
        return user

    def get_user(self, user_id):
        return self.user_repo.get(user_id)

    def get_user_by_email(self, email):
        return self.user_repo.get_by_attribute('email', email)

    def get_all_users(self):
        return self.user_repo.get_all()

    def update_user(self, user_id, user_data):
        user = self.get_user(user_id)
        if not user:
            return None
        self.user_repo.update(user_id, self._pick(user_data, self.USER_FIELDS))
        return user

    # ------------------------------------------------------------ amenities
    def create_amenity(self, amenity_data):
        amenity = Amenity(**self._pick(amenity_data, self.AMENITY_FIELDS))
        self.amenity_repo.add(amenity)
        return amenity

    def get_amenity(self, amenity_id):
        return self.amenity_repo.get(amenity_id)

    def get_all_amenities(self):
        return self.amenity_repo.get_all()

    def update_amenity(self, amenity_id, amenity_data):
        amenity = self.get_amenity(amenity_id)
        if not amenity:
            return None
        self.amenity_repo.update(
            amenity_id, self._pick(amenity_data, self.AMENITY_FIELDS))
        return amenity

    # --------------------------------------------------------------- places
    def _resolve_owner(self, owner_id):
        owner = self.get_user(owner_id)
        if not owner:
            raise ValueError("Owner not found")
        return owner

    def _resolve_amenities(self, amenity_ids):
        if not isinstance(amenity_ids, list):
            raise TypeError("amenities must be a list of amenity IDs")
        amenities = []
        for amenity_id in amenity_ids:
            amenity = self.get_amenity(amenity_id)
            if not amenity:
                raise ValueError(f"Amenity {amenity_id} not found")
            if amenity not in amenities:
                amenities.append(amenity)
        return amenities

    def create_place(self, place_data):
        owner = self._resolve_owner(place_data.get('owner_id'))
        amenities = self._resolve_amenities(place_data.get('amenities') or [])
        place = Place(owner=owner,
                      **self._pick(place_data, self.PLACE_FIELDS))
        for amenity in amenities:
            place.add_amenity(amenity)
        self.place_repo.add(place)
        return place

    def get_place(self, place_id):
        return self.place_repo.get(place_id)

    def get_all_places(self):
        return self.place_repo.get_all()

    def update_place(self, place_id, place_data):
        place = self.get_place(place_id)
        if not place:
            return None
        data = self._pick(place_data, self.PLACE_FIELDS)
        # Resolve related objects first so a bad ID changes nothing
        if 'owner_id' in place_data:
            data['owner'] = self._resolve_owner(place_data['owner_id'])
        if 'amenities' in place_data:
            data['amenities'] = self._resolve_amenities(
                place_data['amenities'] or [])
        self.place_repo.update(place_id, data)
        return place

    def delete_place(self, place_id):
        if not self.get_place(place_id):
            return False
        # Reviews are removed with the place (cascade)
        self.place_repo.delete(place_id)
        return True

    # -------------------------------------------------------------- reviews
    def create_review(self, review_data):
        user = self.get_user(review_data.get('user_id'))
        if not user:
            raise ValueError("User not found")
        place = self.get_place(review_data.get('place_id'))
        if not place:
            raise ValueError("Place not found")
        if place.owner_id == user.id:
            raise ValueError("You cannot review your own place.")
        if any(review.user_id == user.id for review in place.reviews):
            raise ValueError("You have already reviewed this place.")
        review = Review(place=place, user=user,
                        **self._pick(review_data, self.REVIEW_FIELDS))
        self.review_repo.add(review)
        return review

    def get_review(self, review_id):
        return self.review_repo.get(review_id)

    def get_all_reviews(self):
        return self.review_repo.get_all()

    def get_reviews_by_place(self, place_id):
        place = self.get_place(place_id)
        if not place:
            return None
        return place.reviews

    def update_review(self, review_id, review_data):
        review = self.get_review(review_id)
        if not review:
            return None
        # A review always stays attached to its original user and place
        self.review_repo.update(
            review_id, self._pick(review_data, self.REVIEW_FIELDS))
        return review

    def delete_review(self, review_id):
        if not self.get_review(review_id):
            return False
        self.review_repo.delete(review_id)
        return True
