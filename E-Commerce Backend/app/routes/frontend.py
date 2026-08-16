"""Frontend routes — serves the static HTML storefront."""
from flask import Blueprint, render_template, request

frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/')
def index():
    """Serve the Field & Form storefront SPA."""
    return render_template('index.html')


@frontend_bp.route('/checkout/success')
def checkout_success():
    """Landing page after a successful Stripe payment.

    Stripe appends ?session_id=cs_... — we pass it to the template so
    it can display an order-confirmation message or poll the order status.
    """
    session_id = request.args.get('session_id', '')
    return render_template('checkout_success.html', session_id=session_id)


@frontend_bp.route('/checkout/cancel')
def checkout_cancel():
    """Landing page when the user closes the Stripe checkout page."""
    return render_template('checkout_cancel.html')
