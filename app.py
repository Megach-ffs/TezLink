# app.py

import sqlite3
import os
from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
# Get the secret key from the environment variable
app.secret_key = os.getenv('SECRET_KEY')

# Get admin credentials from environment variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# --- Database Setup and Utilities ---
# This function creates a connection to the SQLite database.
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# This block is run once when the application starts to ensure the
# contact_messages table exists.
with get_db_connection() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            company_name TEXT,
            telegram_username TEXT,
            interest TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active'
        )
    ''')
    conn.commit()

# --- Login Required Decorator ---
def login_required(f):
    """
    A decorator to protect routes that require a logged-in user.
    If the user is not logged in, they are redirected to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Application Routes ---
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            # Retrieve all form data, including the new fields
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            company_name = request.form.get('company_name')
            telegram_username = request.form.get('telegram_username')
            interest = request.form['interest']
            message = request.form['message']

            conn = get_db_connection()
            conn.execute(
                "INSERT INTO contact_messages (name, email, phone, company_name, telegram_username, interest, message) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, email, phone, company_name, telegram_username, interest, message)
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "An error occurred while saving your message.", 500
        finally:
            if conn:
                conn.close()

        return redirect(url_for('home', success=True))

    success_message = request.args.get('success')
    return render_template('home.html', success_message=success_message)

@app.route('/admin')
@login_required
def admin_panel():
    """
    Admin route to display all contact messages from the database.
    This route is now protected by the login_required decorator.
    """
    conn = get_db_connection()
    messages = conn.execute("SELECT * FROM contact_messages").fetchall()
    conn.close()
    return render_template('admin.html', messages=messages)

# --- New CRUD Routes for Admin Panel (now protected) ---
@app.route('/admin/update_status/<int:message_id>', methods=['POST'])
@login_required
def update_status(message_id):
    """
    Route to update the status of a specific contact message.
    This route is now protected by the login_required decorator.
    """
    try:
        new_status = request.form['new_status']
        conn = get_db_connection()
        conn.execute("UPDATE contact_messages SET status = ? WHERE id = ?", (new_status, message_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    """
    Route to delete a specific contact message from the database.
    This route is now protected by the login_required decorator.
    """
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM contact_messages WHERE id = ?", (message_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin_panel'))

# --- Login and Logout Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    """
    # Check if the environment variables are set before trying to use them
    if not all([ADMIN_USERNAME, ADMIN_PASSWORD]):
        return "Admin credentials are not set. Please check your .env file.", 500

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Compare with credentials from environment variables
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Handles user logout by clearing the session.
    """
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
