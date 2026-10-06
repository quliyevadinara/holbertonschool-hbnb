import uuid
from datetime import datetime


class BaseModel:
    """Common identity and audit fields shared by every entity."""

    PROTECTED_FIELDS = ('id', 'created_at', 'updated_at')

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def save(self):
        """Refresh the updated_at timestamp whenever the object is modified."""
        self.updated_at = datetime.now()

    def update(self, data):
        """Update attributes from a dict, all or nothing.

        Unknown keys and protected fields (id, timestamps) are ignored.
        If one value fails validation, the earlier changes are rolled back.
        """
        previous = {}
        try:
            for key, value in data.items():
                if key in self.PROTECTED_FIELDS or not hasattr(self, key):
                    continue
                previous[key] = getattr(self, key)
                setattr(self, key, value)
        except (ValueError, TypeError):
            for key, value in previous.items():
                setattr(self, key, value)
            raise
        self.save()

    @staticmethod
    def _validate_string(value, field, max_length=None):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")
        value = value.strip()
        if max_length is not None and len(value) > max_length:
            raise ValueError(
                f"{field} must not exceed {max_length} characters")
        return value
