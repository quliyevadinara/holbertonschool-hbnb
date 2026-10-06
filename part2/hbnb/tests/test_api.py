import unittest

from app import create_app
from app.services import facade


class APITestCase(unittest.TestCase):
    def setUp(self):
        # Every test starts with empty in-memory repositories
        facade.__init__()
        self.app = create_app()
        self.client = self.app.test_client()

    def create_user(self, email="jane.doe@example.com"):
        response = self.client.post('/api/v1/users/', json={
            "first_name": "Jane", "last_name": "Doe", "email": email,
            "password": "secret"})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def create_amenity(self, name="Wi-Fi"):
        response = self.client.post('/api/v1/amenities/',
                                    json={"name": name})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def create_place(self, owner_id, amenities=None):
        response = self.client.post('/api/v1/places/', json={
            "title": "Cozy Apartment", "description": "A nice place",
            "price": 100.0, "latitude": 37.7749, "longitude": -122.4194,
            "owner_id": owner_id, "amenities": amenities or []})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def create_review(self, user_id, place_id, rating=5):
        response = self.client.post('/api/v1/reviews/', json={
            "text": "Great place to stay!", "rating": rating,
            "user_id": user_id, "place_id": place_id})
        self.assertEqual(response.status_code, 201)
        return response.get_json()


