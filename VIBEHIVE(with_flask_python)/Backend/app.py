from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import bcrypt                    # 🟢 NEW: secure password hashing
import mysql.connector           # 🟢 CHANGED: use mysql.connector instead of flask_mysqldb
from db_config import get_connection  # 🟢 UPDATED: new db_config function
from difflib import SequenceMatcher

app = Flask(__name__)
CORS(app)


from flask_mail import Mail, Message

# ---------------- EMAIL CONFIG ----------------
# ---------------- EMAIL CONFIG ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'javeranaz48@gmail.com'       # 🟢 replace
app.config['MAIL_PASSWORD'] = 'kebf urtb ncqk yclc'         # 🟢 use Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = ('VibeHive Support', app.config['MAIL_USERNAME'])

mail = Mail(app)


# ---------------- UPLOAD FOLDER CONFIG ----------------
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# ---------------- ADMIN REGISTRATION ----------------
@app.route('/register', methods=['POST'])
def register_admin():
    data = request.form
    full_name = data.get('full_name')
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match!'}), 400

    conn = get_connection()   # 🟢 CHANGED: mysql.connection → get_connection()
    cursor = conn.cursor(dictionary=True)

    # check for duplicate
    cursor.execute("SELECT * FROM admin WHERE email = %s OR username = %s", (email, username))
    existing = cursor.fetchone()
    if existing:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Email or username already exists!'}), 400

    # 🟢 NEW: Secure password hashing
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # check if any admin already exists
    cursor.execute("SELECT COUNT(*) AS count FROM admin")
    result = cursor.fetchone()
    count = int(result['count'])
    
    if count > 0:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Admin already exists! Registration disabled.'}), 400


    # insert admin
    cursor.execute("""
        INSERT INTO admin (full_name, email, username, password_hash)
        VALUES (%s, %s, %s, %s)
    """, (full_name, email, username, hashed_pw.decode('utf-8')))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify({'message': 'Admin registered successfully!'}), 201


# ---------------- ADMIN LOGIN ----------------
@app.route('/login', methods=['POST'])
def login_admin():
    data = request.json
    username_or_email = data.get('username')
    password = data.get('password')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM admin
        WHERE username = %s OR email = %s
    """, (username_or_email, username_or_email))
    admin = cursor.fetchone()

    cursor.close()
    conn.close()

    if not admin:
        return jsonify({'message': 'Invalid credentials!'}), 401

    # 🟢 NEW: Verify hashed password
    if not bcrypt.checkpw(password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
        return jsonify({'message': 'Invalid credentials!'}), 401

    return jsonify({'message': 'Login successful!', 'admin': admin}), 200


# ---------------- ADD PRODUCT ----------------
@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.form
    product_name = data.get('product_name')
    main_category = data.get('main_category')
    sub_category = data.get('sub_category')
    price = data.get('price')
    stock_quantity = data.get('stock_quantity')
    description = data.get('description')

    image = request.files.get('image')
    image_filename = None
    if image:
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (product_name, main_category, sub_category, price, stock_quantity, image_path, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (product_name, main_category, sub_category, price, stock_quantity, image_filename, description))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Product added successfully!'}), 201


# ---------------- DELETE PRODUCT ----------------
@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get image filename before deleting
    cursor.execute("SELECT image_path FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Product not found'}), 404

    image_filename = product['image_path']

    # Delete product from database
    cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
    conn.commit()

    # Delete image from uploads folder if exists
    if image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)

    cursor.close()
    conn.close()
    return jsonify({'message': 'Product deleted successfully!'}), 200

# ---------------- UPDATE PRODUCT ----------------
@app.route('/update_product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.form
    product_name = data.get('product_name')
    # category_name = data.get('category_name')
    main_category = data.get('main_category')
    sub_category = data.get('sub_category')
    price = data.get('price')
    stock_quantity = data.get('stock_quantity')
    description = data.get('description')

    image = request.files.get('image')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get current product image
    cursor.execute("SELECT image_path FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Product not found'}), 404

    image_filename = product['image_path']

    # If new image uploaded, replace the old one
    if image:
        new_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

        # Delete old image
        if image_filename:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            if os.path.exists(old_path):
                os.remove(old_path)

        image_filename = new_filename

    # Update database record
    cursor.execute("""
        UPDATE products
        SET product_name = %s, main_category = %s, sub_category = %s, 
            price = %s, stock_quantity = %s, description = %s, image_path = %s
        WHERE product_id = %s

    """, (product_name, main_category, sub_category, price, stock_quantity, description, image_filename, product_id))
    conn.commit()
    


    cursor.close()
    conn.close()

    return jsonify({'message': 'Product updated successfully!'}), 200



# ---------------- FETCH PRODUCTS (With Filters) ----------------
@app.route('/products', methods=['GET'])
def get_products():
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    sort_order = request.args.get('sort')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT product_id, product_name, main_category, sub_category, price,
               stock_quantity, image_path, description, created_at
        FROM products
    """

    filters = []
    values = []

    # Filter by main category
    if category and category.lower() != "all":
        filters.append("main_category = %s")
        values.append(category)

    # Filter by subcategory
    if subcategory:
        filters.append("sub_category = %s")
        values.append(subcategory)

    # Attach WHERE if filters exist
    if filters:
        query += " WHERE " + " AND ".join(filters)

    # Sorting
    if sort_order == "low":
        query += " ORDER BY price ASC"
    elif sort_order == "high":
        query += " ORDER BY price DESC"
    else:
        query += " ORDER BY created_at DESC"

    cursor.execute(query, values)
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(products), 200


