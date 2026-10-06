/* HBnB front-end: login, places list, place details and reviews. */

const API_URL = 'http://127.0.0.1:5000/api/v1';
const TOKEN_COOKIE = 'token';
const TOKEN_MAX_AGE = 3600; // seconds, matches the API token lifetime

/* ---------- Cookies and authentication ---------- */

function getCookie(name) {
  const prefix = `${name}=`;
  const cookie = document.cookie
    .split('; ')
    .find((row) => row.startsWith(prefix));
  return cookie ? decodeURIComponent(cookie.substring(prefix.length)) : null;
}

function setTokenCookie(token) {
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(token)}; path=/; max-age=${TOKEN_MAX_AGE}; SameSite=Lax`;
}

function deleteTokenCookie() {
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Show the login link to visitors and the logout button to logged-in users
function updateAuthLinks(token) {
  const loginLink = document.getElementById('login-link');
  const logoutButton = document.getElementById('logout-button');

  if (loginLink) {
    loginLink.style.display = token ? 'none' : 'inline-block';
  }
  if (logoutButton) {
    logoutButton.hidden = !token;
    logoutButton.addEventListener('click', () => {
      deleteTokenCookie();
      window.location.href = 'index.html';
    });
  }
}

function getPlaceIdFromURL() {
  return new URLSearchParams(window.location.search).get('id');
}

/* ---------- Small DOM helpers ---------- */

// textContent (never innerHTML) is used for API data to prevent HTML injection
function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) {
    element.className = className;
  }
  if (text !== undefined) {
    element.textContent = text;
  }
  return element;
}

function showStatus(container, message) {
  container.replaceChildren(createElement('p', 'status-message', message));
}

function formatPrice(price) {
  return `$${Number(price).toFixed(Number.isInteger(price) ? 0 : 2)}`;
}

/* ---------- Login (login.html) ---------- */

async function loginUser(email, password) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json().catch(() => ({}));
  return { response, data };
}

function setupLoginForm() {
  const loginForm = document.getElementById('login-form');
  if (!loginForm) {
    return;
  }
  const errorMessage = document.getElementById('login-error');

  loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorMessage.hidden = true;

    const email = loginForm.email.value.trim();
    const password = loginForm.password.value;

    try {
      const { response, data } = await loginUser(email, password);
      if (response.ok) {
        setTokenCookie(data.access_token);
        window.location.href = 'index.html';
        return;
      }
      errorMessage.textContent = `Login failed: ${data.error || response.statusText}`;
    } catch (error) {
      errorMessage.textContent = 'Login failed: cannot reach the server.';
    }
    errorMessage.hidden = false;
  });
}

/* ---------- Places list (index.html) ---------- */

async function fetchPlaces(token) {
  const placesList = document.getElementById('places-list');
  try {
    const response = await fetch(`${API_URL}/places/`, {
      headers: authHeaders(token)
    });
    if (!response.ok) {
      throw new Error(response.statusText);
    }
    displayPlaces(await response.json());
  } catch (error) {
    showStatus(placesList, 'Could not load places. Please try again later.');
  }
}

function displayPlaces(places) {
  const placesList = document.getElementById('places-list');
  const heading = placesList.querySelector('h2');
  placesList.replaceChildren(heading);

  if (places.length === 0) {
    placesList.append(createElement('p', 'status-message', 'No places yet.'));
    return;
  }

  places.forEach((place) => {
    const card = createElement('article', 'place-card');
    card.dataset.price = place.price;

    const price = createElement('p', 'place-price');
    price.append(createElement('strong', '', formatPrice(place.price)), ' per night');

    const button = createElement('a', 'details-button', 'View Details');
    button.href = `place.html?id=${encodeURIComponent(place.id)}`;

    card.append(createElement('h3', '', place.title), price, button);
    placesList.append(card);
  });

  filterPlaces();
}

// Show only the places whose price is at most the selected maximum
function filterPlaces() {
  const priceFilter = document.getElementById('price-filter');
  const placesList = document.getElementById('places-list');
  const maxPrice = priceFilter.value === 'All' ? Infinity : Number(priceFilter.value);
  let visible = 0;

  placesList.querySelectorAll('.place-card').forEach((card) => {
    const show = Number(card.dataset.price) <= maxPrice;
    card.style.display = show ? '' : 'none';
    if (show) {
      visible += 1;
    }
  });

  let emptyMessage = placesList.querySelector('.filter-empty');
  if (!emptyMessage) {
    emptyMessage = createElement('p', 'status-message filter-empty');
    placesList.append(emptyMessage);
  }
  emptyMessage.textContent = `No places at ${formatPrice(maxPrice)} or less per night.`;
  emptyMessage.hidden = visible > 0 || placesList.querySelectorAll('.place-card').length === 0;
}

function setupIndexPage(token) {
  const placesList = document.getElementById('places-list');
  if (!placesList) {
    return;
  }
  document.getElementById('price-filter').addEventListener('change', filterPlaces);
  fetchPlaces(token);
}

/* ---------- Place details (place.html) ---------- */

async function fetchPlaceDetails(token, placeId) {
  const details = document.getElementById('place-details');
  try {
    const response = await fetch(`${API_URL}/places/${encodeURIComponent(placeId)}`, {
      headers: authHeaders(token)
    });
    if (response.status === 404) {
      showStatus(details, 'Place not found.');
      return null;
    }
    if (!response.ok) {
      throw new Error(response.statusText);
    }
    const place = await response.json();
    displayPlaceDetails(place);
    return place;
  } catch (error) {
    showStatus(details, 'Could not load this place. Please try again later.');
    return null;
  }
}

function infoLine(label, value) {
  const line = createElement('p');
  line.append(createElement('span', 'label', `${label}: `), value);
  return line;
}

function displayPlaceDetails(place) {
  const details = document.getElementById('place-details');
  const info = createElement('div', 'place-info');
  const amenities = place.amenities.map((amenity) => amenity.name).join(', ');

  info.append(
    infoLine('Host', `${place.owner.first_name} ${place.owner.last_name}`),
    infoLine('Price per night', formatPrice(place.price)),
    infoLine('Description', place.description || 'No description.'),
    infoLine('Amenities', amenities || 'None listed.')
  );
  details.replaceChildren(createElement('h1', 'place-title', place.title), info);
  document.title = `HBnB - ${place.title}`;

  displayReviews(place.reviews);
}

function displayReviews(reviews) {
  const reviewsList = document.getElementById('reviews-list');
  if (reviews.length === 0) {
    showStatus(reviewsList, 'No reviews yet.');
    return;
  }

  reviewsList.replaceChildren(...reviews.map((review) => {
    const card = createElement('article', 'review-card');
    const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
    const rating = createElement('p', 'review-rating', stars);
    rating.title = `Rating: ${review.rating} out of 5`;
    card.append(
      createElement('p', 'review-user', review.user_name),
      rating,
      createElement('p', 'review-text', review.text)
    );
    return card;
  }));
}

function setupPlacePage(token) {
  const details = document.getElementById('place-details');
  if (!details) {
    return;
  }
  const placeId = getPlaceIdFromURL();
  if (!placeId) {
    showStatus(details, 'No place selected.');
    return;
  }

  // The review form is only available to logged-in users
  document.getElementById('add-review').hidden = !token;
  fetchPlaceDetails(token, placeId);
  setupReviewForm(token, placeId, () => fetchPlaceDetails(token, placeId));
}

/* ---------- Reviews (place.html and add_review.html) ---------- */

async function submitReview(token, placeId, reviewText, rating) {
  return fetch(`${API_URL}/reviews/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    body: JSON.stringify({ text: reviewText, rating, place_id: placeId })
  });
}

