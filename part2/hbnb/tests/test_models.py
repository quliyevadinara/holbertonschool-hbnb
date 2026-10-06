import unittest

from app.models.amenity import Amenity
from app.models.place import Place
from app.models.review import Review
from app.models.user import User


class TestUser(unittest.TestCase):
    def test_creation(self):
        user = User(first_name="John", last_name="Doe",
                    email="john.doe@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.email, "john.doe@example.com")
        self.assertFalse(user.is_admin)
        self.assertIsInstance(user.id, str)
        self.assertIsNotNone(user.created_at)

    def test_ids_are_unique(self):
        a = User("A", "B", "a@example.com")
        b = User("A", "B", "b@example.com")
        self.assertNotEqual(a.id, b.id)

    def test_invalid_names(self):
        with self.assertRaises(ValueError):
            User("", "Doe", "john@example.com")
        with self.assertRaises(ValueError):
            User("John", "x" * 51, "john@example.com")

    def test_invalid_email(self):
        for email in ("", "not-an-email", "a@b", "a b@example.com"):
            with self.assertRaises(ValueError):
                User("John", "Doe", email)

    def test_password_is_hashed(self):
        user = User("John", "Doe", "john@example.com", password="secret")
        self.assertNotIn("secret", str(vars(user)))
        self.assertTrue(user.verify_password("secret"))
        self.assertFalse(user.verify_password("wrong"))
        self.assertNotIn("password", user.to_dict())

    def test_update_refreshes_updated_at(self):
        user = User("John", "Doe", "john@example.com")
        before = user.updated_at
        user.update({"first_name": "Jane"})
        self.assertEqual(user.first_name, "Jane")
        self.assertGreaterEqual(user.updated_at, before)

    def test_failed_update_changes_nothing(self):
        user = User("John", "Doe", "john@example.com")
        with self.assertRaises(ValueError):
            user.update({"first_name": "Jane", "email": "invalid"})
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.email, "john@example.com")

    def test_update_ignores_protected_fields(self):
        user = User("John", "Doe", "john@example.com")
        original_id = user.id
        user.update({"id": "hacked"})
        self.assertEqual(user.id, original_id)


class TestAmenity(unittest.TestCase):
    def test_creation(self):
        amenity = Amenity(name="Wi-Fi")
        self.assertEqual(amenity.name, "Wi-Fi")
        self.assertEqual(amenity.description, "")

    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            Amenity(name="")
        with self.assertRaises(ValueError):
            Amenity(name="x" * 51)


class TestPlace(unittest.TestCase):
    def setUp(self):
        self.owner = User("Alice", "Smith", "alice@example.com")

    def make_place(self, **overrides):
        data = dict(title="Cozy Apartment", description="A nice place",
                    price=100, latitude=37.7749, longitude=-122.4194,
                    owner=self.owner)
        data.update(overrides)
        return Place(**data)

    def test_creation_with_relationships(self):
        place = self.make_place()
        review = Review(text="Great stay!", rating=5, place=place,
                        user=self.owner)
        place.add_review(review)
        wifi = Amenity("Wi-Fi")
        place.add_amenity(wifi)
        place.add_amenity(wifi)
        self.assertEqual(place.title, "Cozy Apartment")
        self.assertEqual(place.price, 100.0)
        self.assertIs(place.owner, self.owner)
        self.assertEqual(place.reviews, [review])
        self.assertEqual(place.amenities, [wifi])

    def test_invalid_title(self):
        with self.assertRaises(ValueError):
            self.make_place(title="")
        with self.assertRaises(ValueError):
            self.make_place(title="x" * 101)

    def test_invalid_price(self):
        with self.assertRaises(ValueError):
            self.make_place(price=0)
        with self.assertRaises(ValueError):
            self.make_place(price=-10)
        with self.assertRaises(TypeError):
            self.make_place(price="100")

    def test_coordinates_boundaries(self):
        self.make_place(latitude=-90, longitude=180)
        self.make_place(latitude=90, longitude=-180)
        with self.assertRaises(ValueError):
            self.make_place(latitude=90.1)
        with self.assertRaises(ValueError):
            self.make_place(longitude=-180.1)

    def test_owner_must_be_user(self):
        with self.assertRaises(TypeError):
            self.make_place(owner="not-a-user")


class TestReview(unittest.TestCase):
    def setUp(self):
        self.user = User("Bob", "Brown", "bob@example.com")
        self.place = Place("Loft", 50, 10, 10, self.user)

    def test_creation(self):
        review = Review("Nice", 4, self.place, self.user)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.to_dict()["place_id"], self.place.id)

    def test_invalid_rating(self):
        for rating in (0, 6, -1):
            with self.assertRaises(ValueError):
                Review("Nice", rating, self.place, self.user)
        for rating in (4.5, "5", True):
            with self.assertRaises(TypeError):
                Review("Nice", rating, self.place, self.user)

    def test_invalid_text(self):
        with self.assertRaises(ValueError):
            Review("   ", 3, self.place, self.user)


if __name__ == '__main__':
    unittest.main()