# ---------------- FETCH CATEGORY COUNTS ----------------

@app.route('/categories', methods=['GET'])
def get_category_counts():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all products grouped by main + sub
    cursor.execute("""
        SELECT main_category, sub_category, COUNT(*) AS count
        FROM products
        WHERE main_category IS NOT NULL AND sub_category IS NOT NULL
        GROUP BY main_category, sub_category
        ORDER BY main_category, sub_category
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Build nested structure
    categories = {}
    for row in rows:
        main = row["main_category"]
        sub = row["sub_category"]

        if main not in categories:
            categories[main] = {
                "main_category": main,
                "total": 0,
                "subcategories": []
            }

        categories[main]["total"] += row["count"]
        categories[main]["subcategories"].append({
            "name": sub,
            "count": row["count"]
        })

    return jsonify(list(categories.values())), 200





# ---------------- FETCH ORDERS ----------------
@app.route('/orders', methods=['GET'])
def get_orders():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
                   SELECT o.order_id, p.product_name, c.full_name AS customer_name,
                   o.quantity, o.total_amount, o.order_status, o.order_date
                   FROM orders o
                   JOIN products p ON o.product_id = p.product_id
                   JOIN customers c ON o.customer_id = c.customer_id
                   ORDER BY o.order_date DESC
                """)

    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(orders), 200


# ---------------- DASHBOARD STATS ----------------
@app.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_products FROM products")
    total_products = cursor.fetchone()['total_products']

    cursor.execute("SELECT COUNT(*) AS pending_orders FROM orders WHERE order_status = 'Pending'")
    pending_orders = cursor.fetchone()['pending_orders']

    cursor.execute("SELECT COUNT(*) AS completed_orders FROM orders WHERE order_status = 'Completed'")
    completed_orders = cursor.fetchone()['completed_orders']

    cursor.close()
    conn.close()

    return jsonify({
        'total_products': total_products,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders
    }), 200


# ---------------- SERVE UPLOADED IMAGES ----------------
@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ---------------- CHECK IF ADMIN EXISTS ----------------
@app.route('/check_admin_exists', methods=['GET'])
def check_admin_exists():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM admin")
    (count,) = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'exists': count > 0})

