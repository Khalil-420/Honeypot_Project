import sqlite3
import os
from datetime import datetime
import base64
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Path to your SQLite database files
SHOB_DB = 'database/shop.db'

# Function to get a connection to the honeypot database (for products and login data)
def get_shop_db():
    conn = sqlite3.connect(SHOB_DB)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

def is_image_file(file):
    if file and '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        return ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
    return False


# Create tables in both databases
def create_tables():
    # Create tables in honeypot.db
    conn = get_shop_db()
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

def add_products():
    conn = get_shop_db()
    cursor = conn.cursor()
    
    # Check if the products table is empty before adding data
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute('''INSERT INTO products (name, price, image) VALUES ('Honey Jar', '$15.99', 'honey_jar.jpg');''')
        cursor.execute("INSERT INTO products (name, price, image) VALUES ('Honey Free', '$18.99', 'honey_free.jpg');")
        conn.commit()
    
    conn.close()


@app.route('/')
def index():
    conn = get_shop_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    conn.close()
    return render_template('index.html', products=products)

# Route for viewing a single product's details
@app.route('/product/<product_id>')
def product(product_id):
    conn = get_shop_db()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM products WHERE id = ?',(product_id))
    product = cursor.fetchone()

    cursor.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,))
    reviews = cursor.fetchall()

    conn.close()
    return render_template('product.html', product=product, reviews=reviews)

# Route for adding a review to a product
@app.route('/product/<product_id>/review', methods=['POST'])
def add_review(product_id):
    review_text = request.form.get('review', '')
    conn = get_shop_db()
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
        if is_image_file(image):
            image_filename = image.filename
            image.save(os.path.join('static/images', image_filename))

            # Connect to the honeypot database and insert the new product
            conn = get_shop_db()
            conn.execute('INSERT INTO products (name, price, image) VALUES (?, ?, ?)', (name, price, image_filename))
            conn.commit()
            conn.close()
        else:
             return render_template('add_product.html',error="A valid image is required") 

        return redirect(url_for('index'))

    return render_template('add_product.html')

if __name__ == "__main__":
    create_tables()
    add_products()
    app.run()
