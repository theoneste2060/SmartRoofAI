from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from database import get_db_connection

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, is_admin=False, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = created_at or datetime.now()
    
    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['email'], 
                       user['password_hash'], user['is_admin'], user['created_at'])
        return None
    
    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['email'], 
                       user['password_hash'], user['is_admin'], user['created_at'])
        return None
    
    @staticmethod
    def create(username, email, password):
        conn = get_db_connection()
        password_hash = generate_password_hash(password)
        cursor = conn.execute('''
            INSERT INTO users (username, email, password_hash) 
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return User.get(user_id)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product:
    def __init__(self, id, name, description, price, category, image_url, stock=100, created_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.image_url = image_url or '/static/images/placeholder.svg'
        self.stock = stock
        self.created_at = created_at or datetime.now()
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        products = conn.execute('SELECT * FROM products').fetchall()
        conn.close()
        return {product['id']: Product(
            product['id'], product['name'], product['description'],
            product['price'], product['category'], product['image_url'],
            product['stock'], product['created_at']
        ) for product in products}
    
    @staticmethod
    def get(product_id):
        conn = get_db_connection()
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        conn.close()
        if product:
            return Product(
                product['id'], product['name'], product['description'],
                product['price'], product['category'], product['image_url'],
                product['stock'], product['created_at']
            )
        return None

class Order:
    def __init__(self, id, user_id, items, total, status='pending'):
        self.id = id
        self.user_id = user_id
        self.items = items
        self.total = total
        self.status = status
        self.created_at = datetime.now()

class Review:
    def __init__(self, id, user_id, product_id, rating, comment, sentiment=None):
        self.id = id
        self.user_id = user_id
        self.product_id = product_id
        self.rating = rating
        self.comment = comment
        self.sentiment = sentiment
        self.created_at = datetime.now()

class CartItem:
    def __init__(self, product_id, quantity, user_id):
        self.product_id = product_id
        self.quantity = quantity
        self.user_id = user_id
