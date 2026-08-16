"""Cart routes — server-side cart for authenticated users."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import CartItem, Product
from sqlalchemy.exc import IntegrityError

cart_bp = Blueprint('cart', __name__, url_prefix='/api/cart')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_int_field(value, field_name: str):
    """Return (int_value, None) or (None, error_response).

    Rejects:
      - missing / None values
      - floats that are not whole numbers (1.9, 2.7 …)
      - strings
      - non-numeric types
    Accepts:
      - Python int (from JSON integer literal)
      - Python float that IS a whole number (1.0, 2.0) for leniency
    """
    if value is None:
        return None, (jsonify({'error': f'{field_name} is required'}), 400)
    # JSON integers arrive as int; floats arrive as float.
    # Reject floats that are not whole numbers.
    if isinstance(value, float):
        if not value.is_integer():
            return None, (jsonify({'error': f'{field_name} must be a whole number'}), 400)
        value = int(value)
    if not isinstance(value, int) or isinstance(value, bool):
        return None, (jsonify({'error': f'{field_name} must be an integer'}), 400)
    return value, None


def _owned_cart_item(item_id: int, user_id: int):
    """Fetch a CartItem that belongs to *user_id*.

    Returns (cart_item, None) on success.
    Returns (None, error_response) when the item does not exist OR belongs
    to a different user — both cases return 404 so the caller cannot infer
    whether a foreign item_id exists (IDOR prevention).
    """
    item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if item is None:
        return None, (jsonify({'error': 'Cart item not found'}), 404)
    return item, None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@cart_bp.route('', methods=['GET'])
@jwt_required()
def get_cart():
    """Return the current user's cart with per-line and overall totals."""
    current_user_id = int(get_jwt_identity())

    cart_items = CartItem.query.filter_by(user_id=current_user_id).all()

    total_items    = sum(item.quantity for item in cart_items)
    subtotal_cents = sum(
        item.quantity * item.product.price_cents
        for item in cart_items
        if item.product  # guard: product could be None if deleted
    )

    return jsonify({
        'cart_items':      [item.to_dict() for item in cart_items],
        'total_items':     total_items,
        'subtotal_cents':  subtotal_cents,
        'subtotal':        subtotal_cents / 100,
    }), 200


@cart_bp.route('/items', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Add a product to the cart, or increment its quantity if already present.

    Body: { "product_id": <int>, "quantity": <int, ≥1> }
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # --- validate product_id -------------------------------------------------
    product_id, err = _parse_int_field(data.get('product_id'), 'product_id')
    if err:
        return err
    if product_id < 1:
        return jsonify({'error': 'product_id must be a positive integer'}), 400

    # --- validate quantity ----------------------------------------------------
    quantity, err = _parse_int_field(data.get('quantity', 1), 'quantity')
    if err:
        return err
    if quantity < 1:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    # --- product existence and stock check -----------------------------------
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock == 0:
        return jsonify({'error': 'Product is out of stock'}), 400

    if quantity > product.stock:
        return jsonify({
            'error':     'Quantity exceeds available stock',
            'available': product.stock,
        }), 400

    # --- upsert cart item -----------------------------------------------------
    try:
        existing = CartItem.query.filter_by(
            user_id=current_user_id,
            product_id=product_id,
        ).first()

        if existing:
            new_quantity = existing.quantity + quantity
            # Re-check against stock for the combined total
            if new_quantity > product.stock:
                return jsonify({
                    'error':          'Combined quantity exceeds available stock',
                    'available':      product.stock,
                    'current_in_cart': existing.quantity,
                }), 400

            existing.quantity = new_quantity
            db.session.commit()
            return jsonify({
                'message':   'Cart updated',
                'cart_item': existing.to_dict(),
            }), 200

        cart_item = CartItem(
            user_id=current_user_id,
            product_id=product_id,
            quantity=quantity,
        )
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({
            'message':   'Product added to cart',
            'cart_item': cart_item.to_dict(),
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to add item to cart'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add item to cart', 'details': str(e)}), 500


@cart_bp.route('/items/<int:item_id>', methods=['PATCH'])
@jwt_required()
def update_cart_item(item_id):
    """Set the quantity of a cart item to an exact value.

    Body: { "quantity": <int, ≥1> }

    Returns 404 whether the item does not exist OR belongs to another user
    (prevents leaking existence of other users' cart items).
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # --- validate quantity ----------------------------------------------------
    quantity, err = _parse_int_field(data.get('quantity'), 'quantity')
    if err:
        return err
    if quantity < 1:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    # --- ownership check (fetch-and-verify in one query) ---------------------
    cart_item, err = _owned_cart_item(item_id, current_user_id)
    if err:
        return err

    # --- product availability guard ------------------------------------------
    product = cart_item.product
    if not product:
        # Product was deleted after it was added to the cart
        return jsonify({
            'error': 'The product associated with this cart item no longer exists',
        }), 409

    if quantity > product.stock:
        return jsonify({
            'error':     'Quantity exceeds available stock',
            'available': product.stock,
        }), 400

    try:
        cart_item.quantity = quantity
        db.session.commit()
        return jsonify({
            'message':   'Cart item updated',
            'cart_item': cart_item.to_dict(),
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update cart item', 'details': str(e)}), 500


@cart_bp.route('/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    """Remove a single item from the cart.

    Returns 404 whether the item does not exist OR belongs to another user
    (prevents leaking existence of other users' cart items).
    """
    current_user_id = int(get_jwt_identity())

    cart_item, err = _owned_cart_item(item_id, current_user_id)
    if err:
        return err

    try:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'message': 'Item removed from cart'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to remove item from cart', 'details': str(e)}), 500


@cart_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Remove every item from the current user's cart."""
    current_user_id = int(get_jwt_identity())

    try:
        CartItem.query.filter_by(user_id=current_user_id).delete()
        db.session.commit()
        return jsonify({'message': 'Cart cleared'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to clear cart', 'details': str(e)}), 500
