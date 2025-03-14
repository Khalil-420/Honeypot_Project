from flask import Flask, render_template, request, redirect, url_for, session, flash , jsonify
import sqlite3
from werkzeug.security import check_password_hash
app = Flask(__name__)


logs_db = "/app/database/logs.db"
# Secret key for session management
app.secret_key = 'very_secure_secret'

# Function to check if the username and password are correct
def check_user_credentials(username, password):
    # Connect to the SQLite database
    conn = sqlite3.connect('database/users.db')
    cursor = conn.cursor()

    # Query the database for the user
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    conn.close()

    # If user exists, check the password hash
    if user and check_password_hash(user[0], password):
        return True
    return False

def fetch_logs():
    conn = sqlite3.connect(logs_db)  # Ensure this matches the path to your database
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, ip_address, endpoint, payload_used FROM logs")
    rows = cursor.fetchall()
    conn.close()
    return [{"timestamp": row[0], "ip": row[1], "endpoint": row[2], "payload": row[3]} for row in rows]

@app.route("/api/logs")
def get_logs():
    logs = fetch_logs()
    return jsonify(logs)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate credentials against the database
        if check_user_credentials(username, password):
            session['username'] = username 
            return redirect(url_for('dashboard'))  # Redirect to dashboard
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Check if the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login page if not logged in
    
    return render_template('index.html', username=session['username'])  # Pass username to dashboard template

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('login'))  # Redirect to login page after logout

if __name__ == '__main__':
    app.run(debug=True)
