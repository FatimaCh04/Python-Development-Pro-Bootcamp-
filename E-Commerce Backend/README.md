# FIELD & FORM — E-Commerce Platform

A full-stack e-commerce store featuring a custom-designed, animated storefront frontend
and a Flask REST API backend with Stripe-powered payments.

---

## Features

- **Product inventory** — products with name, price, stock, and category, served via a
  REST API and rendered dynamically with live category filtering
- **User authentication** — JWT-based signup and login, with protected routes for cart
  and checkout actions
- **Shopping cart** — add, remove, and adjust item quantities with a live-updating subtotal
- **Stripe Checkout** — generates a secure Stripe-hosted checkout session and redirects
  the user to complete payment
- **Stripe webhooks** — listens for payment success events, confirms the order, and
  decrements product stock automatically and atomically
- **Email notifications** — sends order confirmation emails asynchronously via Celery
  background workers backed by Redis

---

## Screenshots

### Storefront home — hero, trust stats, marquee
<img width="1196" height="623" alt="E 1" src="https://github.com/user-attachments/assets/a53afa53-6867-4268-905d-f500225982bd" />


### Category filtering
<img width="1360" height="653" alt="E 5" src="https://github.com/user-attachments/assets/0a353636-f64b-49c7-af98-453d4a7cb238" />


### Product grid
<img width="1205" height="657" alt="E 2" src="https://github.com/user-attachments/assets/2b3ddc6e-672d-44ac-a63c-9eb55f20ab90" />


### Add to cart — toast confirmation + live cart badge
<img width="1306" height="653" alt="E 3" src="https://github.com/user-attachments/assets/9b9daf3f-ade0-404f-bb72-0e2d691dabef" />


### Cart drawer — line items, SKU, quantity controls, subtotal
<img width="1302" height="645" alt="E 4" src="https://github.com/user-attachments/assets/70417c23-8560-40a1-bd6a-f01bc2f12c8f" />

## Tech Stack

**Backend:** Flask, SQLAlchemy, Flask-JWT-Extended, Stripe API, Celery, Redis, Flask-Mail
**Frontend:** HTML5, custom CSS design system (no framework), vanilla JavaScript

---

## Architecture

The frontend is a fully custom animated storefront (product grid, cart drawer, auth
modal, checkout flow) that communicates with the Flask backend over a REST API. Orders
are created locally before redirecting to Stripe, and confirmed asynchronously once
Stripe's webhook notifies the backend of successful payment — ensuring stock is only
decremented once payment is verified. Order confirmation emails are handed off to a
Celery task queue so checkout stays fast.

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
├── static/
├── templates/
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

## Test Credentials (Stripe test mode)

| Field | Value |
|---|---|
| Card number | `4242 4242 4242 4242` |
| Expiry | Any future date |
| CVC | Any 3 digits |
| ZIP | Any 5 digits |
