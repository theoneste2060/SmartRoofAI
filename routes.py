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
    print("DEBUG: Login route accessed")
    if request.method == 'POST':
        print("DEBUG: Login POST request received")
        email = request.form['email']
        password = request.form['password']
        
        print(f"DEBUG: Login attempt for email: {email}")
        
        user = User.get_by_email(email)
        print(f"DEBUG: User found: {user is not None}")
        
        if user and user.check_password(password):
            print("DEBUG: Password check successful, logging in user")
            login_user(user)
            flash('Logged in successfully!', 'success')
            
            # Check if user is admin and redirect accordingly
            if user.is_admin:
                print("DEBUG: User is admin, redirecting to admin dashboard")
                return redirect(url_for('admin_dashboard'))
            else:
                print("DEBUG: User is regular user, redirecting to home page")
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            print("DEBUG: Login failed - invalid credentials")
            flash('Invalid email or password', 'error')
    
    print("DEBUG: Rendering login template")
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
    try:
        conn = get_db_connection()
        cart_items_data = conn.execute('''
            SELECT ci.*, p.name, p.price, p.image_url 
            FROM cart_items ci 
            JOIN products p ON ci.product_id = p.id 
            WHERE ci.user_id = ?
        ''', (current_user.id,)).fetchall()
        conn.close()
        
        cart_items = []
        total = 0
        
        for item in cart_items_data:
            product = Product.get(item['product_id'])
            if product:
                cart_items.append({
                    'id': item['id'],
                    'product': product,
                    'quantity': item['quantity'],
                    'subtotal': product.price * item['quantity']
                })
                total += product.price * item['quantity']
        
        return render_template('cart.html', cart_items=cart_items, total=total)
    except Exception as e:
        return render_template('cart.html', cart_items=[], total=0)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.get(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('products'))
    
    quantity = int(request.form.get('quantity', 1))
    
    try:
        conn = get_db_connection()
        # Check if item already in cart
        existing_item = conn.execute(
            'SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?',
            (current_user.id, product_id)
        ).fetchone()
        
        if existing_item:
            # Update quantity
            conn.execute(
                'UPDATE cart_items SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?',
                (quantity, current_user.id, product_id)
            )
        else:
            # Add new item
            conn.execute(
                'INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)',
                (current_user.id, product_id, quantity)
            )
        
        conn.commit()
        conn.close()
        
        flash(f'{product.name} added to cart!', 'success')
    except Exception as e:
        flash('Error adding item to cart. Please try again.', 'error')
    
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    try:
        conn = get_db_connection()
        # Verify the item belongs to the current user
        item = conn.execute(
            'SELECT * FROM cart_items WHERE id = ? AND user_id = ?',
            (item_id, current_user.id)
        ).fetchone()
        
        if item:
            conn.execute('DELETE FROM cart_items WHERE id = ?', (item_id,))
            conn.commit()
            flash('Item removed from cart!', 'success')
        else:
            flash('Item not found in cart!', 'error')
        
        conn.close()
    except Exception as e:
        flash('Error removing item from cart. Please try again.', 'error')
    
    return redirect(url_for('cart'))

