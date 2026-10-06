from app import db
from app.models.review import Review
from app.persistence.repository import SQLAlchemyRepository


class ReviewRepository(SQLAlchemyRepository):
    def __init__(self):
        super().__init__(Review)

    def get_by_place(self, place_id):
        return db.session.scalars(
            db.select(Review).filter_by(place_id=place_id)).all()

    def get_by_user_and_place(self, user_id, place_id):
        return db.session.scalars(
            db.select(Review).filter_by(user_id=user_id,
                                        place_id=place_id)).first()