function showFormMessage(message, type) {
  const formMessage = document.getElementById('form-message');
  formMessage.textContent = message;
  formMessage.className = `form-message ${type}`;
  formMessage.hidden = false;
}

function setupReviewForm(token, placeId, onSuccess) {
  const reviewForm = document.getElementById('review-form');
  if (!reviewForm || !token) {
    return;
  }

  reviewForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const reviewText = reviewForm.text.value.trim();
    const rating = Number(reviewForm.rating.value);

    try {
      const response = await submitReview(token, placeId, reviewText, rating);
      if (response.ok) {
        showFormMessage('Review submitted successfully!', 'success');
        reviewForm.reset();
        if (onSuccess) {
          onSuccess();
        }
        return;
      }
      if (response.status === 401 || response.status === 422) {
        // Missing, expired or invalid token
        deleteTokenCookie();
        showFormMessage('Your session has expired. Please log in again.', 'error');
        return;
      }
      const data = await response.json().catch(() => ({}));
      showFormMessage(`Failed to submit review: ${data.error || response.statusText}`, 'error');
    } catch (error) {
      showFormMessage('Failed to submit review: cannot reach the server.', 'error');
    }
  });
}

// add_review.html: logged-in users only
function checkAuthentication() {
  const token = getCookie(TOKEN_COOKIE);
  if (!token) {
    window.location.href = 'index.html';
  }
  return token;
}

async function setupAddReviewPage() {
  const placeName = document.getElementById('place-name');
  if (!placeName) {
    return;
  }
  const token = checkAuthentication();
  if (!token) {
    return;
  }
  const placeId = getPlaceIdFromURL();
  if (!placeId) {
    window.location.href = 'index.html';
    return;
  }

  setupReviewForm(token, placeId);
  try {
    const response = await fetch(`${API_URL}/places/${encodeURIComponent(placeId)}`);
    if (!response.ok) {
      throw new Error(response.statusText);
    }
    const place = await response.json();
    placeName.textContent = place.title;
    placeName.href = `place.html?id=${encodeURIComponent(placeId)}`;
  } catch (error) {
    placeName.textContent = 'unknown place';
  }
}

/* ---------- Start ---------- */

document.addEventListener('DOMContentLoaded', () => {
  const token = getCookie(TOKEN_COOKIE);
  updateAuthLinks(token);
  setupLoginForm();
  setupIndexPage(token);
  setupPlacePage(token);
  setupAddReviewPage();
});
