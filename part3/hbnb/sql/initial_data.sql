-- Initial data for HBnB

-- Administrator account
-- Password: admin1234 (stored as a bcrypt hash)
INSERT INTO users (id, first_name, last_name, email, password, is_admin)
VALUES (
    '36c9050e-ddd3-4c3b-9731-9f487208bbc1',
    'Admin',
    'HBnB',
    'admin@hbnb.io',
    '$2b$12$EyBfEYnT5Z6HIH03HImKF.BaW2/OcGp4DGIlvA3xApf2rjvYRjTem',
    TRUE
);

-- Initial amenities
INSERT INTO amenities (id, name) VALUES
    ('a45e7b27-bd6a-4f39-b300-9272772d0733', 'WiFi'),
    ('dd8635b5-acf5-4724-89b3-9ab80ded0ca7', 'Swimming Pool'),
    ('7a2985b3-8f50-41a1-a7f9-345acd6f817b', 'Air Conditioning');
