"""Celery tasks for asynchronous operations."""
from markupsafe import Markup, escape
from app.extensions import celery, mail, db
from app.models import Order, User
from flask_mail import Message
from flask import current_app, render_template_string
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError

logger = get_task_logger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id):
    """Send an HTML order confirmation email to the customer.

    Uses purchase-time snapshots (product_name, unit_price_cents) stored on
    OrderItem — never live Product data — so the email is accurate even if a
    product is later renamed or deleted.

    Retry behaviour
    ---------------
    On any SMTP or rendering failure the task retries up to 3 times with
    exponential backoff: 60 s → 120 s → 240 s.

    MaxRetriesExceededError is caught separately so it does not re-enter
    the retry loop, logs the final failure, and returns an error dict
    instead of raising, which prevents Celery from marking the task as
    permanently failed with an unhandled exception.
    """
    try:
        # ── Fetch data ───────────────────────────────────────────────────────
        order = db.session.get(Order, order_id)

        if not order:
            logger.error(f'send_order_confirmation_email: order {order_id} not found')
            return {'status': 'error', 'message': 'Order not found'}

        if order.status != 'paid':
            logger.warning(
                f'send_order_confirmation_email: order {order_id} '
                f'has status {order.status!r} — skipping'
            )
            return {'status': 'skipped', 'message': 'Order not paid'}

        user = db.session.get(User, order.user_id)

        if not user:
            logger.error(
                f'send_order_confirmation_email: user {order.user_id} '
                f'not found for order {order_id}'
            )
            return {'status': 'error', 'message': 'User not found'}

        # ── Build item list from purchase-time snapshots ─────────────────────
        order_items = [
            {
                'name':       item.product_name,            # snapshot
                'quantity':   item.quantity,
                'unit_price': item.unit_price_cents / 100,
                'line_total': (item.quantity * item.unit_price_cents) / 100,
            }
            for item in order.items
        ]

        # ── Render HTML body ─────────────────────────────────────────────────
        html_body = render_email_template(
            user_name=user.name,
            order_id=order.id,
            order_items=order_items,
            subtotal=order.subtotal_cents / 100,
            order_date=order.created_at.strftime('%B %d, %Y at %I:%M %p'),
        )

        # ── Build and send the message ───────────────────────────────────────
        msg = Message(
            subject=f'Order Confirmation — Field & Form (Order #{order.id})',
            recipients=[user.email],
            html=html_body,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
        )

        if current_app.config.get('MAIL_SUPPRESS_SEND'):
            logger.info(
                f'[EMAIL SUPPRESSED — SMTP not configured] '
                f'Would send order #{order_id} confirmation to {user.email}'
            )
            print(
                f'\n📧  Order #{order_id} confirmation'
                f' (SMTP not configured — console only)\n'
                f'    To      : {user.email}\n'
                f'    Subject : Order Confirmation — Field & Form (Order #{order.id})\n'
            )
        else:
            mail.send(msg)
            logger.info(
                f'Order #{order_id} confirmation sent to {user.email}'
            )

        return {
            'status':   'success',
            'message':  f'Email sent to {user.email}',
            'order_id': order_id,
        }

    except MaxRetriesExceededError:
        # All retries exhausted — log and return gracefully so Celery does
        # not treat this as an unhandled exception and mark the task FAILED
        # with a traceback in the result backend.
        logger.error(
            f'send_order_confirmation_email: max retries exceeded '
            f'for order {order_id}'
        )
        return {
            'status':   'failed',
            'message':  'Max retries exceeded',
            'order_id': order_id,
        }

    except Exception as exc:
        logger.error(
            f'send_order_confirmation_email: error for order {order_id}: {exc}'
        )
        # Retry with exponential backoff: attempt 0→60 s, 1→120 s, 2→240 s.
        # self.retry() raises celery.exceptions.Retry (a BaseException subclass)
        # which propagates out of this except block and is caught by Celery
        # to schedule the next attempt.
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# ---------------------------------------------------------------------------
# Email template
# ---------------------------------------------------------------------------

def render_email_template(
    user_name: str,
    order_id: int,
    order_items: list,
    subtotal: float,
    order_date: str,
) -> str:
    """Render the order confirmation HTML email.

    Security
    --------
    All user-supplied string values (user_name, product names) are passed
    through markupsafe.escape() before being handed to render_template_string.
    This prevents Server-Side Template Injection: a user who registered with
    the name ``{{ 7*7 }}`` will see the literal string, not ``49``.

    render_template_string does NOT auto-escape by default, so escaping must
    be done explicitly here.
    """
    # Escape every user-controlled string value.
    safe_user_name = escape(user_name)
    safe_order_date = escape(order_date)   # from DB but sanitise defensively

    safe_items = [
        {
            'name':       escape(item['name']),
            'quantity':   item['quantity'],           # integer — safe
            'unit_price': item['unit_price'],         # float   — safe
            'line_total': item['line_total'],         # float   — safe
        }
        for item in order_items
    ]

    template = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Order Confirmation</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                   'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6; color: #333; max-width: 600px;
      margin: 0 auto; padding: 20px; background-color: #f5f5f5;
    }
    .container { background: #fff; padding: 40px; border-radius: 8px;
                 box-shadow: 0 2px 4px rgba(0,0,0,.1); }
    .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px;
              border-bottom: 2px solid #2c5f2d; }
    .header h1 { color: #2c5f2d; margin: 0; font-size: 28px; }
    .order-info { background: #f9f9f9; padding: 15px; border-radius: 4px;
                  margin-bottom: 30px; }
    .order-info p { margin: 5px 0; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th { background: #2c5f2d; color: #fff; padding: 12px; text-align: left; }
    td { padding: 12px; border-bottom: 1px solid #ddd; }
    tr:last-child td { border-bottom: none; }
    .total { font-weight: bold; font-size: 18px; text-align: right;
             padding: 20px 0; border-top: 2px solid #2c5f2d; }
    .footer { text-align: center; margin-top: 30px; padding-top: 20px;
              border-top: 1px solid #ddd; color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Field &amp; Form</h1>
      <p>Thank you for your order!</p>
    </div>

    <p>Hi {{ user_name }},</p>
    <p>Your order has been confirmed and is being processed.
       We'll send a shipping notification as soon as your items are on their way.</p>

    <div class="order-info">
      <p><strong>Order Number:</strong> #{{ order_id }}</p>
      <p><strong>Order Date:</strong> {{ order_date }}</p>
    </div>

    <h2>Order Details</h2>
    <table>
      <thead>
        <tr>
          <th>Item</th><th>Qty</th><th>Unit Price</th><th>Line Total</th>
        </tr>
      </thead>
      <tbody>
        {% for item in order_items %}
        <tr>
          <td>{{ item.name }}</td>
          <td>{{ item.quantity }}</td>
          <td>${{ "%.2f"|format(item.unit_price) }}</td>
          <td>${{ "%.2f"|format(item.line_total) }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>

    <div class="total">
      Order Total: ${{ "%.2f"|format(subtotal) }}
    </div>

    <div class="footer">
      <p>Questions? <a href="mailto:support@fieldandform.com">support@fieldandform.com</a></p>
      <p>&copy; 2024 Field &amp; Form. All rights reserved.</p>
    </div>
  </div>
</body>
</html>"""

    return render_template_string(
        template,
        user_name=safe_user_name,
        order_id=order_id,        # integer
        order_date=safe_order_date,
        order_items=safe_items,
        subtotal=subtotal,        # float
    )
