import unittest

from app import create_app, db
from app.services import facade


class APITestCase(unittest.TestCase):
    def setUp(self):
        # A fresh in-memory database for every test
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()
        with self.app.app_context():
            admin = facade.create_user({
                "first_name": "Admin", "last_name": "HBnB",
                "email": "admin@hbnb.io", "password": "admin1234",
                "is_admin": True})
            self.admin_id = admin.id
        self.admin = self.auth("admin@hbnb.io", "admin1234")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, email, password):
        return self.client.post('/api/v1/auth/login',
                                json={"email": email, "password": password})

    def auth(self, email, password):
        response = self.login(email, password)
        self.assertEqual(response.status_code, 200)
        return {"Authorization":
                f"Bearer {response.get_json()['access_token']}"}

    def create_user(self, email="jane.doe@example.com"):
        """Create a regular user (as admin) and return (user, headers)."""
        response = self.client.post('/api/v1/users/', headers=self.admin,
                                    json={"first_name": "Jane",
                                          "last_name": "Doe",
                                          "email": email,
                                          "password": "secret"})
        self.assertEqual(response.status_code, 201)
        return response.get_json(), self.auth(email, "secret")

    def create_amenity(self, name="Wi-Fi"):
        response = self.client.post('/api/v1/amenities/', headers=self.admin,
                                    json={"name": name})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def create_place(self, headers, amenities=None):
        response = self.client.post('/api/v1/places/', headers=headers, json={
            "title": "Cozy Apartment", "description": "A nice place",
            "price": 100.0, "latitude": 37.7749, "longitude": -122.4194,
            "amenities": amenities or []})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def create_review(self, headers, place_id, rating=5):
        return self.client.post('/api/v1/reviews/', headers=headers, json={
            "text": "Great place to stay!", "rating": rating,
            "place_id": place_id})


class TestConfiguration(APITestCase):
    def test_factory_uses_given_config(self):
        self.assertTrue(self.app.config["TESTING"])
        self.assertEqual(self.app.config["SQLALCHEMY_DATABASE_URI"],
                         "sqlite:///:memory:")
        dev = create_app("config.DevelopmentConfig")
        self.assertTrue(dev.config["DEBUG"])


class TestAuthentication(APITestCase):
    def test_login_returns_token(self):
        response = self.login("admin@hbnb.io", "admin1234")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.get_json())

    def test_login_invalid_credentials(self):
        for email, password in (("admin@hbnb.io", "wrong"),
                                ("nobody@hbnb.io", "admin1234")):
            response = self.login(email, password)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.get_json(),
                             {"error": "Invalid credentials"})

    def test_protected_endpoint(self):
        response = self.client.get('/api/v1/auth/protected')
        self.assertEqual(response.status_code, 401)
        response = self.client.get('/api/v1/auth/protected',
                                   headers={"Authorization": "Bearer bad"})
        self.assertEqual(response.status_code, 422)
        response = self.client.get('/api/v1/auth/protected',
                                   headers=self.admin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(),
                         {"message": f"Hello, user {self.admin_id}"})

    def test_password_never_returned(self):
        user, _ = self.create_user()
        self.assertNotIn("password", user)
        for url in ('/api/v1/users/', f'/api/v1/users/{user["id"]}'):
            self.assertNotIn("password",
                             self.client.get(url).get_data(as_text=True))


