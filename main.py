from flask import Flask, render_template, request, session, g, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
import pymysql
import os
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__)

# Configuration
load_dotenv()

db_user = os.getenv('CLOUD_SQL_USERNAME')
db_password = os.getenv('CLOUD_SQL_PASSWORD')
db_name = os.getenv('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')

app.secret_key = 'your_secret_key'  # Replace with your actual secret key

# Function to open a database connection
def open_connection():
    unix_socket = f'/cloudsql/{db_connection_name}'
    try:
        return pymysql.connect(
            user=db_user,
            password=db_password,
            unix_socket=unix_socket,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
    except pymysql.MySQLError as e:
        print(f"Database connection error: {e}")
        return None

# Test connection

print(db_user)
print(db_password)
print(db_name)
print(db_connection_name)

conn = open_connection()
if conn:
    print("Connection successful!")
else:
    print("Failed to connect.")

# Routes
@app.route('/')
def home():
    if 'logged_in' in session:
        return redirect(url_for('index_page'))
    else:
        return redirect(url_for('index_page'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index_page'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = open_connection()
        if conn is None:
            flash('Database connection error. Please try again later.', 'danger')
            return render_template('login.html')

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM w_users WHERE tl_user = %s", (username,))
                user = cursor.fetchone()
            
            if user and check_password_hash(user['tl_pass'], password):
                session['logged_in'] = True
                session['username'] = username
                session['name'] = user['tl_name']
                session['dp_path'] = user['profile_pic_path']
                return redirect(url_for('index_page'))
            else:
                flash('Invalid credentials, please try again.', 'danger')
        except pymysql.MySQLError as e:
            flash(f'An error occurred: {str(e)}', 'danger')
        finally:
            conn.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('name', None)
    session.pop('dp_path', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def index_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    fullname = session.get('name')
    dp_path = session.get('dp_path')

    return render_template('index.html', user_name=fullname, dp_path=dp_path)

@app.before_request
def load_user():
    g.fullname = session.get('name')
    g.dpPath = session.get('dp_path')

@app.route('/manage_invoice', methods=['GET', 'POST'])
def manage_invoice():
    fullname = session.get('name')
    dp_path = session.get('dp_path')
    current_date = datetime.now().date()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    customer = request.form.get('customer-tranx', '')
    from_date = request.form.get('from-date-picker', '')
    to_date = request.form.get('to-date-picker', '')
    
    if request.form.get('clear_button'):
        customer = ''
        from_date = ''
        to_date = ''
    
    orders_all = get_orders(customer, from_date, to_date, 'all', page, per_page)
    orders_paid = get_orders(customer, from_date, to_date, 'paid', page, per_page)
    orders_pending = get_orders(customer, from_date, to_date, 'pending', page, per_page)
    orders_overdue = get_orders(customer, from_date, to_date, 'overdue', page, per_page)

    total_orders = len(get_orders(customer, from_date, to_date, 'all'))
    total_pages = (total_orders + per_page - 1) // per_page

    cnt = {
        'total_orders': len(orders_all),
        'paid_orders': len(orders_paid),
        'pending_orders': len(orders_pending),
        'overdue_orders': len(orders_overdue)
    }

    today_date = datetime.today().strftime('%Y-%m-%d')

    return render_template('manage_invoice.html', 
                           orders_all=orders_all, 
                           orders_paid=orders_paid, 
                           orders_pending=orders_pending, 
                           orders_overdue=orders_overdue, 
                           cnt=cnt, 
                           page=page, 
                           per_page=per_page,
                           total_pages=total_pages,
                           search_customer=customer, 
                           search_from_date=from_date,
                           search_to_date=to_date,
                           today_date=today_date,
                           user_name=fullname, 
                           dp_path=dp_path,
                           current_date=current_date)
    
def get_orders(customer='', from_date='', to_date='', status='', page=1, per_page=10):
    query = """
            SELECT orders.*, 
                   CASE
                       WHEN orders.balance = 0 THEN 'paid'
                       WHEN CURDATE() > orders.due_date THEN 'overdue'
                       ELSE 'pending'
                   END AS status,
                   customers.cust_name,
                   customers.cust_email
            FROM orders
            LEFT JOIN customers ON orders.cid = customers.cid
            WHERE 1=1
            """
    
    params = []
    if customer and customer.strip():
        query += " AND customers.cust_name LIKE %s"
        params.append(f'%{customer}%')
    if from_date:
        query += " AND orders.pur_date >= %s"
        params.append(from_date)
    if to_date:
        query += " AND orders.pur_date <= %s"
        params.append(to_date)
    if status and status != 'all':
        query += " AND CASE WHEN orders.balance = 0 THEN 'paid' WHEN CURDATE() > orders.due_date THEN 'overdue' ELSE 'pending' END = %s"
        params.append(status)
    
    query += " LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])
    
    conn = open_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"Query error: {e}")
        results = []
    finally:
        conn.close()
    
    return results

@app.route('/search_by_brand_code', methods=['POST'])
def search_by_brand_code():
    brand_code = request.form.get('brand_code')
    
    if not brand_code:
        return jsonify({'error': 'Brand code is required'}), 400

    conn = open_connection()
    if conn is None:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Products WHERE code = %s", (brand_code,))
            result = cursor.fetchone()
        
        if result:
            return jsonify({
                'brand': result['Brand'],
                'description': result['item_desc'],
                'price': result['Price']
            })
        else:
            return jsonify({'error': 'No data found'}), 404
    except pymysql.MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/search_by_customer', methods=['POST'])
def search_by_customer():
    customer = request.form.get('customer-tranx')
    
    if not customer:
        return jsonify({'error': 'Customer name is required'}), 400

    conn = open_connection()
    if conn is None:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM orders LEFT JOIN customers ON orders.cid = customers.cid WHERE customers.cust_name = %s", (customer,))
            result = cursor.fetchall()
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'No data found'}), 404
    except pymysql.MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/products')
def product_page():
    return "Our Product"

@app.route('/users')
def users_page():
    return "Hello User"

@app.route('/Customer')
def customer_page():
    return "Hi Customer"

@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    conn = open_connection()
    if conn is None:
        flash('Database connection error. Please try again later.', 'danger')
        return redirect(url_for('create_invoice'))
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1;")
            last_id = cursor.fetchone()
            last_id = last_id['id'] if last_id else 0
            last_id += 1
    except pymysql.MySQLError as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        last_id = 1
    finally:
        conn.close()
    
    return render_template('create_invoice.html', last_id=last_id, user_name=session.get('name'), dp_path=session.get('dp_path'))

@app.route('/add_order', methods=['POST'])
def add_order():
    # List of required fields
    required_fields = [
        'from-date-picker', 'to-date-picker', 'customer_name', 
        'customer_address_1', 'customer_city', 'customer_postcode', 
        'customer_email', 'customer_province', 'customer_country', 
        'customer_phone', 'layaway-terms', 'months-topay', 
        'payment-method', 'invoice_sub_total', 'invoice_downpayment', 
        'invoice_total'
    ]
    
    # Check for missing fields
    missing_fields = [field for field in required_fields if not request.form.get(field)]
    
    if missing_fields:
        flash('Please fill in all required fields.', 'error')
        return render_template('create_invoice.html', 
                               last_id=request.form.get('invoice_id'), 
                               form_data=request.form, 
                               user_name=session.get('name'), 
                               dp_path=session.get('dp_path'))
    
    # Open database connection
    conn = open_connection()
    if conn is None:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('create_invoice'))

    try:
        with conn.cursor() as cursor:
            # Extract form data
            invid = request.form.get('invoice_id')
            invdate = request.form.get('from-date-picker')
            invdue = request.form.get('to-date-picker')
            customer = request.form.get('customer_name')
            customer_add1 = request.form.get('customer_address_1')
            customer_city = request.form.get('customer_city')
            post_code = request.form.get('customer_postcode')
            customer_email = request.form.get('customer_email')
            customer_province = request.form.get('customer_province')
            customer_country = request.form.get('customer_country')
            customer_phone = request.form.get('customer_phone')
            lay_terms = request.form.get('layaway-terms')
            months_to_pay = request.form.get('months-topay')
            pay_method = request.form.get('payment-method')
            pay_method_others = request.form.get('other-payment-method')
            sub_total = float(request.form.get('invoice_sub_total'))
            downpayment = float(request.form.get('invoice_downpayment'))
            total = float(request.form.get('invoice_total'))
            
            # Build full address and payment method
            full_add = f"{customer_add1}, {customer_city}, {customer_province}, {customer_country}, {post_code}"
            p_method = pay_method_others if pay_method == "Others" else pay_method  
            p_status = 'Pending'
            
            # Check if customer exists
            cursor.execute(
                'SELECT cid FROM customers WHERE cust_email = %s AND customer_contact = %s',
                (customer_email, customer_phone)
            )
            res = cursor.fetchone()
            
            if res is None:
                # Insert new customer if not exists
                cursor.execute(
                    'INSERT INTO customers (cust_name, cust_address, cust_email, customer_contact) VALUES (%s, %s, %s, %s)',
                    (customer, full_add, customer_email, customer_phone)
                )
                customer_id = cursor.lastrowid
            else:
                customer_id = res['cid']
            
            # Insert order details
            cursor.execute(
                'INSERT INTO orders (inv_id, pur_date, due_date, cid, lay_away_terms, months_term, pay_method, total_price, dp, balance, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (invid, invdate, invdue, customer_id, lay_terms, months_to_pay, p_method, sub_total, downpayment, total, p_status)
            )
            
            # Process order items
            brand_codes = request.form.getlist('brand_code[]')
            brand_invs = request.form.getlist('brand-inv[]')
            quantities = request.form.getlist('quantity[]')
            product_prices = request.form.getlist('invoice_product_price[]')
            descriptions = request.form.getlist('desc[]')
            
            for i in range(len(brand_codes)):
                sub_price = float(product_prices[i]) * float(quantities[i])
                
                # Insert product transaction details
                cursor.execute(
                    'INSERT INTO product_transactions (inv_id, code, brand, quantity, description, price, total_price) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (invid, brand_codes[i], brand_invs[i], quantities[i], descriptions[i], product_prices[i], sub_price)
                )
                
                # Update product stock
                cursor.execute(
                    'UPDATE products SET stock = stock - %s WHERE code = %s',
                    (quantities[i], brand_codes[i])
                )
        
        # Commit the transaction
        conn.commit()
        flash('Your order has been added successfully!', 'success')
    
    except pymysql.MySQLError as e:
        # Rollback in case of error
        conn.rollback()
        flash(f'Error while adding order: {str(e)}', 'error')
        print(f'Error while adding order: {str(e)}')
    
    finally:
        # Close the connection
        conn.close()
    
    return redirect(url_for('create_invoice'))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
