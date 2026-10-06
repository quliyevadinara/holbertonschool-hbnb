from app import db
from app.models.amenity import Amenity
from app.persistence.repository import SQLAlchemyRepository


class AmenityRepository(SQLAlchemyRepository):
    def __init__(self):
        super().__init__(Amenity)

    def get_by_name(self, name):
        return db.session.scalars(
            db.select(Amenity).filter_by(name=name)).first()
