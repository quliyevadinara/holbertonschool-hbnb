# HBnB Part 2 — Testing Report

This report covers the validation rules implemented in the Business Logic layer, the automated tests, and the black-box tests run with cURL against a running server.

## 1. Validation Rules

Validation lives in the model classes, so it applies to every request that reaches the facade. Flask-RESTx (`validate=True`) also rejects payloads with missing required fields or wrong JSON types before they reach the business logic.

| Entity  | Field                   | Rule                                              | Error example                              |
| ------- | ----------------------- | ------------------------------------------------- | ------------------------------------------ |
| User    | `first_name`, `last_name` | Non-empty string, max 50 characters             | `first_name must be a non-empty string`    |
| User    | `email`                 | Valid email format, unique                        | `Email already registered`                 |
| User    | `password`              | Non-empty, stored hashed, never returned          | n/a                                        |
| Amenity | `name`                  | Non-empty string, max 50 characters               | `name must be a non-empty string`          |
| Place   | `title`                 | Non-empty string, max 100 characters              | `title must be a non-empty string`         |
| Place   | `price`                 | Number greater than 0                             | `price must be a positive number`          |
| Place   | `latitude`              | Number between -90 and 90                         | `latitude must be between -90 and 90`      |
| Place   | `longitude`             | Number between -180 and 180                       | `longitude must be between -180 and 180`   |
| Place   | `owner_id`, `amenities` | Must reference existing objects                   | `Owner not found`                          |
| Review  | `text`                  | Non-empty string                                  | `text must be a non-empty string`          |
| Review  | `rating`                | Integer between 1 and 5                           | `rating must be between 1 and 5`           |
| Review  | `user_id`, `place_id`   | Must reference existing objects                   | `User not found`, `Place not found`        |

Updates are atomic: if one field in a `PUT` is invalid, the request returns `400` and no field is changed.

## 2. Automated Tests

```bash
cd part2/hbnb
python -m unittest discover -s tests -t .
```

```
............................................
----------------------------------------------------------------------
Ran 44 tests in 5.285s

OK
```

| File             | Tests | Coverage                                                                                                      |
| ---------------- | ----- | ------------------------------------------------------------------------------------------------------------- |
| `test_models.py` | 18    | Creation, relationships, every validation rule and boundary value, password hashing, atomic updates           |
| `test_api.py`    | 26    | Every endpoint: success cases, `400` invalid data, `404` unknown IDs, nested place details, review deletion   |

Each API test starts from empty repositories, so tests do not depend on each other.

## 3. Black-Box Tests with cURL

Server started with `python run.py`. Base URL: `http://localhost:5000/api/v1`. IDs below come from the actual run.

### Users

| # | Request | Expected | Result |
| - | ------- | -------- | ------ |
| 1 | `POST /users/` `{"first_name":"John","last_name":"Doe","email":"john.doe@example.com","password":"secret"}` | 201, user without password | ✅ 201 `{"id": "46553f00-…", "first_name": "John", "last_name": "Doe", "email": "john.doe@example.com"}` |
| 2 | `POST /users/` with the same email | 400 | ✅ 400 `{"error": "Email already registered"}` |
| 3 | `POST /users/` `{"first_name":"","last_name":"","email":"invalid-email"}` | 400 | ✅ 400 `{"error": "first_name must be a non-empty string"}` |
| 4 | `GET /users/46553f00-…` | 200 | ✅ 200 user details |
| 5 | `GET /users/unknown-id` | 404 | ✅ 404 `{"error": "User not found"}` |
| 6 | `PUT /users/46553f00-…` `{"first_name":"Johnny"}` | 200, updated user | ✅ 200 `"first_name": "Johnny"` |

### Amenities

| # | Request | Expected | Result |
| - | ------- | -------- | ------ |
| 7  | `POST /amenities/` `{"name":"Wi-Fi"}` | 201 | ✅ 201 `{"id": "88f5fd04-…", "name": "Wi-Fi", "description": ""}` |
| 8  | `POST /amenities/` `{"name":""}` | 400 | ✅ 400 `{"error": "name must be a non-empty string"}` |
| 9  | `PUT /amenities/88f5fd04-…` `{"name":"Air Conditioning"}` | 200 | ✅ 200 `{"message": "Amenity updated successfully"}` |
| 10 | `GET /amenities/` | 200, list | ✅ 200 `[{"id": "88f5fd04-…", "name": "Air Conditioning", "description": ""}]` |