class TestUserEndpoints(APITestCase):
    def test_create_user(self):
        user = self.create_user()
        self.assertEqual(user["email"], "jane.doe@example.com")
        self.assertIn("id", user)
        self.assertNotIn("password", user)

    def test_create_user_duplicate_email(self):
        self.create_user()
        response = self.client.post('/api/v1/users/', json={
            "first_name": "J", "last_name": "D",
            "email": "jane.doe@example.com"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(),
                         {"error": "Email already registered"})

    def test_create_user_invalid_data(self):
        for payload in (
                {"first_name": "", "last_name": "", "email": "invalid"},
                {"first_name": "Jane", "last_name": "Doe",
                 "email": "invalid-email"},
                {"first_name": "Jane", "last_name": "Doe"}):
            response = self.client.post('/api/v1/users/', json=payload)
            self.assertEqual(response.status_code, 400, payload)

    def test_get_users(self):
        self.create_user("a@example.com")
        self.create_user("b@example.com")
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 2)
        for user in response.get_json():
            self.assertNotIn("password", user)

    def test_get_user(self):
        user = self.create_user()
        response = self.client.get(f'/api/v1/users/{user["id"]}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), user)

    def test_get_user_not_found(self):
        response = self.client.get('/api/v1/users/unknown')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "User not found"})

    def test_update_user(self):
        user = self.create_user()
        response = self.client.put(f'/api/v1/users/{user["id"]}', json={
            "first_name": "Janet", "last_name": "Smith",
            "email": "janet.smith@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["first_name"], "Janet")
        self.assertEqual(response.get_json()["email"],
                         "janet.smith@example.com")

    def test_update_user_errors(self):
        user = self.create_user()
        other = self.create_user("other@example.com")
        response = self.client.put(f'/api/v1/users/{user["id"]}',
                                   json={"email": other["email"]})
        self.assertEqual(response.status_code, 400)
        response = self.client.put(f'/api/v1/users/{user["id"]}',
                                   json={"email": "bad"})
        self.assertEqual(response.status_code, 400)
        response = self.client.put('/api/v1/users/unknown',
                                   json={"first_name": "X"})
        self.assertEqual(response.status_code, 404)


class TestAmenityEndpoints(APITestCase):
    def test_create_and_get_amenity(self):
        amenity = self.create_amenity()
        self.assertEqual(amenity["name"], "Wi-Fi")
        response = self.client.get(f'/api/v1/amenities/{amenity["id"]}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "Wi-Fi")

    def test_create_amenity_invalid(self):
        response = self.client.post('/api/v1/amenities/', json={"name": ""})
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/v1/amenities/', json={})
        self.assertEqual(response.status_code, 400)

    def test_list_amenities(self):
        self.create_amenity("Wi-Fi")
        self.create_amenity("Air Conditioning")
        response = self.client.get('/api/v1/amenities/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 2)

    def test_update_amenity(self):
        amenity = self.create_amenity()
        response = self.client.put(f'/api/v1/amenities/{amenity["id"]}',
                                   json={"name": "Air Conditioning"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(),
                         {"message": "Amenity updated successfully"})
        response = self.client.get(f'/api/v1/amenities/{amenity["id"]}')
        self.assertEqual(response.get_json()["name"], "Air Conditioning")

    def test_amenity_not_found(self):
        self.assertEqual(
            self.client.get('/api/v1/amenities/unknown').status_code, 404)
        response = self.client.put('/api/v1/amenities/unknown',
                                   json={"name": "Pool"})
        self.assertEqual(response.status_code, 404)


class TestPlaceEndpoints(APITestCase):
    def test_create_place(self):
        owner = self.create_user()
        amenity = self.create_amenity()
        place = self.create_place(owner["id"], [amenity["id"]])
        self.assertEqual(place["title"], "Cozy Apartment")
        self.assertEqual(place["owner_id"], owner["id"])

    def test_create_place_invalid(self):
        owner = self.create_user()
        base = {"title": "Place", "price": 100.0, "latitude": 10.0,
                "longitude": 10.0, "owner_id": owner["id"]}
        cases = [
            {"price": -10.0}, {"price": 0}, {"latitude": 91.0},
            {"latitude": -91.0}, {"longitude": 181.0},
            {"longitude": -181.0}, {"title": ""},
            {"owner_id": "unknown"}, {"amenities": ["unknown"]},
            {"price": "abc"}]
        for overrides in cases:
            response = self.client.post('/api/v1/places/',
                                        json={**base, **overrides})
            self.assertEqual(response.status_code, 400, overrides)

    def test_get_place_with_relationships(self):
        owner = self.create_user()
        amenity = self.create_amenity()
        place = self.create_place(owner["id"], [amenity["id"]])
        response = self.client.get(f'/api/v1/places/{place["id"]}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["owner"]["id"], owner["id"])
        self.assertEqual(data["owner"]["first_name"], "Jane")
        self.assertEqual(data["amenities"],
                         [{"id": amenity["id"], "name": "Wi-Fi"}])
        self.assertEqual(data["reviews"], [])

    def test_list_places(self):
        owner = self.create_user()
        self.create_place(owner["id"])
        response = self.client.get('/api/v1/places/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)
        self.assertEqual(set(response.get_json()[0]),
                         {"id", "title", "latitude", "longitude"})

    def test_update_place(self):
        owner = self.create_user()
        place = self.create_place(owner["id"])
        response = self.client.put(f'/api/v1/places/{place["id"]}', json={
            "title": "Luxury Condo", "price": 200.0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(),
                         {"message": "Place updated successfully"})
        data = self.client.get(f'/api/v1/places/{place["id"]}').get_json()
        self.assertEqual(data["title"], "Luxury Condo")
        self.assertEqual(data["price"], 200.0)

    def test_update_place_invalid_is_atomic(self):
        owner = self.create_user()
        place = self.create_place(owner["id"])
        response = self.client.put(f'/api/v1/places/{place["id"]}', json={
            "title": "Changed", "latitude": 100.0})
        self.assertEqual(response.status_code, 400)
        data = self.client.get(f'/api/v1/places/{place["id"]}').get_json()
        self.assertEqual(data["title"], "Cozy Apartment")

    def test_place_not_found(self):
        self.assertEqual(
            self.client.get('/api/v1/places/unknown').status_code, 404)
        response = self.client.put('/api/v1/places/unknown',
                                   json={"title": "X"})
        self.assertEqual(response.status_code, 404)


class TestReviewEndpoints(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user()
        self.place = self.create_place(self.user["id"])

    def test_create_review(self):
        review = self.create_review(self.user["id"], self.place["id"])
        self.assertEqual(review["rating"], 5)
        self.assertEqual(review["user_id"], self.user["id"])
        self.assertEqual(review["place_id"], self.place["id"])

    def test_create_review_invalid(self):
        base = {"text": "Nice", "rating": 4, "user_id": self.user["id"],
                "place_id": self.place["id"]}
        cases = [{"rating": 0}, {"rating": 6}, {"rating": 4.5},
                 {"text": ""}, {"user_id": "unknown"},
                 {"place_id": "unknown"}]
        for overrides in cases:
            response = self.client.post('/api/v1/reviews/',
                                        json={**base, **overrides})
            self.assertEqual(response.status_code, 400, overrides)

    def test_get_and_list_reviews(self):
        review = self.create_review(self.user["id"], self.place["id"])
        response = self.client.get(f'/api/v1/reviews/{review["id"]}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), review)
        response = self.client.get('/api/v1/reviews/')
        self.assertEqual(len(response.get_json()), 1)

    def test_reviews_by_place(self):
        review = self.create_review(self.user["id"], self.place["id"])
        response = self.client.get(
            f'/api/v1/places/{self.place["id"]}/reviews')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [
            {"id": review["id"], "text": "Great place to stay!",
             "rating": 5}])
        place = self.client.get(
            f'/api/v1/places/{self.place["id"]}').get_json()
        self.assertEqual(len(place["reviews"]), 1)
        response = self.client.get('/api/v1/places/unknown/reviews')
        self.assertEqual(response.status_code, 404)

    def test_update_review(self):
        review = self.create_review(self.user["id"], self.place["id"])
        response = self.client.put(f'/api/v1/reviews/{review["id"]}',
                                   json={"text": "Amazing stay!",
                                         "rating": 4})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(),
                         {"message": "Review updated successfully"})
        data = self.client.get(f'/api/v1/reviews/{review["id"]}').get_json()
        self.assertEqual(data["text"], "Amazing stay!")
        self.assertEqual(data["rating"], 4)
        response = self.client.put(f'/api/v1/reviews/{review["id"]}',
                                   json={"rating": 10})
        self.assertEqual(response.status_code, 400)

    def test_delete_review(self):
        review = self.create_review(self.user["id"], self.place["id"])
        response = self.client.delete(f'/api/v1/reviews/{review["id"]}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(),
                         {"message": "Review deleted successfully"})
        self.assertEqual(
            self.client.get(f'/api/v1/reviews/{review["id"]}').status_code,
            404)
        reviews = self.client.get(
            f'/api/v1/places/{self.place["id"]}/reviews').get_json()
        self.assertEqual(reviews, [])
        response = self.client.delete(f'/api/v1/reviews/{review["id"]}')
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
