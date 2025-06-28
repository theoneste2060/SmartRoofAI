import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

DATABASE_PATH = 'smartroof.db'

def init_database():
    """Initialize SQLite database with tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image_url TEXT,
            stock INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            sentiment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Cart items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    conn.commit()
    
    # Insert default admin user if not exists
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('admin@smartroof.com',))
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@smartroof.com', generate_password_hash('admin123'), True))
    
    # Insert sample products if not exists
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        products = [
            ('Corrugated Metal Sheets', 'Durable galvanized steel roofing sheets perfect for residential and commercial use', 25.99, 'Metal Sheets', '/static/images/placeholder.svg'),
            ('Asphalt Shingles', 'High-quality asphalt shingles with 25-year warranty', 45.50, 'Shingles', '/static/images/placeholder.svg'),
            ('Clay Roof Tiles', 'Traditional clay tiles for Mediterranean-style roofing', 65.00, 'Tiles', '/static/images/placeholder.svg'),
            ('Rubber Roofing Membrane', 'EPDM rubber membrane for flat roofs', 35.75, 'Membrane', '/static/images/placeholder.svg'),
            ('Polycarbonate Sheets', 'Transparent polycarbonate sheets for skylights', 42.25, 'Polycarbonate', '/static/images/placeholder.svg'),
            ('Aluminum Roofing Coil', 'Lightweight aluminum coils for custom roofing', 38.99, 'Metal Sheets', '/static/images/placeholder.svg'),
            ('Fiberglass Shingles', 'Fire-resistant fiberglass shingles with enhanced durability', 52.30, 'Shingles', '/static/images/placeholder.svg'),
            ('Concrete Roof Tiles', 'Heavy-duty concrete tiles for long-lasting roofing', 58.75, 'Tiles', '/static/images/placeholder.svg'),
        ]
        
        cursor.executemany('''
            INSERT INTO products (name, description, price, category, image_url)
            VALUES (?, ?, ?, ?, ?)
        ''', products)
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database when module is imported
init_database()