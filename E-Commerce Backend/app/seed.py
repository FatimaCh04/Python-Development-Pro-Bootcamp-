"""Database seed script with sample products for Field & Form."""
from app.extensions import db
from app.models import Product
from flask import current_app


def seed_products():
    """Seed the database with 12 Field & Form products."""
    
    # Check if products already exist
    if Product.query.count() > 0:
        current_app.logger.info('Products already exist, skipping seed.')
        return
    
    products = [
        {
            'sku': 'ARCH-CHAIR-001',
            'name': 'Arch Support Lounge Chair',
            'category': 'Seating',
            'description': 'Ergonomic lounge chair with curved back support and premium upholstery. Perfect for modern living spaces.',
            'price_cents': 42900,
            'stock': 15,
            'image_url': 'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=800'
        },
        {
            'sku': 'OAK-TABLE-002',
            'name': 'Solid Oak Dining Table',
            'category': 'Tables',
            'description': 'Handcrafted solid oak dining table with natural finish. Seats 6-8 comfortably.',
            'price_cents': 89900,
            'stock': 8,
            'image_url': 'https://images.unsplash.com/photo-1617806118233-18e1de247200?w=800'
        },
        {
            'sku': 'MOD-SHELF-003',
            'name': 'Modular Shelf System',
            'category': 'Storage',
            'description': 'Versatile modular shelving with adjustable heights. Minimalist design in walnut or white oak.',
            'price_cents': 35900,
            'stock': 22,
            'image_url': 'https://images.unsplash.com/photo-1594620302200-9a762244a156?w=800'
        },
        {
            'sku': 'BRASS-LAMP-004',
            'name': 'Brass Arc Floor Lamp',
            'category': 'Lighting',
            'description': 'Sculptural brass floor lamp with adjustable arc. Adds warmth and dimension to any room.',
            'price_cents': 29900,
            'stock': 18,
            'image_url': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800'
        },
        {
            'sku': 'LINEN-SOFA-005',
            'name': 'Linen Upholstered Sofa',
            'category': 'Seating',
            'description': 'Three-seat sofa in natural linen with deep cushions. Timeless comfort and style.',
            'price_cents': 124900,
            'stock': 6,
            'image_url': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800'
        },
        {
            'sku': 'MARBLE-SIDE-006',
            'name': 'Marble Side Table',
            'category': 'Tables',
            'description': 'Elegant side table with white marble top and brass legs. Perfect accent piece.',
            'price_cents': 32900,
            'stock': 14,
            'image_url': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800'
        },
        {
            'sku': 'WOOD-BENCH-007',
            'name': 'Reclaimed Wood Bench',
            'category': 'Seating',
            'description': 'Rustic bench made from reclaimed wood. Each piece is unique with natural variations.',
            'price_cents': 38900,
            'stock': 10,
            'image_url': 'https://images.unsplash.com/photo-1519947486511-46149fa0a254?w=800'
        },
        {
            'sku': 'GLASS-PEND-008',
            'name': 'Hand-Blown Glass Pendant',
            'category': 'Lighting',
            'description': 'Artisan hand-blown glass pendant light. Available in amber, clear, or smoke finish.',
            'price_cents': 24900,
            'stock': 25,
            'image_url': 'https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=800'
        },
        {
            'sku': 'CANE-CABIN-009',
            'name': 'Cane Door Cabinet',
            'category': 'Storage',
            'description': 'Mid-century inspired cabinet with natural cane doors and oak frame. Ample storage space.',
            'price_cents': 68900,
            'stock': 9,
            'image_url': 'https://images.unsplash.com/photo-1595428774223-ef52624120d2?w=800'
        },
        {
            'sku': 'WOOL-RUG-010',
            'name': 'Hand-Tufted Wool Rug',
            'category': 'Textiles',
            'description': 'Luxurious hand-tufted wool rug in neutral tones. 8x10 feet, adds warmth to any space.',
            'price_cents': 79900,
            'stock': 12,
            'image_url': 'https://images.unsplash.com/photo-1600166898405-da9535204843?w=800'
        },
        {
            'sku': 'VELVET-OTTO-011',
            'name': 'Velvet Ottoman',
            'category': 'Seating',
            'description': 'Plush velvet ottoman with wooden legs. Perfect as footrest or extra seating.',
            'price_cents': 27900,
            'stock': 20,
            'image_url': 'https://images.unsplash.com/photo-1586158291800-2665f07bff62?w=800'
        },
        {
            'sku': 'MIRROR-WALL-012',
            'name': 'Arched Wall Mirror',
            'category': 'Decor',
            'description': 'Full-length arched mirror with thin metal frame. Opens up space and reflects light beautifully.',
            'price_cents': 34900,
            'stock': 16,
            'image_url': 'https://images.unsplash.com/photo-1618220179428-22790b461013?w=800'
        }
    ]
    
    try:
        for product_data in products:
            product = Product(**product_data)
            db.session.add(product)
        
        db.session.commit()
        
        current_app.logger.info(f'Successfully seeded {len(products)} products.')
        print(f'✓ Successfully seeded {len(products)} products to the database.')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error seeding products: {str(e)}')
        print(f'✗ Error seeding products: {str(e)}')
        raise


def clear_products():
    """Clear all products from the database (use with caution)."""
    try:
        count = Product.query.delete()
        db.session.commit()
        
        current_app.logger.info(f'Cleared {count} products from database.')
        print(f'✓ Cleared {count} products from the database.')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error clearing products: {str(e)}')
        print(f'✗ Error clearing products: {str(e)}')
        raise
