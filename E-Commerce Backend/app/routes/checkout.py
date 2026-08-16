"""Checkout routes for Stripe integration."""
import stripe
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import CartItem, Product, Order, OrderItem, StripeEvent
from app.tasks import send_order_confirmation_email

checkout_bp = Blueprint('checkout', __name__, url_prefix='/api/checkout')

# Maximum length Stripe accepts for product_data.description.
_STRIPE_DESC_MAX = 500


def _safe_stripe_image(url):
    """Return a one-element list suitable for Stripe's images field, or [].

    Stripe requires images to be absolute HTTPS URLs. Relative paths,
    http:// URLs, and localhost URLs are silently omitted so they never
    cause stripe.Session.create() to raise an InvalidRequestError.
    """
    if not url:
        return []
    if url.startswith('https://') and not url.startswith('https://localhost'):
        return [url]
    return []


@checkout_bp.route('/create-session', methods=['POST'])
@jwt_required()
def create_checkout_session():
    """Create a Stripe Checkout Session from the authenticated user's cart.

    All prices and quantities are read from the database — nothing in the
    request body influences what Stripe is told to charge.

    Returns:
        201  { "url": "https://checkout.stripe.com/...",
               "session_id": "cs_...",
               "order_id": 123 }
    """
    current_user_id = int(get_jwt_identity())

    # 1. Load cart from the DB (JWT-keyed — nothing from request body)
    cart_items = CartItem.query.filter_by(user_id=current_user_id).all()

    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    # 2. Validate every item before touching Stripe or creating the order
    for cart_item in cart_items:
        if not cart_item.product:
            return jsonify({
                'error': f'Product for cart item {cart_item.id} no longer exists',
            }), 409

        if cart_item.product.stock < cart_item.quantity:
            return jsonify({
                'error':      f'Insufficient stock for {cart_item.product.name}',
                'product_id': cart_item.product.id,
                'available':  cart_item.product.stock,
                'requested':  cart_item.quantity,
            }), 400

    # 3. Build line_items, subtotal, and OrderItem data in ONE pass.
    #    Single loop: each product accessed once, same snapshot to Stripe and DB.
    line_items      = []
    order_item_data = []
    subtotal_cents  = 0

    for cart_item in cart_items:
        product    = cart_item.product
        quantity   = cart_item.quantity
        unit_cents = product.price_cents

        subtotal_cents += unit_cents * quantity
        description = (product.description or '')[:_STRIPE_DESC_MAX]

        line_items.append({
            'price_data': {
                'currency':    'usd',
                'unit_amount': unit_cents,
                'product_data': {
                    'name':        product.name,
                    'description': description,
                    'images':      _safe_stripe_image(product.image_url),
                },
            },
            'quantity': quantity,
        })

        order_item_data.append({
            'product_id':       product.id,
            'product_name':     product.name,
            'quantity':         quantity,
            'unit_price_cents': unit_cents,
        })

    # 4. Create Order + OrderItems BEFORE calling Stripe.
    try:
        order = Order(
            user_id=current_user_id,
            status='pending',
            subtotal_cents=subtotal_cents,
        )
        db.session.add(order)
        db.session.flush()

        for data in order_item_data:
            db.session.add(OrderItem(order_id=order.id, **data))

        # 5. Call Stripe — api_key passed explicitly to avoid global mutation.
        frontend_url = current_app.config['FRONTEND_URL']
        stripe_key   = current_app.config['STRIPE_SECRET_KEY']

        stripe_session = stripe.checkout.Session.create(
            api_key=stripe_key,
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=(
                f"{frontend_url}/checkout/success"
                f"?session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{frontend_url}/checkout/cancel",
            client_reference_id=str(order.id),
            metadata={'order_id': order.id, 'user_id': current_user_id},
        )

        # 6. Link the Stripe session to the local order, then commit.
        order.stripe_session_id = stripe_session.id

        try:
            db.session.commit()
        except Exception as commit_err:
            db.session.rollback()
            current_app.logger.error(
                f'DB commit failed after Stripe session {stripe_session.id} '
                f'was created: {commit_err}. Attempting to expire the session.'
            )
            try:
                stripe.checkout.Session.expire(stripe_session.id, api_key=stripe_key)
            except Exception as expire_err:
                current_app.logger.error(
                    f'Could not expire Stripe session {stripe_session.id}: {expire_err}'
                )
            return jsonify({'error': 'Failed to save order — please try again'}), 500

        return jsonify({
            'url':        stripe_session.url,
            'session_id': stripe_session.id,
            'order_id':   order.id,
        }), 201

    except stripe.error.StripeError as e:
        db.session.rollback()
        current_app.logger.error(f'Stripe error during session creation: {e}')
        return jsonify({'error': 'Payment provider error — please try again'}), 502
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Unexpected error during checkout: {e}')
        return jsonify({'error': 'Failed to create checkout session'}), 500


# ---------------------------------------------------------------------------
# Stripe webhook
# ---------------------------------------------------------------------------

@checkout_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Receive and dispatch Stripe webhook events.

    Security
    --------
    Every request is verified against STRIPE_WEBHOOK_SECRET using the
    Stripe-Signature header before any payload data is trusted.  A missing
    or invalid signature returns 400 immediately.

    Idempotency
    -----------
    Each event is deduplicated on its Stripe event ID (evt_...).  Before
    doing any work we INSERT a StripeEvent row inside the same DB transaction
    as all side-effects.  The UNIQUE constraint on stripe_events.event_id
    makes a duplicate delivery raise IntegrityError, rolling back the
    transaction so no side-effects run twice.

    Stripe expects a 2xx quickly; slow work (email) is deferred to Celery.
    """
    payload    = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']

    if not webhook_secret:
        current_app.logger.error('STRIPE_WEBHOOK_SECRET not configured')
        return jsonify({'error': 'Webhook not configured'}), 500

    # ── 1. Verify signature before trusting the payload ────────────────────
    if not sig_header:
        current_app.logger.warning('Webhook received without Stripe-Signature header')
        return jsonify({'error': 'Missing Stripe-Signature header'}), 400

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        current_app.logger.error('Webhook: invalid JSON payload')
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        current_app.logger.error('Webhook: invalid Stripe-Signature')
        return jsonify({'error': 'Invalid signature'}), 400

    # ── 2. Dispatch to the appropriate handler ──────────────────────────────
    event_type = event['type']
    event_id   = event['id']

    try:
        if event_type == 'checkout.session.completed':
            handle_checkout_completed(event_id, event['data']['object'])
        elif event_type == 'checkout.session.expired':
            handle_checkout_expired(event_id, event['data']['object'])
        elif event_type == 'payment_intent.payment_failed':
            handle_payment_failed(event_id, event['data']['object'])
        else:
            current_app.logger.info(f'Webhook: unhandled event type {event_type!r}')
    except Exception as e:
        current_app.logger.error(f'Webhook handler error for {event_id}: {e}')
        return jsonify({'error': 'Webhook processing failed'}), 500

    return jsonify({'status': 'success'}), 200


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _record_event(event_id: str, event_type: str) -> bool:
    """Atomically claim a Stripe event_id for processing.

    Inserts a StripeEvent row inside the caller's open transaction (no
    commit here — the caller commits everything together).

    Returns True  → INSERT succeeded; proceed with side-effects.
    Returns False → UNIQUE violation; event already processed; skip.
    """
    try:
        db.session.add(StripeEvent(event_id=event_id, event_type=event_type))
        db.session.flush()   # surfaces IntegrityError immediately if duplicate
        return True
    except IntegrityError:
        db.session.rollback()
        current_app.logger.info(
            f'Webhook: duplicate event {event_id!r} ({event_type}) — skipping'
        )
        return False


def _lock_order_by_session(stripe_session_id: str):
    """SELECT ... FOR UPDATE on the Order matching stripe_session_id."""
    return db.session.execute(
        select(Order)
        .where(Order.stripe_session_id == stripe_session_id)
        .with_for_update()
    ).scalar_one_or_none()


def _lock_order_by_payment_intent(payment_intent_id: str):
    """SELECT ... FOR UPDATE on the Order matching stripe_payment_intent_id."""
    return db.session.execute(
        select(Order)
        .where(Order.stripe_payment_intent_id == payment_intent_id)
        .with_for_update()
    ).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def handle_checkout_completed(event_id: str, session: dict) -> None:
    """Mark order paid, decrement stock, clear cart, dispatch email task.

    Idempotency guarantee
    ---------------------
    Two concurrent deliveries of the same event are serialised by two
    mechanisms working together:

    1.  SELECT ... FOR UPDATE on the Order row at the very start.  One
        concurrent transaction wins the lock; the other blocks until the
        winner commits, then reads the already-paid status and returns.

    2.  _record_event() inserts a unique StripeEvent row inside this
        same transaction.  If a second delivery somehow arrives after the
        first commits, the INSERT raises IntegrityError and we return early.

    Transaction scope
    -----------------
    One commit covers: StripeEvent INSERT, Order.status = 'paid',
    every Product.stock decrement, and CartItem deletions.

    The Celery task is dispatched AFTER the commit so the worker reads
    committed data, and it is dispatched exactly once because we only
    reach the dispatch line for a successful, non-duplicate event.
    """
    stripe_session_id = session['id']
    payment_intent_id = session.get('payment_intent')

    # Lock the order row first — serialises concurrent deliveries.
    order = _lock_order_by_session(stripe_session_id)

    if not order:
        current_app.logger.error(
            f'Webhook completed: no Order for session {stripe_session_id!r}'
        )
        return

    # Fast-path for non-concurrent duplicates (order already paid).
    if order.status == 'paid':
        current_app.logger.info(
            f'Webhook: order {order.id} already paid — ignoring duplicate event'
        )
        return

    # Atomic claim: INSERT stripe_events row inside this transaction.
    if not _record_event(event_id, 'checkout.session.completed'):
        return

    try:
        order.status = 'paid'
        order.stripe_payment_intent_id = payment_intent_id

        # Lock and decrement each product row individually.
        for order_item in order.items:
            if order_item.product_id is None:
                continue   # product deleted; stock already gone

            product = db.session.execute(
                select(Product)
                .where(Product.id == order_item.product_id)
                .with_for_update()
            ).scalar_one_or_none()

            if product is None:
                current_app.logger.warning(
                    f'Webhook: product {order_item.product_id} missing '
                    f'for order {order.id} — skipping stock decrement'
                )
                continue

            if product.stock >= order_item.quantity:
                product.stock -= order_item.quantity
            else:
                current_app.logger.warning(
                    f'Webhook: stock underflow for product {product.id} '
                    f'(have {product.stock}, need {order_item.quantity}) '
                    f'— clamping to 0'
                )
                product.stock = 0

        # Clear cart atomically with everything else.
        CartItem.query.filter_by(user_id=order.user_id).delete()

        # Single commit covers StripeEvent + Order + all Products + CartItems.
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f'Webhook: error processing completed event for order {order.id}'
        )
        raise

    # Dispatch email AFTER commit — worker sees committed data, fires exactly once.
    send_order_confirmation_email.apply_async(args=[order.id], countdown=2)
    current_app.logger.info(
        f'Webhook: order {order.id} marked paid, confirmation email queued'
    )


def handle_checkout_expired(event_id: str, session: dict) -> None:
    """Mark order failed when the Stripe Checkout Session expires."""
    stripe_session_id = session['id']

    order = _lock_order_by_session(stripe_session_id)

    if not order:
        current_app.logger.error(
            f'Webhook expired: no Order for session {stripe_session_id!r}'
        )
        return

    if order.status in ('failed', 'paid'):
        return   # terminal state — nothing to do

    if not _record_event(event_id, 'checkout.session.expired'):
        return

    try:
        order.status = 'failed'
        db.session.commit()
        current_app.logger.info(
            f'Webhook: order {order.id} marked failed (session expired)'
        )
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f'Webhook: error marking order {order.id} failed (session expired)'
        )
        raise


def handle_payment_failed(event_id: str, payment_intent: dict) -> None:
    """Mark order failed when the PaymentIntent fails."""
    payment_intent_id = payment_intent['id']

    order = _lock_order_by_payment_intent(payment_intent_id)

    if not order:
        # payment_intent may not be linked yet if the order was never created.
        current_app.logger.warning(
            f'Webhook payment_failed: no Order for payment_intent {payment_intent_id!r}'
        )
        return

    if order.status in ('failed', 'paid'):
        return

    if not _record_event(event_id, 'payment_intent.payment_failed'):
        return

    try:
        order.status = 'failed'
        db.session.commit()
        current_app.logger.info(
            f'Webhook: order {order.id} marked failed (payment_intent failed)'
        )
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f'Webhook: error marking order {order.id} failed (payment_intent failed)'
        )
        raise


# ---------------------------------------------------------------------------
# Order history
# ---------------------------------------------------------------------------

@checkout_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_user_orders():
    """Return all orders for the current user."""
    current_user_id = int(get_jwt_identity())

    orders = (
        Order.query
        .filter_by(user_id=current_user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return jsonify({
        'orders': [o.to_dict(include_items=True) for o in orders],
    }), 200


@checkout_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Return a single order, verifying it belongs to the current user."""
    current_user_id = int(get_jwt_identity())

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    if order.user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    return jsonify({'order': order.to_dict(include_items=True)}), 200
