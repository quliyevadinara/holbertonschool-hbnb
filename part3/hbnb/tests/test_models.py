import unittest

from app import create_app, db
from app.models.amenity import Amenity
from app.models.place import Place
from app.models.review import Review
from app.models.user import User


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()


class TestUser(ModelTestCase):
    def test_creation(self):
        user = User(first_name="John", last_name="Doe",
                    email="john.doe@example.com", password="secret")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.email, "john.doe@example.com")
        self.assertFalse(user.is_admin)
        self.assertIsInstance(user.id, str)
        self.assertIsNotNone(user.created_at)

    def test_invalid_fields(self):
        with self.assertRaises(ValueError):
            User("", "Doe", "john@example.com", "secret")
        with self.assertRaises(ValueError):
            User("John", "x" * 51, "john@example.com", "secret")
        with self.assertRaises(ValueError):
            User("John", "Doe", "not-an-email", "secret")
        with self.assertRaises(ValueError):
            User("John", "Doe", "john@example.com", "")

    def test_password_is_hashed_with_bcrypt(self):
        user = User("John", "Doe", "john@example.com", "secret")
        self.assertNotEqual(user.password, "secret")
        self.assertTrue(user.password.startswith("$2b$"))
        self.assertTrue(user.verify_password("secret"))
        self.assertFalse(user.verify_password("wrong"))
        self.assertNotIn("password", user.to_dict())

    def test_update_password_rehashes(self):
        user = User("John", "Doe", "john@example.com", "secret")
        user.update({"password": "new-secret"})
        self.assertTrue(user.verify_password("new-secret"))
        self.assertFalse(user.verify_password("secret"))

    def test_failed_update_changes_nothing(self):
        user = User("John", "Doe", "john@example.com", "secret")
        with self.assertRaises(ValueError):
            user.update({"first_name": "Jane", "email": "invalid"})
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.email, "john@example.com")

    def test_persisted_in_database(self):
        user = User("John", "Doe", "john@example.com", "secret")
        user_id = user.id
        db.session.add(user)
        db.session.commit()
        db.session.expunge_all()
        stored = db.session.get(User, user_id)
        self.assertEqual(stored.email, "john@example.com")
        self.assertTrue(stored.verify_password("secret"))


class TestPlaceAndReview(ModelTestCase):
    def setUp(self):
        super().setUp()
        self.owner = User("Alice", "Smith", "alice@example.com", "secret")
        self.guest = User("Bob", "Brown", "bob@example.com", "secret")

    def make_place(self, **overrides):
        data = dict(title="Cozy Apartment", description="A nice place",
                    price=100, latitude=37.7749, longitude=-122.4194,
                    owner=self.owner)
        data.update(overrides)
        return Place(**data)

    def test_place_validation(self):
        for overrides in ({"title": ""}, {"price": 0}, {"price": -1},
                          {"latitude": 90.1}, {"longitude": -180.1}):
            with self.assertRaises(ValueError):
                self.make_place(**overrides)
        with self.assertRaises(TypeError):
            self.make_place(price="100")
        with self.assertRaises(TypeError):
            self.make_place(owner="not-a-user")

    def test_relationships_are_persisted(self):
        place = self.make_place()
        wifi = Amenity("Wi-Fi")
        place.add_amenity(wifi)
        place.add_amenity(wifi)
        review = Review("Great stay!", 5, place, self.guest)
        place_id = place.id
        db.session.add_all([place, review])
        db.session.commit()
        db.session.expunge_all()

        stored = db.session.get(Place, place_id)
        self.assertEqual(stored.owner.email, "alice@example.com")
        self.assertEqual([a.name for a in stored.amenities], ["Wi-Fi"])
        self.assertEqual([r.text for r in stored.reviews], ["Great stay!"])

    def test_entity_repositories(self):
        from app.services import facade

        place = self.make_place()
        review = Review("Great stay!", 5, place, self.guest)
        db.session.add_all([place, review, Amenity("Wi-Fi")])
        db.session.commit()

        self.assertIs(facade.user_repo.get_user_by_email("bob@example.com"),
                      self.guest)
        self.assertEqual(facade.place_repo.get_by_owner(self.owner.id),
                         [place])
        self.assertEqual(facade.review_repo.get_by_place(place.id), [review])
        self.assertIs(facade.review_repo.get_by_user_and_place(
            self.guest.id, place.id), review)
        self.assertEqual(facade.amenity_repo.get_by_name("Wi-Fi").name,
                         "Wi-Fi")
        self.assertEqual(self.owner.places, [place])

    def test_review_validation(self):
        place = self.make_place()
        for rating in (0, 6):
            with self.assertRaises(ValueError):
                Review("Nice", rating, place, self.guest)
        for rating in (4.5, "5", True):
            with self.assertRaises(TypeError):
                Review("Nice", rating, place, self.guest)
        with self.assertRaises(ValueError):
            Review("   ", 3, place, self.guest)


if __name__ == '__main__':
    unittest.main()
