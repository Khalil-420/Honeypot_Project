import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Path to your SQLite database files
HONEY_POT_DB = 'honeypot.db'
LOGS_DB = 'logs.db'


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

# Function to log the vulnerable request in the logs database
def log_vulnerable_request():
    ip_address = request.remote_addr  # Get the IP address of the requester
    endpoint = request.endpoint  # Get the endpoint that was accessed
    request_data = request.get_data(as_text=True)  # Get the request body
    timestamp = request.date  # Get the timestamp of the request

    # Insert the log data into the logs table in the logs database
    conn = get_logs_db()
    cursor = conn.cursor()

    cursor.execute('''INSERT INTO logs (timestamp, ip_address, endpoint, payload_used) 
                      VALUES (?, ?, ?, ?)''', (timestamp, ip_address, endpoint, request_data))

    conn.commit()
    conn.close()

# Before request hook to log the vulnerable requests
@app.before_request
def before_request():
    # Define the vulnerable endpoints you want to log
    vulnerable_endpoints = ['/product/<product_id>/review', '/add_product','/product/<product_id>']

    # Check if the accessed endpoint is vulnerable
    if request.endpoint in vulnerable_endpoints:
        log_vulnerable_request()

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
    review_text = request.form['review']

    conn = get_honeypot_db()
    cursor = conn.cursor()

    cursor.execute('''INSERT INTO reviews (product_id, text) 
    VALUES (?, ?)''', (product_id, review_text))

    conn.commit()
    conn.close()
    return redirect(url_for('product', product_id=product_id))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        # Get form data for product
        name = request.form['name']
        price = request.form['price']
        image = request.files['image']

        # Save the image to the static folder
        image_filename = image.filename
        image.save(os.path.join('static/images', image_filename))

        # Connect to the honeypot database and insert the new product
        conn = get_honeypot_db()
        conn.execute('INSERT INTO products (name, price, image) VALUES (?, ?, ?)', (name, price, image_filename))
        conn.commit()
        conn.close()

        # Redirect to the home page after adding the product
        return redirect(url_for('index'))

    return render_template('add_product.html')

# Initialize the databases (create tables)
create_tables()
add_products()

if __name__ == '__main__':
    app.run(debug=True)
