import json
import os
import secrets
import threading
import webbrowser
from datetime import datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M')
        return super().default(obj)


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
SETTINGS_FILE = 'train_settings.json'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def format_timestamp(timestamp_str):
    """Convert various timestamp formats to YYYY-MM-DD HH:MM"""
    try:
        # Handle ISO format with microseconds (e.g., 2025-06-16T12:02:12.899211)
        if 'T' in timestamp_str:
            # Remove microseconds if present
            if '.' in timestamp_str:
                timestamp_str = timestamp_str.split('.')[0]
            dt = datetime.fromisoformat(timestamp_str)
            return dt.strftime('%Y-%m-%d %H:%M')
        # Already in correct format
        elif len(timestamp_str) == 16 and timestamp_str[10] == ' ':
            return timestamp_str
        # Handle other formats
        else:
            dt = datetime.fromisoformat(timestamp_str)
            return dt.strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        print(f"Error formatting timestamp '{timestamp_str}': {e}")
        return timestamp_str


@app.route('/')
def index():
    # Add a link to the about page in the context
    has_about_page = True
    settings = load_settings()
    history = settings.get('history', [])

    # Ensure all history entries have display_timestamp
    for item in history:
        if 'display_timestamp' not in item and 'timestamp' in item:
            timestamp = item['timestamp']
            if isinstance(timestamp, str) and 'T' in timestamp:
                try:
                    # Parse ISO format and format as YYYY-MM-DD HH:MM
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    item['display_timestamp'] = dt.strftime('%Y-%m-%d %H:%M')
                except Exception as e:
                    print(f"Error formatting timestamp {timestamp}: {e}")
                    item['display_timestamp'] = timestamp
            else:
                item['display_timestamp'] = str(timestamp)

    # Sort by timestamp (newest first)
    history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Debug output
    print("Sending history to template:", history)

    return render_template('index.html', history=history)


@app.route('/save', methods=['POST'])
def save():
    data = request.json

    # Create a new entry with current datetime in ISO format
    timestamp = datetime.now().isoformat()
    entry = {
        'wpm': data.get('wpm', 0),
        'errors': data.get('errors', 0),
        'backspaces': data.get('backspaces', 0),
        'timestamp': timestamp,
        'display_timestamp': datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M'),
    }

    settings = load_settings()
    history = settings.get('history', [])

    # Insert new entry at the beginning
    history.insert(0, entry)

    # Keep only the 20 most recent entries
    settings['history'] = history[:20]
    save_settings(settings)

    # Return the formatted timestamp
    return jsonify({'status': 'saved', 'timestamp': entry['display_timestamp']})


@app.route('/clear', methods=['POST'])
def clear_history():
    settings = load_settings()
    settings['history'] = []
    save_settings(settings)
    return jsonify({'status': 'cleared'})


@app.route('/about')
def about():
    settings = load_settings()
    profile_image = settings.get('profile_image', None)
    # Simple admin check - you can implement a more secure method if needed
    is_admin = request.remote_addr == '127.0.0.1'
    return render_template('about.html', profile_image=profile_image, is_admin=is_admin)


@app.route('/upload_image', methods=['POST'])
def upload_image():
    # Simple admin check - you can implement a more secure method if needed
    if request.remote_addr != '127.0.0.1':
        return redirect(url_for('about'))

    if 'profile_image' not in request.files:
        return redirect(url_for('about'))

    file = request.files['profile_image']

    if file.filename == '':
        return redirect(url_for('about'))

    if file and allowed_file(file.filename):
        # Create a secure filename to prevent security issues
        filename = 'profile.' + file.filename.rsplit('.', 1)[1].lower()
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save the file
        file.save(file_path)

        # Update settings
        settings = load_settings()
        settings['profile_image'] = filename
        save_settings(settings)

    return redirect(url_for('about'))


def open_browser():
    firefox_path = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
    try:
        if os.path.exists(firefox_path):
            webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(firefox_path))
            webbrowser.get('firefox').open('http://127.0.0.1:5000')
        else:
            webbrowser.open('http://127.0.0.1:5000')
    except Exception:
        webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    threading.Timer(1.5, open_browser).start()  # Increased delay and use open() instead of open_new()
    app.run(debug=True, use_reloader=False)  # Disable reloader to prevent double opening
