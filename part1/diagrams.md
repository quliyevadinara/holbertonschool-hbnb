# HBnB Diagrams — Mermaid Source

Copy any block below into https://mermaid.live to render or edit. GitHub renders these blocks automatically.

---

## Diagram 1: High-Level Package Diagram

```mermaid
classDiagram
    direction TB

    namespace PresentationLayer {
        class UserAPI
        class PlaceAPI
        class ReviewAPI
        class AmenityAPI
    }

    namespace BusinessLogicLayer {
        class HBnBFacade {
            <<Facade>>
            +create_user(data)
            +update_user(user_id, data)
            +create_place(owner_id, data)
            +get_places(filters)
            +create_review(user_id, data)
            +get_reviews_by_place(place_id)
            +create_amenity(data)
        }
        class User
        class Place
        class Review
        class Amenity
    }

    namespace PersistenceLayer {
        class Repository {
            <<Interface>>
            +add(obj)
            +get(obj_id)
            +get_all()
            +update(obj_id, data)
            +delete(obj_id)
        }
        class DatabaseAccess
    }

    UserAPI --> HBnBFacade : Facade pattern
    PlaceAPI --> HBnBFacade : Facade pattern
    ReviewAPI --> HBnBFacade : Facade pattern
    AmenityAPI --> HBnBFacade : Facade pattern

    HBnBFacade --> User : manages
    HBnBFacade --> Place : manages
    HBnBFacade --> Review : manages
    HBnBFacade --> Amenity : manages

    HBnBFacade --> Repository : Database operations
    Repository --> DatabaseAccess : reads / writes
```

---

## Diagram 2: Business Logic Class Diagram

```mermaid
classDiagram
    class BaseModel {
        <<abstract>>
        +UUID4 id
        +datetime created_at
        +datetime updated_at
        +save() void
        +update(data) void
        +to_dict() dict
    }

    class User {
        +str first_name
        +str last_name
        +str email
        -str password
        +bool is_admin
        +register() User
        +update_profile(data) void
        +delete() void
        +verify_password(password) bool
    }

    class Place {
        +str title
        +str description
        +float price
        +float latitude
        +float longitude
        +User owner
        +List~Amenity~ amenities
        +create() Place
        +update(data) void
        +delete() void
        +list() List~Place~
        +add_amenity(amenity) void
        +remove_amenity(amenity) void
    }

    class Review {
        +int rating
        +str comment
        +User user
        +Place place
        +create() Review
        +update(data) void
        +delete() void
        +list_by_place(place_id) List~Review~
    }

    class Amenity {
        +str name
        +str description
        +create() Amenity
        +update(data) void
        +delete() void
        +list() List~Amenity~
    }

    BaseModel <|-- User
    BaseModel <|-- Place
    BaseModel <|-- Review
    BaseModel <|-- Amenity

    User "1" --> "0..*" Place : owns
    User "1" --> "0..*" Review : writes
    Place "1" *-- "0..*" Review : receives
    Place "0..*" o-- "0..*" Amenity : includes
```

---

## Diagram 3a: User Registration

```mermaid
sequenceDiagram
    actor Client
    participant API as API (Presentation Layer)
    participant BL as HBnBFacade (Business Logic Layer)
    participant DB as Repository (Persistence Layer)

    Client->>API: POST /api/v1/users {first_name, last_name, email, password}
    API->>BL: create_user(data)
    BL->>BL: Validate fields (required, email format)
    break invalid data
        BL-->>API: ValidationError
        API-->>Client: 400 Bad Request
    end
    BL->>DB: get_user_by_email(email)
    DB-->>BL: existing user or None
    break email already registered
        BL-->>API: ConflictError
        API-->>Client: 409 Conflict
    end
    BL->>BL: Create User, hash password
    BL->>DB: add(user)
    DB-->>BL: saved user
    BL-->>API: user data (without password)
    API-->>Client: 201 Created {id, first_name, last_name, email}
```

---

## Diagram 3b: Place Creation

```mermaid
sequenceDiagram
    actor Client
    participant API as API (Presentation Layer)
    participant BL as HBnBFacade (Business Logic Layer)
    participant DB as Repository (Persistence Layer)

    Client->>API: POST /api/v1/places (JWT) {title, description, price, latitude, longitude, amenity_ids}
    API->>API: Verify JWT, extract owner_id
    break invalid token
        API-->>Client: 401 Unauthorized
    end
    API->>BL: create_place(owner_id, data)
    BL->>BL: Validate (price >= 0, -90 <= latitude <= 90, -180 <= longitude <= 180)
    break invalid data
        BL-->>API: ValidationError
        API-->>Client: 400 Bad Request
    end
    BL->>DB: get(owner_id)
    DB-->>BL: owner (User)
    BL->>DB: get amenities(amenity_ids)
    DB-->>BL: List of Amenity
    BL->>BL: Create Place, add_amenity() for each
    BL->>DB: add(place)
    DB-->>BL: saved place
    BL-->>API: place data
    API-->>Client: 201 Created {id, title, owner_id, amenities}
```

---

## Diagram 3c: Review Submission

```mermaid
sequenceDiagram
    actor Client
    participant API as API (Presentation Layer)
    participant BL as HBnBFacade (Business Logic Layer)
    participant DB as Repository (Persistence Layer)

    Client->>API: POST /api/v1/reviews (JWT) {place_id, rating, comment}
    API->>API: Verify JWT, extract user_id
    break invalid token
        API-->>Client: 401 Unauthorized
    end
    API->>BL: create_review(user_id, data)
    BL->>DB: get(place_id)
    DB-->>BL: place or None
    break place not found
        BL-->>API: NotFoundError
        API-->>Client: 404 Not Found
    end
    BL->>BL: Validate rating (1-5) and comment
    break invalid data
        BL-->>API: ValidationError
        API-->>Client: 400 Bad Request
    end
    BL->>BL: Create Review linked to user and place
    BL->>DB: add(review)
    DB-->>BL: saved review
    BL-->>API: review data
    API-->>Client: 201 Created {id, rating, comment, user_id, place_id}
```

---

## Diagram 3d: Fetching a List of Places

```mermaid
sequenceDiagram
    actor Client
    participant API as API (Presentation Layer)
    participant BL as HBnBFacade (Business Logic Layer)
    participant DB as Repository (Persistence Layer)

    Client->>API: GET /api/v1/places?price_max=100&amenity=wifi
    API->>BL: get_places(filters)
    BL->>BL: Parse and validate filters
    break invalid filter value
        BL-->>API: ValidationError
        API-->>Client: 400 Bad Request
    end
    BL->>DB: get_all() with filters
    DB-->>BL: List of Place (may be empty)
    BL->>BL: Serialize places (id, title, price, latitude, longitude)
    BL-->>API: list of places
    API-->>Client: 200 OK [ {id, title, price, ...}, ... ]
```
