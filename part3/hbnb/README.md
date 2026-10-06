# HBnB Evolution — Part 3: Authentication and Database

Part 3 builds on [Part 2](../../part2/hbnb/README.md). It adds configuration handling, bcrypt password hashing, JWT authentication, role-based access control, and SQLAlchemy persistence in place of the in-memory repository.

## Project Structure

```
hbnb/
├── app/
│   ├── __init__.py            # create_app(config), db, bcrypt, jwt, create-admin command
│   ├── api/v1/
│   │   ├── auth.py            # /api/v1/auth (login, protected)
│   │   ├── users.py
│   │   ├── amenities.py
│   │   ├── places.py
│   │   └── reviews.py
│   ├── models/                # SQLAlchemy models with validation
│   ├── services/facade.py     # HBnBFacade
│   └── persistence/
│       └── repository.py      # Repository, InMemoryRepository, SQLAlchemyRepository
├── tests/
├── config.py                  # DevelopmentConfig, TestingConfig
├── run.py
└── requirements.txt
```

## Installation and Running

```bash
cd part3/hbnb
pip install -r requirements.txt
flask --app run create-admin --email admin@hbnb.io   # asks for a password
python run.py
```

The API runs on `http://127.0.0.1:5000`, with Swagger at `http://127.0.0.1:5000/api/v1/`. The SQLite database is created automatically in `instance/development.db`.

Creating users requires an administrator, so the first admin is created with the `create-admin` command.

## Configuration (Task 0)

`create_app(config_class="config.DevelopmentConfig")` loads the configuration passed to it:

| Class               | Use            | Database                               |
| ------------------- | -------------- | -------------------------------------- |
| `DevelopmentConfig` | `python run.py`| `sqlite:///development.db` (or `DATABASE_URL`) |
| `TestingConfig`     | unit tests     | `sqlite:///:memory:`                   |

`SECRET_KEY` and `JWT_SECRET_KEY` are read from environment variables when set.

## Password Hashing (Task 1)

`User.hash_password()` hashes the password with bcrypt (Flask-Bcrypt) before it is stored, and `User.verify_password()` checks it at login. The password is required when a user is created and is never returned by any endpoint.

## JWT Authentication (Task 2)

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@hbnb.io", "password": "<password>"}'
# {"access_token": "eyJ..."}
```

The token's identity is the user ID, and it carries an `is_admin` claim. Send it as `Authorization: Bearer <access_token>`. Wrong credentials return `401 {"error": "Invalid credentials"}`.

## Access Rules (Tasks 3 and 4)

| Endpoint                          | Public | Authenticated user                                   | Admin                         |
| --------------------------------- | ------ | ---------------------------------------------------- | ----------------------------- |
| `GET` users, places, amenities, reviews | ✅ |                                                     |                               |
| `POST /users/`                    |        | ❌ 403                                               | ✅                            |
| `PUT /users/<id>`                 |        | Own profile only; not email or password (400)        | Any user, email and password  |
| `POST`, `PUT /amenities/`         |        | ❌ 403                                               | ✅                            |
| `POST /places/`                   |        | ✅ owner is the logged-in user                       | ✅ any owner                  |
| `PUT`, `DELETE /places/<id>`      |        | Own places only (403 otherwise)                      | ✅ any place                  |
| `POST /reviews/`                  |        | ✅ not on own place, once per place (400 otherwise)  | ✅                            |
| `PUT`, `DELETE /reviews/<id>`     |        | Own reviews only (403 otherwise)                     | ✅ any review                 |

Missing or invalid tokens return `401` (`{"msg": "Missing Authorization Header"}`).

## SQLAlchemy Persistence (Task 5)

`SQLAlchemyRepository` implements the same `Repository` interface as `InMemoryRepository` (`add`, `get`, `get_all`, `update`, `delete`, `get_by_attribute`). The facade now uses it for every entity, so the API code did not change.

The models are mapped to tables `users`, `places`, `reviews`, `amenities`, and the `place_amenity` association table. Relationships: a user owns places and writes reviews; deleting a place deletes its reviews; a user can review a place only once (unique constraint).

## Tests

```bash
python -m unittest discover -s tests -t .
```

36 tests cover the configuration, password hashing, login, every access rule (401/403/400), admin bypass, validation, and database persistence. Each test runs on a fresh in-memory database.
