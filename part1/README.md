# HBnB — Technical Architecture Document

**Part 1: Design & Documentation**

---

## Introduction

HBnB is a simplified Airbnb-like web application. This document is the authoritative technical blueprint for the project's architecture and design, produced before any implementation begins. It captures every structural decision so that the development phase can proceed from a clear, agreed-upon foundation.

The document covers three areas:

1. **High-Level Architecture** — the three-layer package structure and the Facade pattern that connects the layers.
2. **Business Logic Layer** — a detailed class diagram for the four core entities (User, Place, Review, Amenity) and their relationships.
3. **API Interaction Flow** — sequence diagrams for the four primary API calls: user registration, place creation, review submission, and fetching a list of places.

---

## 1. High-Level Architecture

### 1.1 Overview

HBnB uses a classic **three-layer (N-tier) architecture**. Each layer has a single responsibility and communicates only with the layer directly adjacent to it.

```
┌─────────────────────────────────────┐
│        Presentation Layer           │  ← HTTP / REST API surface
│   User API · Place API · Review API │
└────────────────┬────────────────────┘
                 │  Facade pattern
┌────────────────▼────────────────────┐
│       Business Logic Layer          │  ← Domain rules & models
│    User · Place · Review · Amenity  │
└────────────────┬────────────────────┘
                 │  Database operations
┌────────────────▼────────────────────┐
│         Persistence Layer           │  ← Data storage & retrieval
│   DB Access · Repositories · ORM   │
└─────────────────────────────────────┘
```

### 1.2 Layer Responsibilities

**Presentation Layer (Services / API)**
Receives HTTP requests, authenticates callers (JWT), serializes/deserializes JSON, and delegates all domain work to the Business Logic layer via the Facade. It contains no business rules of its own.

Key components:

- `UserAPI` — registration, login, profile management endpoints
- `PlaceAPI` — create, list, retrieve, update, delete place endpoints
- `ReviewAPI` — submit, fetch, and delete review endpoints

**Business Logic Layer (Models)**
Houses the domain models (User, Place, Review, Amenity), enforces business rules (validation, uniqueness constraints, authorization checks), and orchestrates multi-step operations.

**Persistence Layer**
Responsible solely for durable storage and retrieval. Uses SQLAlchemy ORM and the Repository pattern so that swapping the underlying database does not affect the layers above.

### 1.3 The Facade Pattern

The Facade pattern provides a single, simplified interface between adjacent layers. The Presentation layer calls well-defined Facade methods (e.g., `create_place(owner_id, payload)`) rather than reaching into model internals. This:

- Keeps the API thin and testable in isolation.
- Allows the Business Logic layer to be refactored or extended without touching the Presentation layer.
- Prevents circular dependencies between layers.

---

## 2. Business Logic Layer — Class Diagram

### 2.1 BaseModel

All four domain entities inherit from `BaseModel`, which provides:

| Attribute    | Type     | Description                                       |
| ------------ | -------- | ------------------------------------------------- |
| `id`         | UUID4    | Globally unique identifier, generated on creation |
| `created_at` | datetime | UTC timestamp set on first save                   |
| `updated_at` | datetime | UTC timestamp refreshed on every save             |

Methods: `save()`, `to_dict()`, `delete()`.

Using a shared base class ensures every entity has a consistent identity scheme and audit trail without repeating the definition.

### 2.2 Entity Descriptions

**User**
Represents a registered person. Stores hashed credentials and profile information. A User can own multiple Places and write multiple Reviews. The `is_admin` flag gates administrative operations.

| Key attributes | `first_name`, `last_name`, `email`, `password` (bcrypt hash), `is_admin` |
| -------------- | ------------------------------------------------------------------------ |
| Key methods    | `register()`, `update_profile()`, `delete()`                             |
| Relationships  | One-to-many with Place (as owner), one-to-many with Review (as author)   |

**Place**
A property listing created by a User. Stores location (lat/lon), pricing, and a descriptive text. A Place can have many Reviews and many Amenities (many-to-many via a join table).

| Key attributes | `title`, `description`, `price`, `latitude`, `longitude`, `owner_id`              |
| -------------- | --------------------------------------------------------------------------------- |
| Key methods    | `create()`, `update()`, `list_by_criteria()`, `delete()`                          |
| Relationships  | Many-to-one with User (owner), one-to-many with Review, many-to-many with Amenity |

**Review**
A user-authored rating and textual comment for a Place. Business rules enforce that a single user may only leave one review per place and that the `rating` field must be an integer between 1 and 5 inclusive.

| Key attributes | `rating` (int, 1–5), `text`, `place_id`, `user_id`      |
| -------------- | ------------------------------------------------------- |
| Key methods    | `submit()`, `update()`, `delete()`, `validate_rating()` |
| Relationships  | Many-to-one with Place, many-to-one with User           |

**Amenity**
A feature that can be associated with a Place (e.g., Wi-Fi, pool, parking). Amenities are independent entities managed separately from places and linked via a join table.

| Key attributes | `name`, `description`            |
| -------------- | -------------------------------- |
| Key methods    | `create()`, `list()`, `delete()` |
| Relationships  | Many-to-many with Place          |

### 2.3 Relationship Summary

```
User  1 ──────────── * Place      (ownership)
User  1 ──────────── * Review     (authorship)
Place 1 ──────────── * Review     (subject)
Place * ──────────── * Amenity    (features, join table)
```

