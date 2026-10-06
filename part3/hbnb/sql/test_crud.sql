-- CRUD checks for the HBnB schema.
-- Run after schema.sql and initial_data.sql.
-- SQLite: run "PRAGMA foreign_keys = ON;" first so cascades are enforced.

-- READ: initial data
SELECT id, email, is_admin FROM users WHERE email = 'admin@hbnb.io';
SELECT name FROM amenities ORDER BY name;

-- CREATE: a regular user, a place owned by the admin, an amenity link and a review
INSERT INTO users (id, first_name, last_name, email, password, is_admin)
VALUES ('11111111-1111-4111-8111-111111111111', 'John', 'Doe',
        'john.doe@example.com',
        '$2b$12$EyBfEYnT5Z6HIH03HImKF.BaW2/OcGp4DGIlvA3xApf2rjvYRjTem', FALSE);

INSERT INTO places (id, title, description, price, latitude, longitude, owner_id)
VALUES ('22222222-2222-4222-8222-222222222222', 'Cozy Apartment',
        'A nice place to stay', 100.0, 37.7749, -122.4194,
        '36c9050e-ddd3-4c3b-9731-9f487208bbc1');

INSERT INTO place_amenity (place_id, amenity_id)
VALUES ('22222222-2222-4222-8222-222222222222',
        'a45e7b27-bd6a-4f39-b300-9272772d0733');

INSERT INTO reviews (id, text, rating, user_id, place_id)
VALUES ('33333333-3333-4333-8333-333333333333', 'Great place to stay!', 5,
        '11111111-1111-4111-8111-111111111111',
        '22222222-2222-4222-8222-222222222222');

-- READ: a place with its owner, amenities and reviews
SELECT p.title, u.email AS owner, a.name AS amenity
FROM places p
JOIN users u ON u.id = p.owner_id
JOIN place_amenity pa ON pa.place_id = p.id
JOIN amenities a ON a.id = pa.amenity_id;

SELECT r.text, r.rating, u.first_name
FROM reviews r JOIN users u ON u.id = r.user_id
WHERE r.place_id = '22222222-2222-4222-8222-222222222222';

-- UPDATE
UPDATE places SET price = 150.0 WHERE id = '22222222-2222-4222-8222-222222222222';
UPDATE reviews SET rating = 4 WHERE id = '33333333-3333-4333-8333-333333333333';
SELECT price FROM places WHERE id = '22222222-2222-4222-8222-222222222222';

-- DELETE: removing the place also removes its review and amenity links
DELETE FROM places WHERE id = '22222222-2222-4222-8222-222222222222';
SELECT COUNT(*) AS remaining_reviews FROM reviews;
SELECT COUNT(*) AS remaining_links FROM place_amenity;
DELETE FROM users WHERE id = '11111111-1111-4111-8111-111111111111';
