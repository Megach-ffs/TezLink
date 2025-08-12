
# app.py

import sqlite3
from flask import Flask, request, render_template, redirect, url_for

# Initialize the Flask application
app = Flask(__name__)

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
            interest TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')
    conn.commit()

# --- Application Routes ---
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            interest = request.form['interest']
            message = request.form['message']

            conn = get_db_connection()
            conn.execute(
                "INSERT INTO contact_messages (name, email, interest, message) VALUES (?, ?, ?, ?)",
                (name, email, interest, message)
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "An error occurred while saving your message.", 500
        finally:
            if conn:
                conn.close()

        # Redirect back to the home page with a query parameter
        return redirect(url_for('home', success=True))

    # If it's a GET request, render the home.html template
    success_message = request.args.get('success')
    return render_template('home.html', success_message=success_message)

@app.route('/admin')
def admin_panel():
    """
    Admin route to display all contact messages from the database.
    """
    conn = get_db_connection()
    # Query all records from the contact_messages table
    messages = conn.execute("SELECT * FROM contact_messages").fetchall()
    conn.close()
    # Render the new admin.html template, passing the messages to it
    return render_template('admin.html', messages=messages)


if __name__ == '__main__':
    app.run(debug=True)

