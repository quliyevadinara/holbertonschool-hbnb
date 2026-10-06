# HBnB Evolution — Part 4: Simple Web Client

A front-end for the HBnB API from [Part 3](../part3/hbnb/README.md), written in HTML5, CSS3, and plain JavaScript (Fetch API, no framework).

## Files

```
part4/
├── index.html        # list of places with a price filter
├── login.html        # login form
├── place.html        # place details, reviews, and the add-review form
├── add_review.html   # standalone add-review form
├── styles.css
├── scripts.js        # all client logic
└── images/
    ├── logo.png
    └── icon.png      # favicon
```

## Running

1. Start the API (Part 3). It must run on `http://127.0.0.1:5000`, the address set in `API_URL` at the top of `scripts.js`:

   ```bash
   cd part3/hbnb
   pip install -r requirements.txt
   python run.py
   ```

   The API enables CORS for `/api/*`, so the pages can call it from another origin.

2. Serve this folder with any static server and open `http://127.0.0.1:8000`:

   ```bash
   cd part4
   python -m http.server 8000
   ```

To log in, use an account from the database, for example the administrator inserted by `part3/hbnb/sql/initial_data.sql` (`admin@hbnb.io` / `admin1234`).

## Pages

| Page              | Behavior                                                                                                                                     |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `login.html`      | Sends the email and password to `POST /auth/login`. On success, stores the JWT in the `token` cookie and redirects to `index.html`. On failure, shows the error. |
| `index.html`      | Loads `GET /places/` and shows each place as a `place-card` (name, price per night, `details-button`). The price filter (10, 50, 100, All) hides places above the selected price without reloading. The login link is hidden once logged in. |
| `place.html`      | Reads `?id=` from the URL and loads `GET /places/<id>`: host, price, description, amenities, and reviews as `review-card`s. The add-review form is shown only to logged-in users. |
| `add_review.html` | Redirects visitors without a token to `index.html`. Submits `POST /reviews/` with the JWT, then shows a success message and clears the form, or shows the API error (for example, reviewing your own place). |

All pages share a header (logo with class `logo`, navigation with `index.html` and `login.html`, login link with class `login-button`) and a footer with the rights notice. Logged-in users get a Logout button that deletes the cookie.

## Design

- Place and review cards: `margin: 20px`, `padding: 10px`, `border: 1px solid #ddd`, `border-radius: 10px`.
- Palette: terracotta `#e85d4a` on a warm light background; font: Nunito Sans.
- The layout adapts to phone widths.
- API data is inserted with `textContent`, never `innerHTML`, so place titles or reviews cannot inject HTML.

## Validation

All four pages pass the [W3C Markup Validator](https://validator.w3.org/) with no errors or warnings, and `styles.css` passes the [W3C CSS Validator](https://jigsaw.w3.org/css-validator/).