@app.route('/update_cart_quantity/<int:item_id>', methods=['POST'])
@login_required
def update_cart_quantity(item_id):
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        return redirect(url_for('remove_from_cart', item_id=item_id))
    
    try:
        conn = get_db_connection()
        # Verify the item belongs to the current user
        item = conn.execute(
            'SELECT * FROM cart_items WHERE id = ? AND user_id = ?',
            (item_id, current_user.id)
        ).fetchone()
        
        if item:
            conn.execute(
                'UPDATE cart_items SET quantity = ? WHERE id = ?',
                (quantity, item_id)
            )
            conn.commit()
            flash('Cart updated!', 'success')
        else:
            flash('Item not found in cart!', 'error')
        
        conn.close()
    except Exception as e:
        flash('Error updating cart. Please try again.', 'error')
    
    return redirect(url_for('cart'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', orders=[])

@app.route('/calculate_roof', methods=['POST'])
def calculate_roof():
    try:
        print("DEBUG: calculate_roof endpoint called")
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")
        
        length = float(data['length'])
        width = float(data['width'])
        roof_type = data['roof_type']
        material_type = data['material_type']
        
        print(f"DEBUG: Processing - Length: {length}, Width: {width}, Roof Type: {roof_type}, Material: {material_type}")
        
        # Check if roof_calculator is available
        if 'roof_calculator' not in globals():
            print("ERROR: roof_calculator not found in globals")
            return jsonify({'error': 'Roof calculator not available'}), 500
        
        calculation = roof_calculator.calculate_materials(length, width, roof_type, material_type)
        print(f"DEBUG: Calculation result: {calculation}")
        
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
        
        result = {
            'calculation': calculation,
            'recommended_products': recommended_products[:3]
        }
        print(f"DEBUG: Returning result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"ERROR in calculate_roof: {str(e)}")
        import traceback
        traceback.print_exc()
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
    
    # Get recent orders for dashboard
    recent_orders_data = conn.execute('''
        SELECT o.*, u.username 
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    # Convert revenue to RWF (multiply by 1000)
    total_revenue_rwf = (total_revenue or 0) * 1000
    
    recent_orders = []
    for order in recent_orders_data:
        recent_orders.append({
            'id': order['id'],
            'username': order['username'] or 'Unknown User',
            'total': order['total'] * 1000,  # Convert to RWF
            'status': order['status'],
            'created_at': order['created_at']
        })
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue_rwf,
                         recent_orders=recent_orders,
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

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        category = request.form['category']
        stock = int(request.form['stock'])
        image_url = request.form['image_url'] or '/static/images/placeholder.svg'
        
        try:
            conn = get_db_connection()
            cursor = conn.execute('''
                INSERT INTO products (name, description, price, category, image_url, stock)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, price, category, image_url, stock))
            product_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash('Error adding product. Please try again.', 'error')
            return render_template('admin/product_form.html', product=None, action='Add')
    
    return render_template('admin/product_form.html', product=None, action='Add')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    product = Product.get(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        category = request.form['category']
        stock = int(request.form['stock'])
        image_url = request.form['image_url'] or '/static/images/placeholder.svg'
        
        try:
            conn = get_db_connection()
            conn.execute('''
                UPDATE products 
                SET name = ?, description = ?, price = ?, category = ?, image_url = ?, stock = ?
                WHERE id = ?
            ''', (name, description, price, category, image_url, stock, product_id))
            conn.commit()
            conn.close()
            
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash('Error updating product. Please try again.', 'error')
            return render_template('admin/product_form.html', product=product, action='Edit')
    
    return render_template('admin/product_form.html', product=product, action='Edit')

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    product = Product.get(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()
        
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting product. Please try again.', 'error')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    try:
        conn = get_db_connection()
        
        # Get all orders with user information
        orders = conn.execute('''
            SELECT o.*, u.username, u.email 
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
        ''').fetchall()
        
        # Get all users for reference
        users = conn.execute('SELECT id, username, email FROM users').fetchall()
        conn.close()
        
        # Convert to dictionaries for easier template usage
        orders_dict = {}
        users_dict = {}
        
        for order in orders:
            orders_dict[order['id']] = {
                'id': order['id'],
                'user_id': order['user_id'],
                'username': order['username'] or 'Unknown User',
                'email': order['email'] or 'N/A',
                'items': order['items'],
                'total': order['total'] * 1000,  # Convert to RWF
                'status': order['status'],
                'shipping_address': order.get('shipping_address', ''),
                'payment_method': order.get('payment_method', 'Unknown'),
                'created_at': order['created_at']
            }
        
        for user in users:
            users_dict[user['id']] = {
                'username': user['username'],
                'email': user['email']
            }
        
        return render_template('admin/orders.html', orders=orders_dict, users=users_dict)
        
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return render_template('admin/orders.html', orders={}, users={})

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

@app.route('/add_review/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    product = Product.get(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('products'))
    
    rating = int(request.form['rating'])
    comment = request.form['comment']
    
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO reviews (user_id, product_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (current_user.id, product_id, rating, comment))
        conn.commit()
        conn.close()
        
        flash('Review added successfully!', 'success')
    except Exception as e:
        flash('Error adding review. Please try again.', 'error')
    
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/debug/cart')
@login_required
def debug_cart():
    """Debug route to check cart contents"""
    try:
        conn = get_db_connection()
        cart_items = conn.execute('SELECT * FROM cart_items WHERE user_id = ?', (current_user.id,)).fetchall()
        conn.close()
        
        return jsonify({
            'user_id': current_user.id,
            'cart_items': [dict(item) for item in cart_items],
            'count': len(cart_items)
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/checkout')
@login_required
def checkout():
    """Checkout page"""
    try:
        conn = get_db_connection()
        cart_items_data = conn.execute('''
            SELECT ci.*, p.name, p.price, p.image_url 
            FROM cart_items ci 
            JOIN products p ON ci.product_id = p.id 
            WHERE ci.user_id = ?
        ''', (current_user.id,)).fetchall()
        conn.close()
        
        cart_items = []
        total = 0
        
        for item in cart_items_data:
            product = Product.get(item['product_id'])
            if product:
                cart_items.append({
                    'id': item['id'],
                    'product': product,
                    'quantity': item['quantity'],
                    'subtotal': product.price * item['quantity']
                })
                total += product.price * item['quantity']
        
        if not cart_items:
            flash('Your cart is empty', 'error')
            return redirect(url_for('cart'))
        
        return render_template('checkout.html', cart_items=cart_items, total=total)
    except Exception as e: 
        flash('Error loading checkout page', 'error')
        return redirect(url_for('cart'))

@app.route('/api/cart/count')
def cart_count():
    """API endpoint to get cart count"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'count': 0})
            
        conn = get_db_connection()
        result = conn.execute('''
            SELECT SUM(quantity) as total_items 
            FROM cart_items 
            WHERE user_id = ?
        ''', (current_user.id,)).fetchone()
        conn.close()
        
        total_items = result['total_items'] if result['total_items'] else 0
        return jsonify({'count': total_items})
    except Exception as e:
        return jsonify({'count': 0})

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    """Process order and handle MTN Mobile Money payment"""
    try:
        conn = get_db_connection()
        cart_items_data = conn.execute('''
            SELECT ci.*, p.name, p.price 
            FROM cart_items ci 
            JOIN products p ON ci.product_id = p.id 
            WHERE ci.user_id = ?
        ''', (current_user.id,)).fetchall()
        
        if not cart_items_data:
            flash('Your cart is empty!', 'error')
            return redirect(url_for('cart'))
        
        # Get form data
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        address = request.form.get('address')
        city = request.form.get('city')
        phone = request.form.get('phone')
        payment_method = request.form.get('payment_method')
        
        # Calculate total and prepare items
        cart_items = []
        total = 0
        for item in cart_items_data:
            cart_items.append({
                'product_id': item['product_id'],
                'product_name': item['name'],
                'quantity': item['quantity'],
                'price': item['price'],
                'subtotal': item['price'] * item['quantity']
            })
            total += item['price'] * item['quantity']
        
        if payment_method == 'mtn_mobile_money':
            # Store order data in session for MTN payment processing
            import json
            from flask import session
            session['pending_order'] = {
                'user_id': current_user.id,
                'items': cart_items,
                'total': total,
                'shipping_info': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'address': address,
                    'city': city,
                    'phone': phone
                },
                'payment_method': payment_method
            }
            return render_template('payment/mtn_payment.html', total=total, phone=phone)
        else:
            # For other payment methods, complete order immediately
            import json
            order_items = json.dumps(cart_items)
            conn.execute('''
                INSERT INTO orders (user_id, items, total, status)
                VALUES (?, ?, ?, ?)
            ''', (current_user.id, order_items, total, 'completed'))
            
            # Clear cart
            conn.execute('DELETE FROM cart_items WHERE user_id = ?', (current_user.id,))
            conn.commit()
            conn.close()
            
            flash('Order placed successfully!', 'success')
            return redirect(url_for('profile'))
            
    except Exception as e:
        flash(f'Error processing order: {str(e)}', 'error')
        return redirect(url_for('checkout'))

@app.route('/process_mtn_payment', methods=['POST'])
@login_required 
def process_mtn_payment():
    """Simulate MTN Mobile Money payment processing"""
    try:
        from flask import session
        pending_order = session.get('pending_order')
        
        if not pending_order:
            flash('No pending order found', 'error')
            return redirect(url_for('checkout'))
        
        # Simulate payment processing delay
        import time
        time.sleep(1)
        
        # Create the order
        import json
        order_items = json.dumps(pending_order['items'])
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO orders (user_id, items, total, status)
            VALUES (?, ?, ?, ?)
        ''', (pending_order['user_id'], order_items, pending_order['total'], 'completed'))
        
        # Clear cart
        conn.execute('DELETE FROM cart_items WHERE user_id = ?', (current_user.id,))
        conn.commit()
        conn.close()
        
        # Clear session
        session.pop('pending_order', None)
        
        flash('MTN Mobile Money payment successful! Your order has been placed.', 'success')
        return redirect(url_for('profile'))
        
    except Exception as e:
        flash(f'Payment failed: {str(e)}', 'error')
        return redirect(url_for('checkout')) 
        return redirect(url_for('cart')) 
