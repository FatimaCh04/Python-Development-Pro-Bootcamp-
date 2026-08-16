"""Product routes for browsing and managing inventory."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Product, User
from sqlalchemy import or_

products_bp = Blueprint('products', __name__, url_prefix='/api/products')


@products_bp.route('', methods=['GET'])
def get_products():
    """Get all products with optional filtering and pagination.
    
    Query parameters:
        - category: Filter by category
        - search: Search in name and description
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
    
    Returns:
        {
            "products": [...],
            "total": 50,
            "page": 1,
            "per_page": 20,
            "pages": 3
        }
    """
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # Build query
    query = Product.query
    
    # Filter by category
    category = request.args.get('category')
    if category:
        query = query.filter(Product.category == category)
    
    # Search in name and description
    search = request.args.get('search')
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )
    
    # Execute paginated query
    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'products': [product.to_dict() for product in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }), 200


@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID.
    
    Returns:
        {
            "product": {...}
        }
    """
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'product': product.to_dict()
    }), 200


@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all unique product categories.
    
    Returns:
        {
            "categories": ["Seating", "Storage", "Lighting", ...]
        }
    """
    categories = db.session.query(Product.category).distinct().order_by(Product.category).all()
    category_list = [cat[0] for cat in categories]
    
    return jsonify({
        'categories': category_list
    }), 200


# Admin-only routes (protected)
def admin_required():
    """Check if the current user is an admin.
    For simplicity, we'll check if the user email contains 'admin'.
    In production, use a proper role-based system."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return None, (jsonify({'error': 'User not found'}), 404)
    
    # Simple admin check - replace with proper role system in production
    if 'admin' not in user.email.lower():
        return None, (jsonify({'error': 'Admin access required'}), 403)
    
    return user, None


@products_bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    """Create a new product (admin only).
    
    Expected JSON:
        {
            "sku": "CHAIR-001",
            "name": "Modern Chair",
            "category": "Seating",
            "description": "A comfortable modern chair",
            "price_cents": 29900,
            "stock": 50,
            "image_url": "https://example.com/chair.jpg"
        }
    
    Returns:
        {
            "message": "Product created successfully",
            "product": {...}
        }
    """
    user, error = admin_required()
    if error:
        return error
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['sku', 'name', 'category', 'price_cents']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if SKU already exists
    existing_product = Product.query.filter_by(sku=data['sku']).first()
    if existing_product:
        return jsonify({'error': 'SKU already exists'}), 409
    
    try:
        product = Product(
            sku=data['sku'],
            name=data['name'],
            category=data['category'],
            description=data.get('description'),
            price_cents=int(data['price_cents']),
            stock=int(data.get('stock', 0)),
            image_url=data.get('image_url')
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create product', 'details': str(e)}), 500


@products_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update an existing product (admin only).
    
    Expected JSON: Any product fields to update
    
    Returns:
        {
            "message": "Product updated successfully",
            "product": {...}
        }
    """
    user, error = admin_required()
    if error:
        return error
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Update fields if provided
        if 'sku' in data:
            # Check if new SKU conflicts with another product
            existing = Product.query.filter(Product.sku == data['sku'], Product.id != product_id).first()
            if existing:
                return jsonify({'error': 'SKU already exists'}), 409
            product.sku = data['sku']
        
        if 'name' in data:
            product.name = data['name']
        if 'category' in data:
            product.category = data['category']
        if 'description' in data:
            product.description = data['description']
        if 'price_cents' in data:
            product.price_cents = int(data['price_cents'])
        if 'stock' in data:
            product.stock = int(data['stock'])
        if 'image_url' in data:
            product.image_url = data['image_url']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update product', 'details': str(e)}), 500


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete a product (admin only).
    
    Returns:
        {
            "message": "Product deleted successfully"
        }
    """
    user, error = admin_required()
    if error:
        return error
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    try:
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete product', 'details': str(e)}), 500