# ---------------- CUSTOMER REGISTRATION ----------------
@app.route('/customer/register', methods=['POST'])
def register_customer():
    data = request.json
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    if not (full_name and email and password):
        return jsonify({'message': 'All required fields must be filled!'}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Check for existing email
    cursor.execute("SELECT * FROM customers WHERE email = %s", (email,))
    existing = cursor.fetchone()
    if existing:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Email already registered!'}), 400

    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute("""
        INSERT INTO customers (full_name, email, password_hash, phone)
        VALUES (%s, %s, %s, %s)
    """, (full_name, email, hashed_pw.decode('utf-8'), phone))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify({'message': 'Customer registered successfully!'}), 201


# ---------------- CUSTOMER LOGIN ----------------
@app.route('/customer/login', methods=['POST'])
def login_customer():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE email = %s", (email,))
    customer = cursor.fetchone()
    cursor.close()
    conn.close()

    if not customer:
        return jsonify({'message': 'Invalid email or password!'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), customer['password_hash'].encode('utf-8')):
        return jsonify({'message': 'Invalid email or password!'}), 401

    return jsonify({'message': 'Login successful!', 'customer': {
        'customer_id': customer['customer_id'],
        'full_name': customer['full_name'],
        'email': customer['email']
    }}), 200


# ---------------- CUSTOMER ORDERS VIEW ----------------
@app.route('/api/orders', methods=['GET'])
def get_customer_orders():
    customer_id = request.args.get('customerId')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.order_id, p.product_name, o.quantity, o.total_amount, 
               o.order_status, o.order_date
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        WHERE o.customer_id = %s
        ORDER BY o.order_date DESC
    """, (customer_id,))
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(orders), 200


# ---------------- CANCEL ORDER (Safe + Stock Restore) ----------------
@app.route('/api/orders/<int:order_id>/cancel', methods=['PUT'])
def cancel_order(order_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1️⃣ Fetch order details
        cursor.execute("""
            SELECT order_status, product_id, quantity
            FROM orders
            WHERE order_id = %s
        """, (order_id,))
        order = cursor.fetchone()

        # 2️⃣ Check if order exists
        if not order:
            return jsonify({'message': 'Order not found'}), 404

        # 3️⃣ Allow cancel only if still pending
        if order['order_status'].lower() != 'pending':
            return jsonify({
                'message': 'Order can only be cancelled if it is still pending.'
            }), 400

        # 4️⃣ Update order status to "Cancelled"
        cursor.execute("""
            UPDATE orders
            SET order_status = 'Cancelled'
            WHERE order_id = %s
        """, (order_id,))

        # 5️⃣ Restore product stock
        cursor.execute("""
            UPDATE products
            SET stock_quantity = stock_quantity + %s
            WHERE product_id = %s
        """, (order['quantity'], order['product_id']))

        # 6️⃣ Commit all changes
        conn.commit()

        return jsonify({
            'message': f'Order #{order_id} cancelled successfully and stock restored.'
        }), 200

    except Exception as e:
        conn.rollback()
        print("Cancel order error:", e)
        return jsonify({'message': 'An error occurred while cancelling the order.'}), 500

    finally:
        cursor.close()
        conn.close()

# ---------------- UPDATE ORDER STATUS (ADMIN) ----------------
@app.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    data = request.get_json()
    new_status = data.get('order_status')

    # Validate new status
    valid_statuses = ['Pending', 'Shipped', 'Completed', 'Cancelled']
    if new_status not in valid_statuses:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Invalid order status'}), 400

    # Check current status
    cursor.execute("SELECT order_status FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        conn.close()
        return jsonify({'message': 'Order not found'}), 404

    # Prevent update if already cancelled
    if order['order_status'] == 'Cancelled':
        cursor.close()
        conn.close()
        return jsonify({'message': 'Cancelled orders cannot be updated'}), 400

    # Update status
    cursor.execute("UPDATE orders SET order_status = %s WHERE order_id = %s", (new_status, order_id))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify({'message': f"Order status updated to {new_status} successfully!"}), 200


# ---------------- Add to Cart ----------------
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    customer_id = data.get('customer_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    conn = get_connection()
    conn.autocommit = False  # ensure manual transaction control
    cursor = conn.cursor(dictionary=True)

    print("🛒 Adding to cart:", customer_id, product_id, quantity)

    try:
        # Set a shorter lock wait time (3 seconds)
        cursor.execute("SET innodb_lock_wait_timeout = 3")

        # Lock the row to avoid race conditions
        cursor.execute("""
            SELECT * FROM cart 
            WHERE customer_id = %s AND product_id = %s 
            FOR UPDATE
        """, (customer_id, product_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE cart 
                SET quantity = quantity + %s
                WHERE customer_id = %s AND product_id = %s
            """, (quantity, customer_id, product_id))
        else:
            cursor.execute("""
                INSERT INTO cart (customer_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (customer_id, product_id, quantity))

        conn.commit()
        return jsonify({'message': 'Item added to cart!'}), 200

    except mysql.connector.Error as err:
        print("❌ Database error:", err)
        conn.rollback()
        return jsonify({'error': str(err)}), 500

    finally:
        cursor.close()
        conn.close()


# ---------------- Place Order ----------------

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.json
    customer_id = data.get('customer_id')
    shipping_address = data.get('shipping_address')
    payment_method = data.get('payment_method')
    phone = data.get('phone')

    if not customer_id:
        return jsonify({'error': 'Login required to place an order.'}), 401

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1️⃣ Fetch cart items
        cursor.execute("""
            SELECT c.product_id, c.quantity, p.product_name, p.price, p.stock_quantity
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.customer_id = %s
        """, (customer_id,))
        cart_items = cursor.fetchall()

        if not cart_items:
            return jsonify({'error': 'Your cart is empty.'}), 400

        order_ids = []

        # 2️⃣ Validate stock before inserting orders
        for item in cart_items:
            if item['quantity'] > item['stock_quantity']:
                conn.rollback()
                return jsonify({
                    'error': f"Insufficient stock for {item['product_name']}. Only {item['stock_quantity']} available."
                }), 400

        # 3️⃣ Create orders and update stock
        for item in cart_items:
            total_amount = item['price'] * item['quantity']

            # Insert order
            cursor.execute("""
                INSERT INTO orders 
                (product_id, customer_id, quantity, total_amount, order_status, shipping_address, payment_method, phone)
                VALUES (%s, %s, %s, %s, 'Pending', %s, %s, %s)
            """, (
                item['product_id'], customer_id, item['quantity'], total_amount,
                shipping_address, payment_method, phone
            ))

            order_id = cursor.lastrowid
            order_ids.append(order_id)

            # Deduct stock
            cursor.execute("""
                UPDATE products 
                SET stock_quantity = stock_quantity - %s
                WHERE product_id = %s
            """, (item['quantity'], item['product_id']))

        # 4️⃣ Clear the cart
        cursor.execute("DELETE FROM cart WHERE customer_id = %s", (customer_id,))

        # 5️⃣ Commit the transaction
        conn.commit()

        return jsonify({
            'message': 'Order placed successfully!',
            'order_ids': order_ids
        }), 200

    except Exception as e:
        conn.rollback()
        print("Checkout error:", e)
        return jsonify({'error': 'Failed to place order. Please try again.'}), 500
    finally:
        cursor.close()
        conn.close()



# ---------------- Total Cart ----------------
@app.route('/cart/summary', methods=['GET'])
def cart_summary():
    customer_id = request.args.get('customer_id')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            SUM(p.price * c.quantity) AS total_price,
            SUM(c.quantity) AS total_items
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.customer_id = %s
    """, (customer_id,))
    summary = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(summary or {'total_price': 0, 'total_items': 0}), 200

