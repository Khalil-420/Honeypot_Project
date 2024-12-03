import sqlite3
import os
from datetime import datetime
import base64
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Path to your SQLite database files
HONEY_POT_DB = 'database/honeypot.db'
LOGS_DB = 'database/logs/logs.db'

# Function to get a connection to the honeypot database (for products and login data)
def get_honeypot_db():
    conn = sqlite3.connect(HONEY_POT_DB)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

# Function to get a connection to the logs database (for logging vulnerable requests)
def get_logs_db():
    conn = sqlite3.connect(LOGS_DB)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

# Create tables in both databases
def create_tables():
    # Create tables in honeypot.db
    conn = get_honeypot_db()
    cursor = conn.cursor()

    # Create products table
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price TEXT NOT NULL,
        image TEXT NOT NULL
    )''')

    # Create reviews table
    cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        text TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    conn.commit()
    conn.close()

    # Create tables in logs.db
    conn = get_logs_db()
    cursor = conn.cursor()

    # Create logs table for logging vulnerable requests
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        payload_used TEXT
    )''')

    conn.commit()
    conn.close()

def add_products():
    conn = get_honeypot_db()
    cursor = conn.cursor()
    
    # Check if the products table is empty before adding data
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute('''INSERT INTO products (name, price, image) VALUES ('Honey Jar', '$15.99', 'honey_jar.jpg');''')
        cursor.execute("INSERT INTO products (name, price, image) VALUES ('Honey Free', '$18.99', 'honey_free.jpg');")
        conn.commit()
    
    conn.close()

def log_vulnerable_request():
    ip_address = request.remote_addr  # Get the IP address of the requester
    endpoint = request.path.split()[0]  # The endpoint the user is accessing
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')  # Timestamp in UTC format

    # Initialize request_data as None
    request_data = None

    # Detect SQL injection in URL path (if any)
    if request.method == 'GET' and 'product' in request.path:
        # Check for SQL injection patterns in the URL path
        sql_injection_patterns = ['UNION', 'SELECT', 'DROP', '--', '/*', '*/', 'OR 1=1', 'INSERT']
        for pattern in sql_injection_patterns:
            if pattern in request.path.upper():
                request_data = " ".join(request.path.split()[1:])
                break

    # Handle POST request payload
    if request.method == 'POST' and 'review' in request.path:
        # If the content is form data (standard POST form)
        if request.form:
            form_data = {key: value for key, value in request.form.items()}
            request_data = str(form_data['review'])  # Convert the dictionary to string for logging
            
    elif request.method == 'POST' and 'add_product' in request.path:
        file_data = {}
        
        for file in request.files.values():
            # Read the file content and encode it in base64
            file_content_base64 = base64.b64encode(file.read()).decode('utf-8') 
            
            file_data[file.filename] = file_content_base64
            
            file.seek(0)
        
        # You can log the full data for all files here
        request_data = str(file_data)  # Convert file data to a string

    # If no SQL injection or request data detected in the previous steps, set request_data to 'No vulnerable data'
    if request_data is None:
        request_data = 'No vulnerable data'

    # Insert the log data into the logs table in the logs database
    conn = get_logs_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO logs (timestamp, ip_address, endpoint, payload_used) 
                      VALUES (?, ?, ?, ?)''', (timestamp, ip_address, endpoint, request_data))

    conn.commit()
    conn.close()

    # Optionally, print or return the log in comma-separated format
    log_entry = f"{ip_address}, {timestamp}, {request_data}, {endpoint}"

# Function to validate if the file uploaded is an image
def is_image_file(file):
    if file and '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        return ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
    return False

# Before request hook to log different types of vulnerable requests
@app.before_request
def before_request():
    ip_address = request.remote_addr
    # Check for potential SQL injection attempts in the URL path (e.g., /product/<product_id>)
    if request.path.startswith('/product/') and request.method == 'GET':
        # Get the product_id from the URL path (directly in the URL, not as a query parameter)
        product_id = request.view_args.get('product_id', '')
        
        # Detect common SQL injection patterns such as UNION, SELECT, '--', and other suspicious keywords
        sql_injection_patterns = ['UNION', 'SELECT', 'DROP', '--', '/*', '*/', 'OR 1=1', 'INSERT']
        
        # Check if any of the SQL injection patterns are in the product_id
        if any(pattern in product_id.upper() for pattern in sql_injection_patterns):
            log_vulnerable_request()  # Log the request if a SQL injection pattern is detected

    # Check for potential XSS attempts in /product/<product_id>/review (POST request)
    elif request.path.startswith('/product/') and '/review' in request.path and request.method == 'POST':
        review_text = request.form.get('review', '')
        if '<' in review_text and '>' in review_text:
            log_vulnerable_request()  # Log if there is potential XSS in the review text
            
    elif request.method == 'POST' and 'image' in request.files:
        uploaded_file = request.files['image']
        
        if not is_image_file(uploaded_file):
            log_vulnerable_request()  # Log the request if the uploaded file is not an image

@app.route('/')
def index():
    conn = get_honeypot_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    conn.close()
    return render_template('index.html', products=products)

# Route for viewing a single product's details
@app.route('/product/<product_id>')
def product(product_id):
    conn = get_honeypot_db()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM products WHERE id = {product_id}')
    product = cursor.fetchone()

    cursor.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,))
    reviews = cursor.fetchall()

    conn.close()
    return render_template('product.html', product=product, reviews=reviews)

# Route for adding a review to a product
@app.route('/product/<product_id>/review', methods=['POST'])
def add_review(product_id):
    review_text = request.form.get('review', '')
    conn = get_honeypot_db()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO reviews (product_id, text) VALUES (?, ?)', (product_id, review_text))

    conn.commit()
    conn.close()
    return redirect(url_for('product', product_id=product_id))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        image = request.files['image']

        image_filename = image.filename
        image.save(os.path.join('static/images', image_filename))

        # Connect to the honeypot database and insert the new product
        conn = get_honeypot_db()
        conn.execute('INSERT INTO products (name, price, image) VALUES (?, ?, ?)', (name, price, image_filename))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('add_product.html')

if __name__ == "__main__":
    create_tables()
    add_products()
    app.run()
