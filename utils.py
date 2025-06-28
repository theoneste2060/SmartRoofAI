from models import User, Product, Order, Review
from werkzeug.security import generate_password_hash
import json

# In-memory storage for MVP
users = {}
products = {}
orders = {}
reviews = {}
cart_items = {}

def initialize_data():
    """Initialize with sample data"""
    global users, products, orders, reviews
    
    # Initialize admin user
    admin_user = User(
        id=1,
        username='admin',
        email='admin@smartroof.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )
    users[1] = admin_user
    
    # Sample products
    sample_products = [
        Product(1, 'Corrugated Metal Sheets', 'Durable galvanized steel roofing sheets perfect for residential and commercial use', 25.99, 'Metal Sheets', 'https://via.placeholder.com/300x200/6c757d/ffffff?text=Metal+Sheets'),
        Product(2, 'Asphalt Shingles', 'High-quality asphalt shingles with 25-year warranty', 45.50, 'Shingles', 'https://via.placeholder.com/300x200/6c757d/ffffff?text=Asphalt+Shingles'),
        Product(3, 'Clay Roof Tiles', 'Traditional clay tiles for Mediterranean-style roofing', 65.00, 'Tiles', 'https://via.placeholder.com/300x200/6c757d/ffffff?text=Clay+Tiles'),
        Product(4, 'Rubber Roofing Membrane', 'EPDM rubber membrane for flat roofs', 35.75, 'Membrane', 'https://via.placeholder.com/300x200/6c757d/ffffff?text=Rubber+Membrane'),
        Product(5, 'Polycarbonate Sheets', 'Transparent polycarbonate sheets for skylights', 42.25, 'Polycarbonate', 'https://via.placeholder.com/300x200/6c757d/ffffff?text=Polycarbonate'),
        Product(6, 'Aluminum Roofing Coil', 'Lightweight aluminum coils for custom roofing', 38.99, 'Metal Sheets', 'https://via.placeholder.com/300x200/6c757d/ffffff?text=Aluminum+Coil'),
        Product(7, 'Fiberglass Shingles', 'Fire-resistant fiberglass shingles with enhanced durability', 52.30, 'Shingles', 'https://via.placeholder.com/300x200/6c757d/ffffff?text=Fiberglass+Shingles'),
        Product(8, 'Concrete Roof Tiles', 'Heavy-duty concrete tiles for long-lasting roofing', 58.75, 'Tiles', 'https://via.placeholder.com/300x200/6c757d/ffffff?text=Concrete+Tiles'),
    ]
    
    for product in sample_products:
        products[product.id] = product

def get_users():
    return users

def get_products():
    return products

def get_orders():
    return orders

def get_reviews():
    return reviews

def get_cart_items():
    return cart_items

def add_user(user):
    users[user.id] = user

def add_product(product):
    products[product.id] = product

def add_order(order):
    orders[order.id] = order

def add_review(review):
    reviews[review.id] = review

def add_cart_item(item):
    if item.user_id not in cart_items:
        cart_items[item.user_id] = {}
    cart_items[item.user_id][item.product_id] = item

def get_user_cart(user_id):
    return cart_items.get(user_id, {})

def clear_user_cart(user_id):
    if user_id in cart_items:
        cart_items[user_id] = {}

def get_next_id(collection):
    if not collection:
        return 1
    return max(collection.keys()) + 1

# Initialize data on import
initialize_data()
