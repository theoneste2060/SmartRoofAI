from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app
from models import User, Product, Order, Review, CartItem
from utils import *
from ml_models import *
import json

@app.route('/')
def index():
    products = get_products()
    featured_products = list(products.values())[:6]
    return render_template('index.html', products=featured_products)

@app.route('/products')
def products():
    products_dict = get_products()
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
    products = get_products()
    product = products.get(product_id)
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('products'))
    
    # Get similar products
    product_recommender.fit(products)
    similar_product_ids = product_recommender.get_similar_products(product_id)
    similar_products = [products[pid] for pid in similar_product_ids if pid in products]
    
    # Get reviews
    all_reviews = get_reviews()
    product_reviews = [r for r in all_reviews.values() if r.product_id == product_id]
    
    # Get users for review display
    users = get_users()
    
    return render_template('product_detail.html', 
                         product=product, 
                         similar_products=similar_products,
                         reviews=product_reviews,
                         users=users)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    
    cart_item = CartItem(product_id, quantity, current_user.id)
    add_cart_item(cart_item)
    
    flash('Item added to cart!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/cart')
@login_required
def cart():
    user_cart = get_user_cart(current_user.id)
    products = get_products()
    
    cart_items = []
    total = 0
    
    for product_id, cart_item in user_cart.items():
        product = products.get(product_id)
        if product:
            subtotal = product.price * cart_item.quantity
            cart_items.append({
                'product': product,
                'quantity': cart_item.quantity,
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > 0:
        cart_item = CartItem(product_id, quantity, current_user.id)
        add_cart_item(cart_item)
    else:
        user_cart = get_user_cart(current_user.id)
        if product_id in user_cart:
            del user_cart[product_id]
    
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    user_cart = get_user_cart(current_user.id)
    products = get_products()
    
    cart_items = []
    total = 0
    
    for product_id, cart_item in user_cart.items():
        product = products.get(product_id)
        if product:
            subtotal = product.price * cart_item.quantity
            cart_items.append({
                'product': product,
                'quantity': cart_item.quantity,
                'subtotal': subtotal
            })
            total += subtotal
    
    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    user_cart = get_user_cart(current_user.id)
    products = get_products()
    
    order_items = []
    total = 0
    
    for product_id, cart_item in user_cart.items():
        product = products.get(product_id)
        if product:
            subtotal = product.price * cart_item.quantity
            order_items.append({
                'product_id': product_id,
                'product_name': product.name,
                'quantity': cart_item.quantity,
                'price': product.price,
                'subtotal': subtotal
            })
            total += subtotal
    
    if not order_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))
    
    # Create order
    orders = get_orders()
    order_id = get_next_id(orders)
    order = Order(order_id, current_user.id, order_items, total)
    add_order(order)
    
    # Clear cart
    clear_user_cart(current_user.id)
    
    flash('Order placed successfully!', 'success')
    return redirect(url_for('profile'))

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
        users = get_users()
        user_id = get_next_id(users)
        user = User(user_id, username, email, generate_password_hash(password))
        add_user(user)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    orders = get_orders()
    user_orders = [o for o in orders.values() if o.user_id == current_user.id]
    user_orders.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('profile.html', orders=user_orders)

@app.route('/add_review/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    rating = int(request.form['rating'])
    comment = request.form['comment']
    
    # Analyze sentiment
    sentiment, score = sentiment_analyzer.analyze_sentiment(comment)
    
    reviews = get_reviews()
    review_id = get_next_id(reviews)
    review = Review(review_id, current_user.id, product_id, rating, comment, sentiment)
    add_review(review)
    
    flash('Review added successfully!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/calculate_roof', methods=['POST'])
def calculate_roof():
    data = request.get_json()
    
    length = float(data['length'])
    width = float(data['width'])
    roof_type = data['roof_type']
    material_type = data['material_type']
    
    calculation = roof_calculator.calculate_materials(length, width, roof_type, material_type)
    
    # Get recommended products
    products = get_products()
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

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        data = request.get_json()
        user_message = data.get('message', '')
        
        response = chatbot.get_response(user_message)
        
        return jsonify({'response': response})
    
    return render_template('chat.html')

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    users = get_users()
    products = get_products()
    orders = get_orders()
    reviews = get_reviews()
    
    # Calculate statistics
    total_users = len(users)
    total_products = len(products)
    total_orders = len(orders)
    total_revenue = sum(order.total for order in orders.values())
    
    # Recent orders
    recent_orders = sorted(orders.values(), key=lambda x: x.created_at, reverse=True)[:5]
    
    # Customer segments
    segments = customer_segmentation.segment_customers(orders)
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders,
                         segments=segments,
                         users=users)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    users = get_users()
    orders = get_orders()
    
    # Get customer segments
    segments = customer_segmentation.segment_customers(orders)
    
    return render_template('admin/users.html', users=users, segments=segments)

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    products = get_products()
    return render_template('admin/products.html', products=products)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    orders = get_orders()
    users = get_users()
    
    # Sort orders by date
    sorted_orders = sorted(orders.values(), key=lambda x: x.created_at, reverse=True)
    
    return render_template('admin/orders.html', orders=sorted_orders, users=users)

@app.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    orders = get_orders()
    reviews = get_reviews()
    products = get_products()
    
    # Revenue by month (simplified)
    revenue_data = {}
    for order in orders.values():
        month = order.created_at.strftime('%Y-%m')
        revenue_data[month] = revenue_data.get(month, 0) + order.total
    
    # Product performance
    product_sales = {}
    for order in orders.values():
        for item in order.items:
            product_id = item['product_id']
            if product_id not in product_sales:
                product_sales[product_id] = {'quantity': 0, 'revenue': 0}
            product_sales[product_id]['quantity'] += item['quantity']
            product_sales[product_id]['revenue'] += item['subtotal']
    
    # Sentiment analysis
    sentiment_data = {'positive': 0, 'negative': 0, 'neutral': 0}
    for review in reviews.values():
        if review.sentiment:
            sentiment_data[review.sentiment] += 1
    
    return render_template('admin/reports.html',
                         revenue_data=revenue_data,
                         product_sales=product_sales,
                         sentiment_data=sentiment_data,
                         products=products)

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    new_status = request.form['status']
    orders = get_orders()
    
    if order_id in orders:
        orders[order_id].status = new_status
        flash('Order status updated', 'success')
    else:
        flash('Order not found', 'error')
    
    return redirect(url_for('admin_orders'))
