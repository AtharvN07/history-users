from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'user_tracking'
}

# Function to initialize the database (run this once to create the table)
def init_db():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255),
            url TEXT,
            timestamp DATETIME
        )
    ''')
    connection.commit()
    cursor.close()
    connection.close()

@app.route('/track', methods=['POST'])
def track():
    data = request.get_json()
    print("Received tracking data:\n", data)

    current_url = data.get("url")
    session_id = data.get("session_id")
    iso_timestamp = data.get("timestamp")

    # Convert ISO 8601 timestamp to MySQL-compatible format
    try:
        timestamp = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        timestamp = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Check the last URL for the session
    cursor.execute(
        "SELECT url FROM tracking_data WHERE session_id = %s ORDER BY id DESC LIMIT 1",
        (session_id,)
    )
    last_url = cursor.fetchone()
    last_url = last_url[0] if last_url else None

    print("🔍 Last URL:", last_url)
    print("🔍 Current URL:", current_url)

    if current_url and current_url != last_url:
        cursor.execute(
            "INSERT INTO tracking_data (session_id, url, timestamp) VALUES (%s, %s, %s)",
            (session_id, current_url, timestamp)
        )
        connection.commit()
        print("✅ New URL appended.")
    else:
        print("⚠️ Duplicate URL - not appended.")

    cursor.close()
    connection.close()

    return jsonify({"status": "success", "message": "Tracking data saved."})

@app.route('/get-tracking-data', methods=['GET'])
def get_tracking_data():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT session_id, url, timestamp FROM tracking_data ORDER BY id ASC")
    existing_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(existing_data)

# New route to serve the HTML page
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()  # Initialize the database (run only once)
    app.run(debug=True)