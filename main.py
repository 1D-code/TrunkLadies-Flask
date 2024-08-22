from flask import Flask, render_template, request, session, g, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
import pymysql
import os
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from datetime import datetime

app = Flask(__name__)

# Configuration
db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_password = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')

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

conn = open_connection()
if conn:
    print("Connection successful!")
else:
    print("Failed to connect.")

mysql = MySQL(app)

@app.route('/')
def home():
    if 'logged_in' in session:
        return redirect(url_for('index_page'))
    else:
        return redirect(url_for('login'))

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
                cursor.close()

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
    session.pop('dp_path', None) # Optionally clear the username
    return redirect(url_for('login'))


@app.route('/dashboard')
def index_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Retrieve user data from the session
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
    
    # Filter orders based on search input
    orders_all = get_orders(customer=customer, from_date=from_date, to_date=to_date, status='all', page=page, per_page=per_page)
    orders_paid = get_orders(customer=customer, from_date=from_date, to_date=to_date, status='paid', page=page, per_page=per_page)
    orders_pending = get_orders(customer=customer, from_date=from_date, to_date=to_date, status='pending', page=page, per_page=per_page)
    orders_overdue = get_orders(customer=customer, from_date=from_date, to_date=to_date, status='overdue', page=page, per_page=per_page)

    # Count total orders for pagination
    total_orders = len(get_orders(customer=customer, from_date=from_date, to_date=to_date, status='all'))
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
            cursor.execute("SELECT * FROM products WHERE code = %s", (brand_code,))
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
    
    #hashed_password = generate_password_hash('pass')
    #cursor.execute("UPDATE w_users SET tl_pass = %s WHERE tl_user = %s", (hashed_password, username))

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
    
    return render_template('create_invoice.html', last_id=last_id,form_data={}, user_name=session.get('name'), dp_path=session.get('dp_path'))


@app.route('/handle_form_error', methods=['POST'])
def handle_form_error():
    data = request.get_json()
    flash(data['message'], 'error')
    return jsonify({'status': 'error'}), 200

@app.route('/add_order', methods=['POST'])
def add_order():
    fullname = session.get('name')
    dp_path = session.get('dp_path')
    
    required_fields = [
        'from-date-picker', 'to-date-picker', 'customer_name', 
        'customer_address_1', 'customer_city', 'customer_postcode', 
        'customer_email', 'customer_province', 'customer_country', 
        'customer_phone', 'layaway-terms', 'months-topay', 
        'payment-method', 'invoice_sub_total', 'invoice_downpayment', 
        'invoice_total'
    ]

    missing_fields = [field for field in required_fields if not request.form.get(field)]
    
    if missing_fields:
        flash('Please fill in all required fields.', 'error')
        return render_template('create_invoice.html', last_id=request.form.get('invoice_id'), form_data=request.form, user_name=fullname, dp_path=dp_path)
    
    # Open database connection
    conn = open_connection()
    if conn is None:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('create_invoice'))

    try:
        with conn.cursor() as cursor:
            # Get form data
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
            monthlypayment = float(request.form.get('invoice_monthly_payment'))
            total = float(request.form.get('invoice_total'))

            # Combine address fields
            full_add = f"{customer_add1}, {customer_city}, {customer_province}, {customer_country}, {post_code}"

            # Determine payment method
            p_method = pay_method_others if pay_method == "Others" else pay_method  
            p_status = 'Pending'
            
            # Check if the customer exists in the customers table
            cursor.execute(
                'SELECT cid FROM customers WHERE cust_email = %s AND customer_contact = %s',
                (customer_email, customer_phone)
            )
            res = cursor.fetchone()

            if res is None:
                # Customer does not exist, insert into customers table
                cursor.execute(
                    'INSERT INTO customers (cust_name, cust_address, cust_email, customer_contact) '
                    'VALUES (%s, %s, %s, %s)',
                    (customer, full_add, customer_email, customer_phone)
                )
                # Get the last inserted customer ID
                customer_id = cursor.lastrowid
            else:
                # Customer exists, retrieve the customer ID
                customer_id = res['cid']
            
            # Insert into orders table
            cursor.execute(
                'INSERT INTO orders (inv_id, pur_date, due_date, cid, lay_away_terms, '
                'months_term, pay_method, total_price, monthly_price, dp, balance, status) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (invid, invdate, invdue, customer_id, lay_terms, months_to_pay, p_method, sub_total, 
                 monthlypayment, downpayment, total, p_status)
            )
            
            # Get brand details
            brand_codes = request.form.getlist('brand_code[]')
            brand_invs = request.form.getlist('brand-inv[]')
            quantities = request.form.getlist('quantity[]')
            product_prices = request.form.getlist('invoice_product_price[]')
            descriptions = request.form.getlist('desc[]')

            # Insert each product into the product_transactions table
            for i in range(len(brand_codes)):
                sub_price = float(product_prices[i]) * float(quantities[i])
                cursor.execute(
                    'INSERT INTO product_transactions (inv_id, code, brand, quantity, description, price, total_price) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (invid, brand_codes[i], brand_invs[i], quantities[i], descriptions[i], product_prices[i], sub_price)
                )
                                    
                # Update the quantity in the products table
                cursor.execute(
                    'UPDATE products SET stock = stock - %s WHERE code = %s',
                    (quantities[i], brand_codes[i])
                )

        # Commit transaction
        conn.commit()
        flash('Your order has been added successfully!', 'success')
    
    except Exception as e:
        conn.rollback()  # Rollback in case of error
        flash(f'Error while adding order: {str(e)}', 'error')
        print(f'Error while adding order: {str(e)}')  # Debug output
    
    finally:
        conn.close()
    
    return redirect(url_for('create_invoice'))



