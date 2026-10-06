# HBnB Evolution — Part 2: Business Logic and API

Part 2 implements the design from [Part 1](../../part1/README.md): a Flask REST API organized in three layers, with the Facade pattern between them and an in-memory repository for storage.

## Project Structure

```
hbnb/
├── app/
│   ├── __init__.py            # create_app(): Flask app + Flask-RESTx Api
│   ├── api/
│   │   └── v1/
│   │       ├── users.py       # /api/v1/users
│   │       ├── amenities.py   # /api/v1/amenities
│   │       ├── places.py      # /api/v1/places
│   │       └── reviews.py     # /api/v1/reviews
│   ├── models/
│   │   ├── base_model.py      # id (UUID4), created_at, updated_at
│   │   ├── user.py
│   │   ├── place.py
│   │   ├── review.py
│   │   └── amenity.py
│   ├── services/
│   │   ├── __init__.py        # facade singleton
│   │   └── facade.py          # HBnBFacade
│   └── persistence/
│       └── repository.py      # Repository interface + InMemoryRepository
├── tests/
│   ├── test_models.py         # business logic unit tests
│   └── test_api.py            # endpoint tests
├── config.py
├── run.py
├── requirements.txt
├── TESTING.md                 # testing report
└── README.md
```

| Layer          | Package            | Role                                                                     |
| -------------- | ------------------ | ------------------------------------------------------------------------ |
| Presentation   | `app/api/v1`       | HTTP endpoints, input format checks, JSON responses and status codes     |
| Business Logic | `app/models`, `app/services` | Entities, validation rules, and the `HBnBFacade` entry point   |
| Persistence    | `app/persistence`  | `InMemoryRepository`, replaced by a database-backed repository in Part 3 |

The API never touches models or repositories directly. Every endpoint calls one `facade` method.

## Installation and Running

```bash
cd part2/hbnb
pip install -r requirements.txt
python run.py
```

The API runs on `http://127.0.0.1:5000`. The Swagger documentation is at `http://127.0.0.1:5000/api/v1/`.

## Business Logic

Every entity inherits from `BaseModel`: a UUID4 `id`, `created_at`, `updated_at`, `save()`, and `update(data)`. `update()` is all or nothing: if one value is invalid, nothing changes.

| Entity  | Attributes                                                                 | Validation                                                                                   |
| ------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| User    | `first_name`, `last_name`, `email`, `password`, `is_admin`                 | Names required, max 50 chars; valid and unique email; password stored only as a hash         |
| Amenity | `name`, `description`                                                      | Name required, max 50 chars                                                                   |
| Place   | `title`, `description`, `price`, `latitude`, `longitude`, `owner`, `amenities`, `reviews` | Title required, max 100 chars; price > 0; latitude -90..90; longitude -180..180; owner and amenities must exist |
| Review  | `text`, `rating`, `user`, `place`                                          | Text required; rating is an integer 1..5; user and place must exist                          |

Relationships: a `Place` keeps its `owner` (User), its list of `amenities`, and its list of `reviews`. A `Review` keeps its `user` and `place`. Deleting a review also removes it from its place.

## API Endpoints

| Method | Endpoint                             | Success | Errors   |
| ------ | ------------------------------------ | ------- | -------- |
| POST   | `/api/v1/users/`                     | 201     | 400      |
| GET    | `/api/v1/users/`                     | 200     |          |
| GET    | `/api/v1/users/<user_id>`            | 200     | 404      |
| PUT    | `/api/v1/users/<user_id>`            | 200     | 400, 404 |
| POST   | `/api/v1/amenities/`                 | 201     | 400      |
| GET    | `/api/v1/amenities/`                 | 200     |          |
| GET    | `/api/v1/amenities/<amenity_id>`     | 200     | 404      |
| PUT    | `/api/v1/amenities/<amenity_id>`     | 200     | 400, 404 |
| POST   | `/api/v1/places/`                    | 201     | 400      |
| GET    | `/api/v1/places/`                    | 200     |          |
| GET    | `/api/v1/places/<place_id>`          | 200     | 404      |
| PUT    | `/api/v1/places/<place_id>`          | 200     | 400, 404 |
| GET    | `/api/v1/places/<place_id>/reviews`  | 200     | 404      |
| POST   | `/api/v1/reviews/`                   | 201     | 400      |
| GET    | `/api/v1/reviews/`                   | 200     |          |
| GET    | `/api/v1/reviews/<review_id>`        | 200     | 404      |
| PUT    | `/api/v1/reviews/<review_id>`        | 200     | 400, 404 |
| DELETE | `/api/v1/reviews/<review_id>`        | 200     | 404      |

Users, amenities, and places cannot be deleted in Part 2. Reviews are the only entity with a DELETE endpoint.

Errors always use the format `{"error": "<message>"}`. The password is never included in any response.

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "password": "secret"}'
```

```json
{"id": "46553f00-ca50-4668-90c9-7851b6ae8d94", "first_name": "John", "last_name": "Doe", "email": "john.doe@example.com"}
```

## Tests

```bash
cd part2/hbnb
python -m unittest discover -s tests -t .
```

The results and the manual cURL tests are documented in [TESTING.md](TESTING.md).