All entities extend `BaseModel` (generalization/inheritance relationship in UML).

---

## 3. API Interaction Flow — Sequence Diagrams

All four diagrams follow the same participant conventions:

| Participant    | Role                                                   |
| -------------- | ------------------------------------------------------ |
| Client         | External caller (browser, mobile app, curl)            |
| API            | Presentation layer — HTTP routing, auth, serialization |
| Business Logic | Domain models and validation                           |
| Database       | Persistence layer — SQL queries via ORM                |

Solid arrows represent requests; dashed arrows represent responses.

---

### 3.1 User Registration

**Endpoint:** `POST /api/v1/users`
**Auth required:** No

**Flow:**

1. Client sends `email`, `password`, and profile fields.
2. API passes the payload to Business Logic (`validate_and_create`).
3. Business Logic checks the database for an existing account with the same email.
4. If the email is free, the password is hashed and the user record is saved.
5. The database returns the new `user_id` and `created_at`.
6. Business Logic assembles a UserDTO and returns it to the API.
7. API responds with `201 Created` and the user object.

**Error paths:**

- Duplicate email → `409 Conflict`
- Missing/invalid fields → `400 Bad Request`

**Key design decision:** Email uniqueness is checked by the Business Logic layer (not the API), so the rule is enforced consistently regardless of which client or internal service calls the Facade.

---

### 3.2 Place Creation

**Endpoint:** `POST /api/v1/places`
**Auth required:** Yes (JWT Bearer)

**Flow:**

1. Client sends a JWT token and the place payload (title, description, price, coordinates, amenity IDs).
2. API verifies the JWT and extracts `owner_id`. An invalid token returns `401 Unauthorized` immediately.
3. API calls `create_place(owner_id, payload)` on the Business Logic Facade.
4. Business Logic validates required fields and value ranges (e.g., price > 0, valid lat/lon).
5. The place record is inserted into the database.
6. Amenity associations are written to the join table in a second operation.
7. A PlaceDTO (id, title, owner_id) is returned up to the API.
8. API responds with `201 Created`.

**Key design decision:** Amenity linking is a separate persistence call after the main insert. This keeps the place table schema clean and isolates the join-table logic, making it easier to add/remove amenities later without touching the place record itself.

---

### 3.3 Review Submission

**Endpoint:** `POST /api/v1/reviews`
**Auth required:** Yes (JWT Bearer)

**Flow:**

1. Client provides a JWT, `place_id`, `rating` (1–5), and `text`.
2. API verifies the JWT.
3. Business Logic is called with `submit_review(user_id, place_id, data)`.
4. Business Logic queries the database to confirm the referenced Place exists (`404` if not).
5. Business Logic queries for an existing review from this user for this place (`409` if found).
6. The `rating` value is validated (1–5 range; `400` if invalid).
7. The review record is inserted and the new `review_id` / `created_at` are returned.
8. A ReviewDTO is returned to the API, which responds with `201 Created`.

**Key design decision:** The duplicate-review guard lives in Business Logic (not as a unique constraint only in the database) so that the violation can return a human-readable `409 Conflict` with a clear message, rather than a raw database integrity error.

---

### 3.4 Fetching a List of Places

**Endpoint:** `GET /api/v1/places?city=...&price_max=...&page=...`
**Auth required:** No (public endpoint)

**Flow:**

1. Client sends query parameters as filters (city, price range, amenity IDs, etc.) and pagination parameters (page, per_page).
2. API passes the raw query string to Business Logic (`get_places(filters, pagination)`).
3. Business Logic parses and sanitises the filters (coerces types, sets defaults for pagination).
4. A filtered, paginated SQL query is executed against the database.
5. The result rows and `total_count` are returned.
6. Amenities for all matching places are fetched in a **single bulk query** (using `WHERE place_id IN (...)`) to avoid N+1 query performance issues.
7. Business Logic serialises the rows into PlaceDTOs and attaches pagination metadata (`total`, `page`, `pages`).
8. API responds with `200 OK` and the result object. An empty result set returns `200` with `results: []`, not `404`.

**Key design decision:** The N+1 guard (bulk amenity fetch) is a Business Logic responsibility rather than a persistence-layer concern, because it requires knowledge of the full result set before the query can be constructed. This keeps the Persistence layer's repository methods simple and composable.

---

## 4. Summary of Design Decisions

| Decision                          | Rationale                                                                                                       |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Three-layer architecture          | Separation of concerns; each layer can be tested and replaced independently                                     |
| Facade pattern between layers     | Prevents tight coupling; the API surface remains stable as internal logic evolves                               |
| BaseModel with UUID4              | Globally unique IDs that are safe to expose in URLs without leaking sequential information                      |
| JWT auth at the API layer         | Auth is a cross-cutting concern, not a business rule; keeping it at the boundary avoids polluting domain models |
| Business-Logic-layer validation   | Rules are enforced in one place regardless of which client calls the API                                        |
| Bulk amenity fetch                | Avoids N+1 query problem on list endpoints; critical for performance at scale                                   |
| Repository pattern in Persistence | Decouples domain code from SQLAlchemy specifics; simplifies unit testing with mock repositories                 |

---

_Document version 1.0 — HBnB Part 1 Design Phase_