@app.route('/load_invoice', methods=['POST'])
def load_invoice():
    try:
        data = request.get_json()
        inv_id = data.get('inv_id')

        if not inv_id:
            return jsonify({'error': 'Invoice ID is required'}), 400
        
        conn = open_connection()
        if conn is None:
            return jsonify({'error': 'Database connection error'}), 500

        try:
            with conn.cursor() as cur:
                # Query the database for the invoice details
                cur.execute("SELECT * FROM orders WHERE inv_id = %s", (inv_id,))
                invoice = cur.fetchone()

            if invoice:
                # Return invoice data as JSON
                return jsonify({
                    'due_date': invoice.get('due_date', 'Not available'),  # Ensure 'due_date' is a key in the result
                    'balance': invoice.get('balance', 'Not available'),   # Ensure 'balance' is a key in the result
                })
            else:
                return jsonify({'error': 'Invoice not found'}), 404
                
        except Exception as e:
            # Log and return error
            print("Exception occurred:", str(e))
            return jsonify({'error': 'Error retrieving invoice data'}), 500
        
        finally:
            conn.close()  # Ensure connection is closed

    except Exception as e:
        # Print exception for debugging
        print("Exception occurred:", str(e))
        return jsonify({'error': str(e)}), 500

    
    

@app.route('/pay_order', methods=['POST'])
def pay_order():
    
    fullname = session.get('name')
    dp_path = session.get('dp_path')
    
    required_fields = ['pay_penalty']

    missing_fields = [field for field in required_fields if not request.form.get(field)]
    
    if missing_fields:
        flash('Please fill in all required fields.', 'error')
        return render_template('manage_invoice.html', last_id=request.form.get('invoice_id'), form_data=request.form,user_name=fullname, dp_path=dp_path)
    
    else:

    # Handle unsupported media types
        return jsonify({'status': 'error', 'message': 'Unsupported Media Type'}), 415

@app.route('/get_customers', methods=['GET'])
def get_customers():
    try:
        # Get the page and per_page parameters from the request arguments
        page = int(request.args.get('page', 1))  # Default to page 1 if not provided
        per_page = int(request.args.get('per_page', 10))  # Default to 10 results per page

        # Calculate the offset for the SQL query
        offset = (page - 1) * per_page

        conn = open_connection()
        if conn is None:
            return jsonify({'error': 'Database connection error'}), 500

        try:
            with conn.cursor() as cur:
                # Query the database with LIMIT and OFFSET for pagination
                cur.execute("""
                    SELECT cid, cust_name, cust_address, cust_email, customer_contact
                    FROM customers
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
                customers = cur.fetchall()

                # Count total customers for pagination metadata
                cur.execute("SELECT COUNT(*) AS total FROM customers")
                total_customers = cur.fetchone()['total']

            # Check if data is returned
            if not customers:
                return jsonify({'error': 'No data found'}), 404

            # Convert rows to list of dictionaries
            customer_list = [
                {
                    'id': row['cid'],
                    'name': row['cust_name'],
                    'address': row['cust_address'],
                    'email': row['cust_email'],
                    'phone': row['customer_contact']
                }
                for row in customers
            ]

            # Create pagination metadata
            pagination = {
                'page': page,
                'per_page': per_page,
                'total_pages': (total_customers + per_page - 1) // per_page,  # Calculate total pages
                'total_customers': total_customers
            }

            return jsonify({'customers': customer_list, 'pagination': pagination})

        except Exception as e:
            print(f"Database query error: {str(e)}")
            return jsonify({'error': 'Error retrieving customers'}), 500

        finally:
            conn.close()  # Ensure the connection is closed

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_invoice_data', methods=['GET'])
def get_invoice_data():
    try:
        invNum = request.args.get('invoiceNumber')  # Get the inv_id from query parameters

        if not invNum:
            return jsonify({'error': 'Invoice ID is missing'}), 400

        # Open database connection
        conn = open_connection()
        if conn is None:
            return jsonify({'error': 'Database connection error'}), 500

        try:
            with conn.cursor() as cur:
                # Fetch product transaction data using inv_id
                cur.execute("SELECT * FROM product_transactions WHERE inv_id = %s", (invNum,))
                invoice_data = cur.fetchall()

                # Fetch customer data using inv_id
                cur.execute("""
                    SELECT customers.cust_name, customers.cust_address, customers.cust_email 
                    FROM orders 
                    LEFT JOIN customers ON orders.cid = customers.cid 
                    WHERE orders.inv_id = %s
                """, (invNum,))
                customer_data = cur.fetchone()  # Assuming there's only one customer per invoice

            # Check if any invoice data was retrieved
            if not invoice_data:
                return jsonify({'error': 'No data found for this invoice'}), 404

            # Format invoice data for the response
            invoice_list = [
                {
                    'code': row['code'],
                    'brand': row['brand'],
                    'quantity': row['quantity'],
                    'description': row['description'],
                    'price': row['price']
                }
                for row in invoice_data
            ]

            # Check if customer data was retrieved
            if customer_data:
                customer_details = {
                    'cName': customer_data['cust_name'],
                    'cAddress': customer_data['cust_address'],
                    'cEmail': customer_data['cust_email'],
                }
            else:
                customer_details = {}

            return jsonify({
                'invoice_data': invoice_list,
                'inv_id': invNum,
                'customer_data': customer_details
            })

        except Exception as e:
            return jsonify({'error': f'Database query error: {str(e)}'}), 500

        finally:
            conn.close()  # Ensure the connection is closed

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


    
    
       
if __name__ == '__main__':
    app.run(debug=True)
