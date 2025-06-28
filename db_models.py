import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from datetime import datetime

def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=os.environ.get('PGHOST'),
        database=os.environ.get('PGDATABASE'),
        user=os.environ.get('PGUSER'),
        password=os.environ.get('PGPASSWORD'),
        port=os.environ.get('PGPORT'),
        cursor_factory=RealDictCursor
    )

def init_database():
    """Initialize PostgreSQL database with tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop existing tables if they exist (for development)
    cursor.execute('DROP TABLE IF EXISTS reviews CASCADE')
    cursor.execute('DROP TABLE IF EXISTS cart_items CASCADE')
    cursor.execute('DROP TABLE IF EXISTS orders CASCADE')
    cursor.execute('DROP TABLE IF EXISTS products CASCADE')
    cursor.execute('DROP TABLE IF EXISTS users CASCADE')
    
    # Users table
    cursor.execute('''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            category VARCHAR(100) NOT NULL,
            image_url VARCHAR(255),
            stock INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Orders table
    cursor.execute('''
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            items JSONB NOT NULL,
            total DECIMAL(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Reviews table
    cursor.execute('''
        CREATE TABLE reviews (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            sentiment VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Cart items table
    cursor.execute('''
        CREATE TABLE cart_items (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, product_id)
        )
    ''')
    
    conn.commit()
    
    # Insert default admin user
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = %s', ('admin@smartroof.com',))
    if cursor.fetchone()['count'] == 0:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (%s, %s, %s, %s)
        ''', ('admin', 'admin@smartroof.com', generate_password_hash('admin123'), True))
    
    # Insert sample products
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()['count'] == 0:
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
            VALUES (%s, %s, %s, %s, %s)
        ''', products)
    
    conn.commit()
    cursor.close()
    conn.close()

# Initialize database when module is imported
try:
    init_database()
    print("Database initialized successfully")
except Exception as e:
    print(f"Database initialization error: {e}")