# ---------------- View Cart ----------------
@app.route('/cart', methods=['GET'])
def get_cart():
    customer_id = request.args.get('customer_id')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.cart_id, p.product_name, p.price, c.quantity,
               (p.price * c.quantity) AS total
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.customer_id = %s
    """, (customer_id,))
    cart_items = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(cart_items), 200

# ---------------- Clear Cart ----------------
@app.route('/cart/clear', methods=['POST'])
def clear_cart():
    data = request.json
    customer_id = data.get('customer_id')

    if not customer_id:
        return jsonify({'error': 'Customer ID is required.'}), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Delete all items for this customer
        cursor.execute("""
            DELETE FROM cart
            WHERE customer_id = %s
        """, (customer_id,))
        conn.commit()
        return jsonify({'message': 'Cart cleared successfully!'}), 200
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ---------------- Get Specific Order Details ----------------
@app.route('/api/order/<int:order_id>', methods=['GET'])
def get_order_details(order_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            o.order_id, o.quantity, o.total_amount, o.order_status, 
            o.order_date, o.shipping_address, o.payment_method, 
            p.product_name, p.price
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        WHERE o.order_id = %s
    """, (order_id,))
    order_items = cursor.fetchall()
    cursor.close()
    conn.close()

    if not order_items:
        return jsonify({'message': 'Order not found'}), 404

    # Calculate totals for frontend display
    subtotal = sum(float(item['price']) * item['quantity'] for item in order_items)
    shipping_fee = 15.00
    total_amount = subtotal + shipping_fee

    return jsonify({
        'order_id': order_items[0]['order_id'],
        'order_date': order_items[0]['order_date'],
        'order_status': order_items[0]['order_status'],
        'shipping_address': order_items[0]['shipping_address'],
        'payment_method': order_items[0]['payment_method'],
        'items': order_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total_amount': total_amount
    }), 200



# ---------------- AI CHATBOT ROUTE (Local Fallback) ----------------
# ---------------- OFFLINE AI CHATBOT (SMART VERSION, NO OPENAI) ----------------
from bs4 import BeautifulSoup
import re

