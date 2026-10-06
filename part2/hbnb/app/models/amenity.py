from app.models.base_model import BaseModel


class Amenity(BaseModel):
    def __init__(self, name, description=""):
        super().__init__()
        self.name = name
        self.description = description

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = self._validate_string(value, "name", 50)

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

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
