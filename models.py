from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = datetime.now()
    
    @staticmethod
    def get(user_id):
        from utils import get_users
        users = get_users()
        return users.get(user_id)
    
    @staticmethod
    def get_by_email(email):
        from utils import get_users
        users = get_users()
        for user in users.values():
            if user.email == email:
                return user
        return None
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product:
    def __init__(self, id, name, description, price, category, image_url, stock=100):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.image_url = image_url
        self.stock = stock
        self.created_at = datetime.now()

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
