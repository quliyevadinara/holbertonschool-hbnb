from app import db
from app.models.place import Place
from app.persistence.repository import SQLAlchemyRepository


class PlaceRepository(SQLAlchemyRepository):
    def __init__(self):
        super().__init__(Place)

    def get_by_owner(self, owner_id):
        return db.session.scalars(
            db.select(Place).filter_by(owner_id=owner_id)).all()