def extract_text_from_html(filename):
    """Extract readable text from frontend HTML files."""
    try:
        with open(f"templates/{filename}", "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            return " ".join(text.split())
    except:
        return ""


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").lower().strip()
    customer_id = data.get("customer_id")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    reply = ""

    try:
        # 🌐 Extract content from HTML pages
        about_text = extract_text_from_html("about.html")
        contact_text = extract_text_from_html("contact.html")

        # ------------------------------------------------------------
        # 1️⃣ ABOUT / BUSINESS INFO
        # ------------------------------------------------------------
        if any(kw in message for kw in ["what is vibehive", "about vibehive", "who are you", "your business", "describe vibehive", "vibehive"]):
            reply = (
                "🛍️ VibeHive is an online shopping platform offering trendy fashion, footwear, and lifestyle accessories. "
                "We focus on affordability, quality, and customer satisfaction.\n\n"
                f"📘 Summary from About page:\n{about_text[:400]}..."
            )

        # ------------------------------------------------------------
        # 2️⃣ SPECIFIC PRODUCT CHECK (“do you have ...”)
        # ------------------------------------------------------------
        elif any(kw in message for kw in ["have", "available", "in stock", "show me", "find", "search", "looking for", "want", "price of", "cost of"]):
            cursor.execute("SELECT product_name, price, stock_quantity FROM products")
            products = cursor.fetchall()

            found = []
            for p in products:
                if p['product_name'].lower() in message:
                    found.append(p)

            if found:
                lines = []
                for f in found:
                    status = "✅ In stock" if f['stock_quantity'] > 0 else "❌ Out of stock"
                    lines.append(f"• {f['product_name']} — {f['price']} PKR ({status})")
                reply = "🛒 Here’s what I found:\n" + "\n".join(lines)
            else:
                reply = (
                    "🤔 I couldn’t find that exact product name. "
                    "Please make sure you typed it correctly or browse our catalog."
                )

        # ------------------------------------------------------------
        # 3️⃣ NEW ARRIVALS / LATEST PRODUCTS
        # ------------------------------------------------------------
        elif any(kw in message for kw in ["new arrivals", "latest products", "recent products", "what’s new", "new collection"]):
            cursor.execute("SELECT product_name, price FROM products ORDER BY created_at DESC LIMIT 3")
            products = cursor.fetchall()
            if products:
                reply = "🆕 Here are our latest arrivals:\n" + "\n".join(
                    [f"• {p['product_name']} — {p['price']} PKR" for p in products]
                )
            else:
                reply = "Currently, there are no new arrivals listed."

        # ------------------------------------------------------------
        # 4️⃣ BEST SELLING / POPULAR PRODUCT
        # ------------------------------------------------------------
        elif any(kw in message for kw in ["best selling", "most popular", "top product", "famous item", "trending"]):
            cursor.execute("""
                SELECT p.product_name, COUNT(o.product_id) AS total_orders, p.price
                FROM orders o
                JOIN products p ON o.product_id = p.product_id
                GROUP BY p.product_id
                ORDER BY total_orders DESC
                LIMIT 1
            """)
            p = cursor.fetchone()
            if p:
                reply = f"🔥 Our most popular product is **{p['product_name']}**, ordered {p['total_orders']} times. Price: {p['price']} PKR."
            else:
                reply = "We’re still collecting data to determine our best sellers."

        # ------------------------------------------------------------
        # 5️⃣ CHEAPEST / AFFORDABLE PRODUCTS
        # ------------------------------------------------------------
        elif any(kw in message for kw in ["cheapest", "low price", "budget", "under", "affordable", "lowest price"]):
            match = re.search(r"under\s*(\d+)", message)
            if match:
                limit = int(match.group(1))
                cursor.execute("SELECT product_name, price FROM products WHERE price <= %s ORDER BY price ASC LIMIT 3", (limit,))
            else:
                cursor.execute("SELECT product_name, price FROM products ORDER BY price ASC LIMIT 3")
            products = cursor.fetchall()
            if products:
                reply = "💸 Here are some affordable options:\n" + "\n".join(
                    [f"• {p['product_name']} — {p['price']} PKR" for p in products]
                )
            else:
                reply = "😔 No products found under that price range."

        # ------------------------------------------------------------
        # 6️⃣ DISCOUNTS / PROMOTIONS
        # ------------------------------------------------------------
        elif any(kw in message for kw in ["discount", "sale", "offer", "promo", "voucher", "coupon"]):
            reply = (
                "🎉 We regularly run discounts and sales! "
                "Check our homepage or banners for current promotions."
            )


        # ------------------------------------------------------------
# 7️⃣ SMART PRODUCT COMPARISON (Final optimized version for partial names)
# ------------------------------------------------------------

        elif "difference" in message or "compare" in message:
            cursor.execute("SELECT product_id, product_name, description, price, stock_quantity FROM products")
            products = cursor.fetchall()

            def normalize(s):
                return re.sub(r'[^a-z0-9\s]', '', s.lower().strip())

            msg_norm = normalize(message)
            msg_tokens = set(msg_norm.split())

            from difflib import SequenceMatcher

            def smart_match_score(prod_name):
                """Compute a hybrid match score that works for partial names."""
                name_norm = normalize(prod_name)
                name_tokens = set(name_norm.split())

                # Token overlap score
                overlap = len(msg_tokens & name_tokens) / max(len(msg_tokens), 1)

                # Partial substring score
                partial = 1.0 if msg_norm in name_norm or name_norm in msg_norm else 0
                if partial == 0:
                    # Try sliding substring (partial match anywhere)
                    for token in msg_tokens:
                        if token in name_norm:
                            partial = max(partial, 0.8)

                # Fuzzy match score (sequence similarity)
                fuzzy = SequenceMatcher(None, msg_norm, name_norm).ratio()

                # If message tokens all exist in product tokens, strong boost
                all_match = 1.0 if msg_tokens.issubset(name_tokens) else 0

                # Weighted hybrid score
                return 0.4 * fuzzy + 0.3 * overlap + 0.2 * partial + 0.1 * all_match

            # Score all products
            scored = [(smart_match_score(p["product_name"]), p) for p in products]
            scored.sort(key=lambda x: x[0], reverse=True)

            # Pick top 2 distinct products
            matched = []
            for score, p in scored:
                if p not in matched:
                    matched.append(p)
                if len(matched) >= 2:
                    break

            # 🧾 Build reply
            if len(matched) >= 2:
                p1, p2 = matched[0], matched[1]

                try:
                    price1 = float(p1["price"])
                    price2 = float(p2["price"])
                    if price1 == price2:
                        price_diff_text = "Both products are priced the same."
                    else:
                        higher = p1 if price1 > price2 else p2
                        diff = abs(price1 - price2)
                        price_diff_text = f"{higher['product_name']} is more expensive by {diff:.2f} PKR."
                except Exception:
                    price_diff_text = ""

                desc1 = (p1["description"] or "").strip()
                desc2 = (p2["description"] or "").strip()

                reply = (
                    f"🆚 <b>Product Comparison</b>\n\n"
                    f"1️⃣ <b>{p1['product_name']}</b>\n"
                    f"   • Price: {float(p1['price']):.2f} PKR\n"
                    f"   • Stock: {'In stock' if p1.get('stock_quantity', 0) > 0 else 'Out of stock'}\n"
                    f"   • Info: {desc1[:160]}{'...' if len(desc1) > 160 else ''}\n\n"
                    f"2️⃣ <b>{p2['product_name']}</b>\n"
                    f"   • Price: {float(p2['price']):.2f} PKR\n"
                    f"   • Stock: {'In stock' if p2.get('stock_quantity', 0) > 0 else 'Out of stock'}\n"
                    f"   • Info: {desc2[:160]}{'...' if len(desc2) > 160 else ''}\n\n"
                    f"💡 {price_diff_text}\n"
                    f"🔎 Would you like a more detailed feature comparison or help choosing which is better value?"
                )
            else:
                reply = (
                    "I couldn't confidently identify two products to compare from your message. "
                    "Please mention both names clearly (e.g., “Compare Men Tan Formal Brogue and Regular Fullsleeve Jacket Dark Blue”)."
                )


        # ------------------------------------------------------------
        # 8️⃣ ORDERS / TRACKING (Login required)
        # ------------------------------------------------------------
        elif any(kw in message for kw in ["my order", "track my order", "where is my order", "order status", "last order"]):
            if not customer_id:
                reply = '🔒 Please log in to view your order history. <a href="login.html" class="chat-link">Login here</a>'

            else:
                cursor.execute("""
                               SELECT 
                               o.order_id,
                                o.order_status,
                                o.total_amount,
                                o.quantity,
                                o.order_date,
                                p.product_name
                                FROM orders o
                                JOIN products p ON o.product_id = p.product_id
                                WHERE o.customer_id = %s
                                ORDER BY o.order_date DESC
                                LIMIT 5
                               """, (customer_id,))
                orders = cursor.fetchall()

                if orders:
                    reply = "📦 Your recent orders:\n" + "\n".join(
    [f"• {o['product_name']} — {o['order_status']} ({o['total_amount']} PKR)" for o in orders]
)

                else:
                    reply = "🕐 You haven’t placed any orders yet."

        # ------------------------------------------------------------
        # 9️⃣ PAYMENT & SHIPPING
        # ------------------------------------------------------------
        elif any(kw in message for kw in ["payment", "jazzcash", "easypaisa", "cod", "cash on delivery"]):
            reply = (
                "💳 You can pay using Cash on Delivery (COD), EasyPaisa, JazzCash, or Credit/Debit Card."
            )
        elif any(kw in message for kw in ["shipping", "delivery", "how long", "courier", "ship"]):
            reply = (
                "🚚 Delivery usually takes 3–5 working days depending on your location."
            )

        # ------------------------------------------------------------
        # 🔟 DEFAULT RESPONSE
        # ------------------------------------------------------------
        else:
            reply = (
                "🤖 I'm your VibeHive shopping assistant!\n"
                "You can ask me about:\n"
                "• Product availability (e.g., 'Do you have Men Tan Formal Brogue?')\n"
                "• Price details ('What’s the price of...')\n"
                "• Best sellers ('What are your most popular items?')\n"
                "• Orders ('Where is my last order?')\n"
                "• Payments ('Do you accept JazzCash?')\n"
                "• Discounts ('Any sale today?')"
            )

    except Exception as e:
        print("Chatbot error:", e)
        reply = "⚠️ Sorry, something went wrong while processing your question."
    finally:
        cursor.close()
        conn.close()

    return jsonify({"reply": reply})


@app.route('/api/featured', methods=['GET'])
def get_featured_products():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            p.main_category,
            p.product_id,
            p.product_name,
            p.price,
            p.image_path,
            SUM(o.quantity) AS total_sold
        FROM products p
        JOIN orders o ON p.product_id = o.product_id
        WHERE o.order_status = 'Completed'
        GROUP BY p.main_category, p.product_id, p.product_name, p.price, p.image_path
        ORDER BY p.main_category, total_sold DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    featured = {}
    for row in rows:
        category = row['main_category']
        if category not in featured:
            featured[category] = row
    cursor.close()
    conn.close()
    return jsonify(list(featured.values()))


# ---------------- CONTACT FORM ----------------
@app.route('/contact', methods=['POST'])
def contact_form():
    data = request.json or request.form
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    if not (name and email and message):
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400

    try:
        msg = Message(
            subject=f"New Contact Form Message from {name}",
            recipients=[app.config['MAIL_USERNAME']],  # send to your own inbox
            body=f"""
You received a new contact form message:

Name: {name}
Email: {email}
Message:
{message}
"""
        )
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Message sent successfully!'}), 200

    except Exception as e:
        print("❌ Email send error:", e)
        return jsonify({'success': False, 'error': 'Failed to send message. Try again later.'}), 500

@app.route('/product/<int:product_id>', methods=['GET'])
def get_single_product(product_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()

    conn.close()

    if product:
        return jsonify(product)
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/price-alert', methods=['POST'])
def price_alert():
    data = request.json
    product_id = data.get('product_id')
    email = data.get('email')
    demand_price = data.get('demand_price')

    if not (product_id and email and demand_price):
        return jsonify({"success": False, "message": "Missing data"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO price_alerts (product_id, email, demand_price)
        VALUES (%s, %s, %s)
    """, (product_id, email, demand_price))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"success": True, "message": "Alert saved!"})


from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

def check_price_alerts():
    with app.app_context():   # ✅ FIX: Enable Flask app context
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT pa.id, pa.email, pa.demand_price, p.product_name, p.price
            FROM price_alerts pa
            JOIN products p ON pa.product_id = p.product_id
            WHERE pa.notified = 0
        """)
        alerts = cur.fetchall()

        for alert in alerts:
            alert_id, email, demand_price, product_name, current_price = alert

            if float(current_price) <= float(demand_price):
                msg = Message(
                    subject=f"Price Drop Alert for {product_name}",
                    recipients=[email]
                )
                msg.body = f"""
Good news!

The price for "{product_name}" has dropped.

Current Price: Rs {current_price}
Your Expected Price: Rs {demand_price}

Visit VibeHive to buy now!
                """

                mail.send(msg)

                cur.execute("UPDATE price_alerts SET notified = 1 WHERE id = %s", (alert_id,))
                conn.commit()

        cur.close()
        conn.close()

scheduler.add_job(check_price_alerts, 'interval', seconds=10)

# ---------------- Customer Demands ----------------
@app.route('/customer_demands', methods=['GET'])
def customer_demands():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch product-wise demand stats
    cur.execute("""
        SELECT 
            pa.product_id,
            p.product_name,
            p.price AS current_price,
            COUNT(pa.id) AS total_demands,
            AVG(pa.demand_price) AS avg_demand_price,
            MIN(pa.demand_price) AS min_demand_price,
            MAX(pa.demand_price) AS max_demand_price
        FROM price_alerts pa
        JOIN products p ON pa.product_id = p.product_id
        GROUP BY pa.product_id;
    """)
    products = cur.fetchall()

    # Fetch detailed list
    cur.execute("""
        SELECT 
            pa.product_id,
            pa.email,
            pa.demand_price
        FROM price_alerts pa
        ORDER BY pa.product_id;
    """)
    details = cur.fetchall()

    # Convert to map and add calculations
    result = []
    for p in products:
        product_details = [d for d in details if d["product_id"] == p["product_id"]]

        avg_demand = p["avg_demand_price"] or 0
        current_price = p["current_price"]

        # Calculate price difference %
        price_diff_abs = avg_demand - current_price
        price_diff_percentage = (price_diff_abs / current_price) * 100 if current_price else 0

        # Demand % (Smart popularity indicator)
        demand_percentage = min(100, p["total_demands"] * 5)  
        # (Example: every demand = +5% popularity)

        result.append({
            **p,
            "details": product_details,
            "avg_demand_price": round(avg_demand, 2),
            "min_demand_price": p["min_demand_price"],
            "max_demand_price": p["max_demand_price"],
            "demand_percentage": round(demand_percentage),
            "price_diff_abs": round(price_diff_abs, 2),
            "price_diff_percentage": round(price_diff_percentage, 2)
        })

    return jsonify(result)


# @app.route('/product.html')
# def product_page():
#     return render_template("product.html")

@app.route('/search', methods=["GET"])
def search_products():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    # Convert words to prefix search
    search_terms = " ".join(word + "*" for word in query.split())

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT product_id, product_name, price, stock_quantity, image_path
        FROM products
        WHERE MATCH(product_name, description)
        AGAINST (%s IN BOOLEAN MODE)
        LIMIT 10
    """, (search_terms,))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(results)

@app.route('/wishlist', methods=['GET'])
def get_wishlist():
    customer_id = request.args.get('customer_id')

    if not customer_id:
        return jsonify({"error": "Customer ID is required"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.price,
            p.image_path,
            p.stock_quantity
        FROM wishlist w
        JOIN products p ON w.product_id = p.product_id
        WHERE w.customer_id = %s
        ORDER BY w.added_at DESC
    """

    cursor.execute(query, (customer_id,))
    wishlist = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(wishlist), 200

@app.route('/wishlist/add', methods=['POST'])
def add_to_wishlist():
    data = request.get_json()

    # ❌ If no JSON
    if not data:
        return jsonify({"error": "No data received"}), 400

    customer_id = data.get('customer_id')
    product_id = data.get('product_id')

    # ❌ Missing values
    if not customer_id or not product_id:
        return jsonify({"error": "Missing customer_id or product_id"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # ✅ Check duplicate
    cursor.execute("""
        SELECT 1 FROM wishlist
        WHERE customer_id = %s AND product_id = %s
    """, (customer_id, product_id))

    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Already in wishlist"}), 200

    # ✅ Insert
    cursor.execute("""
        INSERT INTO wishlist (customer_id, product_id)
        VALUES (%s, %s)
    """, (customer_id, product_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Added to wishlist"}), 201

@app.route('/wishlist/remove', methods=['POST'])
def remove_from_wishlist():
    data = request.json
    customer_id = data.get("customer_id")
    product_id = data.get("product_id")

    if not customer_id or not product_id:
        return jsonify({"error": "Missing data"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        DELETE FROM wishlist
        WHERE customer_id = %s AND product_id = %s
    """

    cursor.execute(query, (customer_id, product_id))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Removed from wishlist"}), 200

@app.route('/wishlist/check', methods=['GET'])
def check_wishlist():
    customer_id = request.args.get('customer_id')
    product_id = request.args.get('product_id')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 1 FROM wishlist
        WHERE customer_id = %s AND product_id = %s
    """, (customer_id, product_id))

    exists = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({"exists": bool(exists)})


if __name__ == '__main__':
    app.run(debug=True)
