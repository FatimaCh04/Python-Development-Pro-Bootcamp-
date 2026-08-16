# FIELD & FORM — E-Commerce Platform

A full-stack e-commerce store: an animated storefront frontend (HTML/CSS/JS) backed by a
Flask + SQLAlchemy + Stripe + Celery + Redis API.

Live locally at `http://127.0.0.1:5000`

---

## Screenshots

### Storefront home — hero, trust stats, marquee
![Hero and shop section](assets/01-hero-shop.png)

### Category filtering (dynamic — pulled from backend `/api/products`)
![Category filter](assets/02-category-filter.png)

### Product grid
![Product grid](assets/03-product-grid.png)

### Add to cart — toast confirmation + live cart badge
![Add to cart toast](assets/04-add-to-cart-toast.png)

### Cart drawer — line items, SKU, quantity controls, subtotal
![Cart drawer](assets/05-cart-drawer.png)

### Cart quantity update — subtotal recalculates live
![Cart quantity update](assets/06-cart-qty-update.png)

---

## Tech Stack

**Frontend:** HTML5, CSS3 (custom design system, no framework), vanilla JavaScript
**Backend:** Flask, SQLAlchemy, Flask-JWT-Extended, Stripe API, Celery, Redis, Flask-Mail

---

## Feature Status

| # | Requirement | Status | Notes |
|---|---|---|---|
| 1 | Product inventory (name, price, stock) | ✅ Working | Products load dynamically from `/api/products`, categories filter correctly |
| 2 | User authentication (JWT) | ⚠️ Partially verified | Login/signup UI wired; token issuance and protected-route validation not yet confirmed end-to-end |
| 3 | Cart system (add/remove items) | ✅ Working | Add, remove, quantity +/-, live subtotal all confirmed |
| 4 | Stripe checkout session generation | ❌ Not working | Checkout button does not currently redirect to a real Stripe Checkout page |
| 5 | Stripe webhook (confirm order + decrease stock) | ⚠️ Blocked | Cannot be tested until #4 is fixed — no payment is being initiated |
| 6 | Email order confirmation (SMTP) | ❌ Not working | No email is sent after order events; Celery worker / SMTP config needs debugging |

---

## Project Structure

```
field-and-form-ecommerce/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models.py
│   ├── seed.py
│   ├── tasks.py
│   └── routes/
├── migrations/
├── static/              # (frontend CSS/JS once merged into Flask)
├── templates/            # (index.html once merged into Flask)
├── celery_worker.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── run.py
```

---

## Setup

```bash
# 1. Clone and enter the project
cd field-and-form-ecommerce

# 2. Create virtual environment and install dependencies
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 3. Copy environment file and fill in real values
cp .env.example .env
# Set: DATABASE_URL, JWT_SECRET_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
#      REDIS_URL, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FRONTEND_URL

# 4. Run database migrations and seed products
flask db upgrade
python -m app.seed

# 5. Start Redis (required for Celery)
docker run -p 6379:6379 redis

# 6. Start the Celery worker (separate terminal)
celery -A celery_worker worker --loglevel=info

# 7. In a separate terminal, forward Stripe webhooks for local testing
stripe listen --forward-to localhost:5000/api/checkout/webhook

# 8. Start the Flask server
python run.py
```

Open `http://127.0.0.1:5000` in a browser.

---

## Known Issues / Next Steps

1. **Checkout button doesn't reach Stripe.** Verify the frontend actually calls
   `POST /api/checkout/create-session` (check Network tab), that the route creates a real
   `stripe.checkout.Session`, and that the frontend redirects via
   `window.location.href = data.url`.
2. **No confirmation email sent.** Confirm the Celery worker is running and connected to
   Redis, that `send_order_confirmation_email` is actually queued from the webhook handler,
   and that SMTP credentials in `.env` are valid (test with a direct `.delay()` call from a
   Flask shell to isolate whether the issue is Celery or SMTP).
3. Once #1 is fixed, re-test the full flow: add to cart → checkout → pay with Stripe test
   card `4242 4242 4242 4242` → confirm webhook marks the order `paid`, decrements stock,
   and triggers the confirmation email.

---

## Test Credentials (Stripe test mode)

| Field | Value |
|---|---|
| Card number | `4242 4242 4242 4242` |
| Expiry | Any future date |
| CVC | Any 3 digits |
| ZIP | Any 5 digits |