### Places

| # | Request | Expected | Result |
| - | ------- | -------- | ------ |
| 11 | `POST /places/` valid place with owner and amenity | 201 | ✅ 201 `{"id": "82ea4ba9-…", "title": "Cozy Apartment", …, "owner_id": "46553f00-…"}` |
| 12 | `POST /places/` with `"price": -10.0` | 400 | ✅ 400 `{"error": "price must be a positive number"}` |
| 13 | `POST /places/` with `"latitude": 95.0` | 400 | ✅ 400 `{"error": "latitude must be between -90 and 90"}` |
| 14 | `POST /places/` with `"owner_id": "unknown-id"` | 400 | ✅ 400 `{"error": "Owner not found"}` |
| 15 | `PUT /places/82ea4ba9-…` `{"title":"Luxury Condo","price":200.0}` | 200 | ✅ 200 `{"message": "Place updated successfully"}` |
| 16 | `GET /places/82ea4ba9-…` | 200 with owner, amenities, reviews | ✅ 200 (see below) |

Response of test 16, showing the related objects:

```json
{
  "id": "82ea4ba9-461f-40ff-97f0-c5f6b1ce0b65",
  "title": "Luxury Condo",
  "description": "A nice place to stay",
  "price": 200.0,
  "latitude": 37.7749,
  "longitude": -122.4194,
  "owner": {"id": "46553f00-ca50-4668-90c9-7851b6ae8d94", "first_name": "Johnny", "last_name": "Doe", "email": "john.doe@example.com"},
  "amenities": [{"id": "88f5fd04-7436-4d47-82cd-ff45c89a0ecf", "name": "Air Conditioning"}],
  "reviews": [{"id": "4f89b697-d6bb-495e-a4d8-4a2591b874a5", "text": "Great place to stay!", "rating": 5, "user_id": "46553f00-ca50-4668-90c9-7851b6ae8d94"}]
}
```

### Reviews

| # | Request | Expected | Result |
| - | ------- | -------- | ------ |
| 17 | `POST /reviews/` `{"text":"Great place to stay!","rating":5,"user_id":…,"place_id":…}` | 201 | ✅ 201 `{"id": "4f89b697-…", "text": "Great place to stay!", "rating": 5, "user_id": …, "place_id": …}` |
| 18 | `POST /reviews/` with `"rating": 6` | 400 | ✅ 400 `{"error": "rating must be between 1 and 5"}` |
| 19 | `POST /reviews/` with `"text": ""` | 400 | ✅ 400 `{"error": "text must be a non-empty string"}` |
| 20 | `GET /places/82ea4ba9-…/reviews` | 200, list | ✅ 200 `[{"id": "4f89b697-…", "text": "Great place to stay!", "rating": 5}]` |
| 21 | `PUT /reviews/4f89b697-…` `{"text":"Amazing stay!","rating":4}` | 200 | ✅ 200 `{"message": "Review updated successfully"}` |
| 22 | `DELETE /reviews/4f89b697-…` | 200 | ✅ 200 `{"message": "Review deleted successfully"}` |
| 23 | `DELETE /reviews/4f89b697-…` again | 404 | ✅ 404 `{"error": "Review not found"}` |

All 23 manual tests returned the expected status code and body.

## 4. Swagger Documentation

The Swagger UI generated by Flask-RESTx is available at `http://localhost:5000/api/v1/` (HTTP 200). `swagger.json` documents all 9 routes:

```
/api/v1/amenities/            /api/v1/amenities/{amenity_id}
/api/v1/places/               /api/v1/places/{place_id}
/api/v1/places/{place_id}/reviews
/api/v1/reviews/              /api/v1/reviews/{review_id}
/api/v1/users/                /api/v1/users/{user_id}
```

Each operation lists its input model and its possible responses (`201`, `200`, `400`, `404`), so the API can also be tested interactively from the Swagger page.
