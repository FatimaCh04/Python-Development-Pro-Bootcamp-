from datetime import datetime, timezone
from app.extensions import db
import bcrypt


def _utcnow():
    """Return current UTC time.  Using timezone-aware form avoids the
    Python 3.12 deprecation warning on datetime.utcnow()."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(db.Model):
    """Registered customer account."""
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime(timezone=True), default=_utcnow, nullable=False)

    # cascade='all, delete-orphan' handles ORM-level deletes.
    # ondelete='CASCADE' on the FK makes the DB enforce the same rule
    # when rows are removed via raw SQL / migrations / admin tools.
    cart_items = db.relationship(
        'CartItem', backref='user',
        lazy='select', cascade='all, delete-orphan',
        passive_deletes=True,
    )
    orders = db.relationship(
        'Order', backref='user',
        lazy='select', cascade='all, delete-orphan',
        passive_deletes=True,
    )

    # ------------------------------------------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8'),
        )

    def to_dict(self) -> dict:
        """Serialise to dict.  password_hash is intentionally excluded."""
        return {
            'id':         self.id,
            'name':       self.name,
            'email':      self.email,
            'created_at': self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class Product(db.Model):
    """Inventory item."""
    __tablename__ = 'products'

    id          = db.Column(db.Integer, primary_key=True)
    sku         = db.Column(db.String(50),  unique=True, nullable=False, index=True)
    name        = db.Column(db.String(200), nullable=False)
    category    = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    # Price is stored in cents (integer) to avoid floating-point rounding.
    price_cents = db.Column(db.Integer, nullable=False)
    stock       = db.Column(db.Integer, nullable=False, default=0)
    image_url   = db.Column(db.String(500))
    created_at  = db.Column(db.DateTime(timezone=True), default=_utcnow, nullable=False)

    # No cascade here: deleting a Product that has order history must be
    # blocked at the application layer (or use SET NULL on order_items.product_id).
    cart_items  = db.relationship('CartItem',  backref='product', lazy='select')
    order_items = db.relationship('OrderItem', backref='product', lazy='select')

    def to_dict(self) -> dict:
        return {
            'id':          self.id,
            'sku':         self.sku,
            'name':        self.name,
            'category':    self.category,
            'description': self.description,
            'price_cents': self.price_cents,
            'price':       self.price_cents / 100,   # convenience field for frontend
            'stock':       self.stock,
            'image_url':   self.image_url,
            'created_at':  self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class Order(db.Model):
    """Purchase record linked to a Stripe Checkout Session."""
    __tablename__ = 'orders'

    id                       = db.Column(db.Integer, primary_key=True)
    # DB-level CASCADE: deleting a User removes their orders automatically.
    user_id                  = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    # Allowed values: pending | paid | failed | refunded
    status                   = db.Column(db.String(20), nullable=False, default='pending', index=True)
    stripe_session_id        = db.Column(db.String(255), unique=True, index=True)
    stripe_payment_intent_id = db.Column(db.String(255), index=True)
    # Total stored in cents – computed from OrderItem.unit_price_cents at
    # checkout time so it never changes after payment.
    subtotal_cents           = db.Column(db.Integer, nullable=False)
    created_at               = db.Column(db.DateTime(timezone=True), default=_utcnow, nullable=False)

    items = db.relationship(
        'OrderItem', backref='order',
        lazy='select', cascade='all, delete-orphan',
        passive_deletes=True,
    )

    def to_dict(self, include_items: bool = False) -> dict:
        d = {
            'id':                       self.id,
            'user_id':                  self.user_id,
            'status':                   self.status,
            'subtotal_cents':           self.subtotal_cents,
            'subtotal':                 self.subtotal_cents / 100,
            'created_at':               self.created_at.isoformat(),
            # Stripe IDs are internal; expose only what the frontend needs.
            # They are included here for order-status pages / receipts but
            # should be omitted in any public-facing list endpoint.
            'stripe_session_id':        self.stripe_session_id,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
        }
        if include_items:
            d['items'] = [item.to_dict() for item in self.items]
        return d


# ---------------------------------------------------------------------------
# OrderItem
# ---------------------------------------------------------------------------

class OrderItem(db.Model):
    """Line item snapshot.

    Both price and product name are captured at the moment of purchase so
    that historical orders remain accurate even if the product is later
    renamed, repriced, or deleted.
    """
    __tablename__ = 'order_items'

    id              = db.Column(db.Integer, primary_key=True)
    # DB-level CASCADE: removing an Order cascades to its items.
    order_id        = db.Column(
        db.Integer,
        db.ForeignKey('orders.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    # SET NULL instead of CASCADE: deleting a Product does not delete
    # historical order records — we still have the name/price snapshot.
    product_id      = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='SET NULL'),
        nullable=True,   # must be nullable to allow SET NULL
    )
    # --- purchase-time snapshots (never updated after order is created) ---
    product_name    = db.Column(db.String(200), nullable=False)   # NEW
    unit_price_cents = db.Column(db.Integer,    nullable=False)
    # ---------------------------------------------------------------------
    quantity        = db.Column(db.Integer, nullable=False)

    def to_dict(self) -> dict:
        return {
            'id':               self.id,
            'order_id':         self.order_id,
            'product_id':       self.product_id,
            # Use the snapshot – never the live Product.name
            'product_name':     self.product_name,
            'quantity':         self.quantity,
            'unit_price_cents': self.unit_price_cents,
            'unit_price':       self.unit_price_cents / 100,
            'line_total_cents': self.quantity * self.unit_price_cents,
            'line_total':       (self.quantity * self.unit_price_cents) / 100,
        }


# ---------------------------------------------------------------------------
# StripeEvent  — webhook deduplication log
# ---------------------------------------------------------------------------

class StripeEvent(db.Model):
    """Records every Stripe webhook event that has been fully processed.

    Purpose
    -------
    Stripe guarantees *at-least-once* delivery: it will retry a webhook
    until it receives a 2xx response.  Without deduplication, a network
    hiccup that causes our 200 to be lost makes Stripe retry, and we
    process the same event twice — decrementing stock twice and sending
    two confirmation emails.

    Idempotency strategy
    --------------------
    Before doing any work for a webhook event, we attempt to INSERT a row
    with the Stripe event ID (``evt_...``).  Because ``event_id`` has a
    UNIQUE constraint, a duplicate delivery will raise an IntegrityError,
    which we catch and convert to an early 200 return.  The INSERT and all
    side-effects (order status, stock, cart clear) happen inside the same
    DB transaction, so either everything commits together or nothing does.

    Fields
    ------
    event_id   : Stripe's globally unique event identifier (``evt_...``)
    event_type : e.g. ``checkout.session.completed``
    processed_at: when the event was successfully processed
    """
    __tablename__ = 'stripe_events'

    id           = db.Column(db.Integer, primary_key=True)
    event_id     = db.Column(db.String(255), unique=True, nullable=False, index=True)
    event_type   = db.Column(db.String(100), nullable=False)
    processed_at = db.Column(db.DateTime(timezone=True), default=_utcnow, nullable=False)


# ---------------------------------------------------------------------------
# CartItem
# ---------------------------------------------------------------------------

class CartItem(db.Model):
    """Server-side cart entry for a logged-in user."""
    __tablename__ = 'cart_items'

    id         = db.Column(db.Integer, primary_key=True)
    # DB-level CASCADE: removing a User removes their cart.
    user_id    = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    # RESTRICT: a Product with active cart entries cannot be deleted
    # without first clearing those carts (prevents silent data loss).
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='RESTRICT'),
        nullable=False,
    )
    quantity   = db.Column(db.Integer, nullable=False, default=1)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_user_product_cart'),
    )

    def to_dict(self) -> dict:
        return {
            'id':              self.id,
            'user_id':         self.user_id,
            'product_id':      self.product_id,
            'product':         self.product.to_dict() if self.product else None,
            'quantity':        self.quantity,
            'line_total_cents': self.quantity * self.product.price_cents if self.product else 0,
            'line_total':      (self.quantity * self.product.price_cents / 100) if self.product else 0,
        }
