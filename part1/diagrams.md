# HBnB Diagrams — Mermaid Source

Copy any block below into https://mermaid.live to render or edit.

---

## Diagram 1: High-Level Package Diagram

```mermaid
classDiagram
    class PresentationLayer {
        <<Interface>>
        +UserAPI
        +PlaceAPI
        +ReviewAPI
    }
    class BusinessLogicLayer {
        +User
        +Place
        +Review
        +Amenity
    }
    class PersistenceLayer {
        +DatabaseAccess
        +Repositories
        +ORM_SQLAlchemy
    }
    PresentationLayer --> BusinessLogicLayer : Facade pattern
    BusinessLogicLayer --> PersistenceLayer : Database operations
```

---

## Diagram 2: Business Logic Class Diagram

```mermaid
classDiagram
    class BaseModel {
        +UUID4 id
        +datetime created_at
        +datetime updated_at
        +save()
        +to_dict()
        +delete()
    }

    class User {
        +str first_name
        +str last_name
        +str email
        +str password
        +bool is_admin
        +register()
        +update_profile()
        +delete()
    }

    class Place {
        +str title
        +str description
        +float price
        +float latitude
        +float longitude
        +UUID4 owner_id
        +create()
        +update()
        +list_by_criteria()
        +delete()
    }

    class Review {
        +int rating
        +str text
        +UUID4 place_id
        +UUID4 user_id
        +submit()
        +update()
        +delete()
        +validate_rating()
    }

    class Amenity {
        +str name
        +str description
        +create()
        +list()
        +delete()
    }

    BaseModel <|-- User : inherits
    BaseModel <|-- Place : inherits
    BaseModel <|-- Review : inherits
    BaseModel <|-- Amenity : inherits

    User "1" --> "*" Place : owns
    User "1" --> "*" Review : writes
    Place "1" --> "*" Review : has
    Place "*" --> "*" Amenity : has amenities
```

---

## Diagram 3a: User Registration

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant BusinessLogic
    participant Database

    Client->>API: POST /api/v1/users (email, password, name)
    API->>BusinessLogic: validate_and_create(data)
    BusinessLogic->>Database: check_email_exists(email)
    Database-->>BusinessLogic: False
    BusinessLogic->>Database: save_user(hashed_data)
    Database-->>BusinessLogic: user_id, created_at
    BusinessLogic-->>API: UserDTO (id, email)
    API-->>Client: 201 Created {id, email, created_at}

    Note over BusinessLogic,Database: alt [email exists] → 409 Conflict
```

---

## Diagram 3b: Place Creation

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant BusinessLogic
    participant Database

    Client->>API: POST /api/v1/places (JWT, place data)
    Note over API: Verify JWT — 401 if invalid
    API->>BusinessLogic: create_place(owner_id, payload)
    Note over BusinessLogic: Validate fields
    BusinessLogic->>Database: insert_place(place_record)
    Database-->>BusinessLogic: place_id, created_at
    BusinessLogic->>Database: link_amenities(place_id, amenity_ids)
    Database-->>BusinessLogic: OK
    BusinessLogic-->>API: PlaceDTO (id, title, owner_id)
    API-->>Client: 201 Created {place_id, title}
```

---

## Diagram 3c: Review Submission

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant BusinessLogic
    participant Database

    Client->>API: POST /api/v1/reviews (JWT, place_id, rating, text)
    Note over API: Verify JWT — 401 if invalid
    API->>BusinessLogic: submit_review(user_id, place_id, data)
    BusinessLogic->>Database: get_place(place_id)
    Database-->>BusinessLogic: Place record (or 404)
    BusinessLogic->>Database: find_review(user_id, place_id)
    Database-->>BusinessLogic: None (or 409)
    Note over BusinessLogic: validate_rating() — 400 if out of range
    BusinessLogic->>Database: insert_review(review_record)
    Database-->>BusinessLogic: review_id, created_at
    BusinessLogic-->>API: ReviewDTO (id, rating, text)
    API-->>Client: 201 Created {review_id, place_id}
```

---

## Diagram 3d: Fetching a List of Places

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant BusinessLogic
    participant Database

    Client->>API: GET /api/v1/places?city=Paris&price_max=100&page=1
    API->>BusinessLogic: get_places(filters, pagination)
    Note over BusinessLogic: Parse and sanitise filters
    BusinessLogic->>Database: query(filters, limit, offset)
    Database-->>BusinessLogic: rows[], total_count
    BusinessLogic->>Database: get_amenities_bulk(place_ids)
    Database-->>BusinessLogic: amenities_map
    Note over BusinessLogic: Serialize DTOs
    BusinessLogic-->>API: PlaceList[] + pagination metadata
    API-->>Client: 200 OK {results[], total, page, pages}
```