class TestUserAccess(APITestCase):
    def test_only_admin_creates_users(self):
        _, headers = self.create_user()
        payload = {"first_name": "X", "last_name": "Y",
                   "email": "x@example.com", "password": "secret"}
        response = self.client.post('/api/v1/users/', json=payload)
        self.assertEqual(response.status_code, 401)
        response = self.client.post('/api/v1/users/', json=payload,
                                    headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(),
                         {"error": "Admin privileges required"})

    def test_admin_create_user_validation(self):
        self.create_user()
        response = self.client.post('/api/v1/users/', headers=self.admin,
                                    json={"first_name": "J",
                                          "last_name": "D",
                                          "email": "jane.doe@example.com",
                                          "password": "x"})
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/v1/users/', headers=self.admin,
                                    json={"first_name": "J",
                                          "last_name": "D",
                                          "email": "j@example.com"})
        self.assertEqual(response.status_code, 400)

    def test_user_updates_own_profile(self):
        user, headers = self.create_user()
        response = self.client.put(f'/api/v1/users/{user["id"]}',
                                   headers=headers,
                                   json={"first_name": "Janet"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["first_name"], "Janet")

    def test_user_cannot_modify_email_or_password(self):
        user, headers = self.create_user()
        for payload in ({"email": "new@example.com"},
                        {"password": "new-secret"}):
            response = self.client.put(f'/api/v1/users/{user["id"]}',
                                       headers=headers, json=payload)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json(),
                             {"error": "You cannot modify email or password."})

    def test_user_cannot_modify_other_user(self):
        _, headers = self.create_user()
        other, _ = self.create_user("other@example.com")
        response = self.client.put(f'/api/v1/users/{other["id"]}',
                                   headers=headers,
                                   json={"first_name": "Hacked"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {"error": "Unauthorized action"})

    def test_admin_modifies_any_user(self):
        user, _ = self.create_user()
        self.create_user("taken@example.com")
        response = self.client.put(f'/api/v1/users/{user["id"]}',
                                   headers=self.admin,
                                   json={"email": "taken@example.com"})
        self.assertEqual(response.status_code, 400)
        response = self.client.put(f'/api/v1/users/{user["id"]}',
                                   headers=self.admin,
                                   json={"email": "new@example.com",
                                         "password": "changed"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["email"], "new@example.com")
        self.assertEqual(self.login("new@example.com", "changed").status_code,
                         200)


class TestAmenityAccess(APITestCase):
    def test_only_admin_manages_amenities(self):
        _, headers = self.create_user()
        response = self.client.post('/api/v1/amenities/', headers=headers,
                                    json={"name": "Pool"})
        self.assertEqual(response.status_code, 403)

        amenity = self.create_amenity()
        response = self.client.put(f'/api/v1/amenities/{amenity["id"]}',
                                   headers=headers, json={"name": "Pool"})
        self.assertEqual(response.status_code, 403)
        response = self.client.put(f'/api/v1/amenities/{amenity["id"]}',
                                   headers=self.admin, json={"name": "Pool"})
        self.assertEqual(response.status_code, 200)

    def test_amenity_name_is_unique(self):
        amenity = self.create_amenity("Wi-Fi")
        response = self.client.post('/api/v1/amenities/', headers=self.admin,
                                    json={"name": "Wi-Fi"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(),
                         {"error": "Amenity already exists"})
        self.create_amenity("Pool")
        response = self.client.put(f'/api/v1/amenities/{amenity["id"]}',
                                   headers=self.admin, json={"name": "Pool"})
        self.assertEqual(response.status_code, 400)
        response = self.client.put(f'/api/v1/amenities/{amenity["id"]}',
                                   headers=self.admin, json={"name": "Wi-Fi"})
        self.assertEqual(response.status_code, 200)

    def test_amenities_are_public(self):
        amenity = self.create_amenity()
        self.assertEqual(self.client.get('/api/v1/amenities/').status_code,
                         200)
        response = self.client.get(f'/api/v1/amenities/{amenity["id"]}')
        self.assertEqual(response.get_json()["name"], "Wi-Fi")


class TestPlaceAccess(APITestCase):
    def test_create_place_requires_token(self):
        response = self.client.post('/api/v1/places/', json={
            "title": "X", "price": 10.0, "latitude": 0.0, "longitude": 0.0})
        self.assertEqual(response.status_code, 401)

    def test_owner_is_logged_in_user(self):
        user, headers = self.create_user()
        amenity = self.create_amenity()
        place = self.create_place(headers, [amenity["id"]])
        self.assertEqual(place["owner_id"], user["id"])

        details = self.client.get(f'/api/v1/places/{place["id"]}').get_json()
        self.assertEqual(details["owner"]["id"], user["id"])
        self.assertEqual(details["amenities"],
                         [{"id": amenity["id"], "name": "Wi-Fi"}])

    def test_cannot_create_place_for_someone_else(self):
        _, headers = self.create_user()
        other, _ = self.create_user("other@example.com")
        response = self.client.post('/api/v1/places/', headers=headers, json={
            "title": "X", "price": 10.0, "latitude": 0.0, "longitude": 0.0,
            "owner_id": other["id"]})
        self.assertEqual(response.status_code, 403)

    def test_place_validation(self):
        _, headers = self.create_user()
        base = {"title": "Place", "price": 100.0, "latitude": 10.0,
                "longitude": 10.0}
        for overrides in ({"price": -10.0}, {"latitude": 91.0},
                          {"longitude": -181.0}, {"title": ""},
                          {"amenities": ["unknown"]}):
            response = self.client.post('/api/v1/places/', headers=headers,
                                        json={**base, **overrides})
            self.assertEqual(response.status_code, 400, overrides)

    def test_only_owner_updates_and_deletes(self):
        _, owner = self.create_user()
        _, other = self.create_user("other@example.com")
        place = self.create_place(owner)
        url = f'/api/v1/places/{place["id"]}'

        response = self.client.put(url, headers=other, json={"title": "Mine"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {"error": "Unauthorized action"})
        self.assertEqual(self.client.delete(url, headers=other).status_code,
                         403)

        response = self.client.put(url, headers=owner,
                                   json={"title": "Luxury Condo"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(url).get_json()["title"],
                         "Luxury Condo")
        self.assertEqual(self.client.delete(url, headers=owner).status_code,
                         200)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_admin_bypasses_ownership(self):
        _, owner = self.create_user()
        place = self.create_place(owner)
        url = f'/api/v1/places/{place["id"]}'
        response = self.client.put(url, headers=self.admin,
                                   json={"price": 250.0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(url).get_json()["price"], 250.0)
        self.assertEqual(
            self.client.delete(url, headers=self.admin).status_code, 200)

    def test_places_are_public(self):
        _, headers = self.create_user()
        place = self.create_place(headers)
        self.assertEqual(len(self.client.get('/api/v1/places/').get_json()),
                         1)
        self.assertEqual(
            self.client.get(f'/api/v1/places/{place["id"]}').status_code, 200)


class TestReviewAccess(APITestCase):
    def setUp(self):
        super().setUp()
        _, self.owner = self.create_user("owner@example.com")
        self.guest_user, self.guest = self.create_user("guest@example.com")
        self.place = self.create_place(self.owner)

    def test_create_review(self):
        response = self.create_review(self.guest, self.place["id"])
        self.assertEqual(response.status_code, 201)
        review = response.get_json()
        self.assertEqual(review["user_id"], self.guest_user["id"])
        reviews = self.client.get(
            f'/api/v1/places/{self.place["id"]}/reviews').get_json()
        self.assertEqual(len(reviews), 1)

    def test_cannot_review_own_place(self):
        response = self.create_review(self.owner, self.place["id"])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(),
                         {"error": "You cannot review your own place."})

    def test_cannot_review_twice(self):
        self.create_review(self.guest, self.place["id"])
        response = self.create_review(self.guest, self.place["id"], 3)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(),
                         {"error": "You have already reviewed this place."})

    def test_review_validation(self):
        for rating in (0, 6):
            response = self.create_review(self.guest, self.place["id"],
                                          rating)
            self.assertEqual(response.status_code, 400)
        response = self.create_review(self.guest, "unknown")
        self.assertEqual(response.status_code, 400)

    def test_only_author_updates_and_deletes(self):
        review = self.create_review(self.guest, self.place["id"]).get_json()
        url = f'/api/v1/reviews/{review["id"]}'

        response = self.client.put(url, headers=self.owner,
                                   json={"text": "Edited"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.delete(url, headers=self.owner)
                         .status_code, 403)

        response = self.client.put(url, headers=self.guest,
                                   json={"text": "Amazing stay!",
                                         "rating": 4})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(url).get_json()["rating"], 4)
        self.assertEqual(self.client.delete(url, headers=self.guest)
                         .status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_admin_bypasses_review_ownership(self):
        review = self.create_review(self.guest, self.place["id"]).get_json()
        url = f'/api/v1/reviews/{review["id"]}'
        response = self.client.put(url, headers=self.admin,
                                   json={"rating": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.delete(url, headers=self.admin)
                         .status_code, 200)

    def test_deleting_place_deletes_its_reviews(self):
        review = self.create_review(self.guest, self.place["id"]).get_json()
        self.client.delete(f'/api/v1/places/{self.place["id"]}',
                           headers=self.owner)
        self.assertEqual(
            self.client.get(f'/api/v1/reviews/{review["id"]}').status_code,
            404)


if __name__ == '__main__':
    unittest.main()
