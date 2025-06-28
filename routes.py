from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app
from models import User, Product
from ml_models import *
from database import get_db_connection
import json

@app.route('/')
def index():
    products = Product.get_all()
    featured_products = list(products.values())[:6]
    return render_template('index.html', products=featured_products)

@app.route('/products')
def products():
    products_dict = Product.get_all()
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    filtered_products = list(products_dict.values())
    
    if category:
        filtered_products = [p for p in filtered_products if p.category == category]
    
    if search:
        filtered_products = [p for p in filtered_products 
                           if search.lower() in p.name.lower() or 
                              search.lower() in p.description.lower()]
    
    categories = list(set(p.category for p in products_dict.values()))
    
    return render_template('products.html', 
                         products=filtered_products, 
                         categories=categories,
                         selected_category=category,
                         search_query=search)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.get(product_id)
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('products'))
    
    # Get similar products (simplified)
    products = Product.get_all()
    similar_products = []
    for p in list(products.values())[:4]:
        if p.id != product_id and p.category == product.category:
            similar_products.append(p)
    
    return render_template('product_detail.html', 
                         product=product, 
                         similar_products=similar_products,
                         reviews=[],
                         users={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.get_by_email(email)
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists
        if User.get_by_email(email):
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        try:
            user = User.create(username, email, password)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html', cart_items=[], total=0)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', orders=[])

@app.route('/calculate_roof', methods=['POST'])
def calculate_roof():
    try:
        data = request.get_json()
        
        length = float(data['length'])
        width = float(data['width'])
        roof_type = data['roof_type']
        material_type = data['material_type']
        
        calculation = roof_calculator.calculate_materials(length, width, roof_type, material_type)
        
        # Get recommended products
        products = Product.get_all()
        recommended_products = []
        for product in products.values():
            if material_type in product.category:
                recommended_products.append({
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'category': product.category
                })
        
        return jsonify({
            'calculation': calculation,
            'recommended_products': recommended_products[:3]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        try:
            data = request.get_json()
            user_message = data.get('message', '')
            
            response = chatbot.get_response(user_message)
            
            return jsonify({'response': response})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    return render_template('chat.html')

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_orders = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    total_revenue = conn.execute('SELECT COALESCE(SUM(total), 0) FROM orders').fetchone()[0]
    conn.close()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         recent_orders=[],
                         segments={},
                         users={})

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    users_data = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    users = {}
    for user_data in users_data:
        users[user_data['id']] = User(
            user_data['id'], user_data['username'], user_data['email'],
            user_data['password_hash'], user_data['is_admin'], user_data['created_at']
        )
    
    return render_template('admin/users.html', users=users, segments={})

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    products = Product.get_all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin/orders.html', orders=[], users={})

@app.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin/reports.html',
                         revenue_data={},
                         product_sales={},
                         sentiment_data={},
                         products={})