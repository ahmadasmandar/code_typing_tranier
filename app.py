#!/usr/bin/env python3
"""
Code Typing Trainer - Flask Web Application

A web-based typing trainer focused on practicing programming code rather than plain text.
Provides accurate metrics, error handling, and history tracking for typing practice.

Author: Ahmad Asmandar <ahmad.asmandar@gmx.com>
License: GNU General Public License v3.0 (GPL-3.0)
Version: 1.0.0
Date: 2025-06-22
"""

# Standard library imports
import json
import os
import secrets
import threading
import subprocess
import argparse
import shutil
import sys
from datetime import datetime

# Third-party imports
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for datetime objects.
    
    Extends the standard JSONEncoder to properly serialize datetime objects
    by converting them to string format (YYYY-MM-DD HH:MM).
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M')
        return super().default(obj)


# Initialize Flask application
app = Flask(__name__)

# Generate a secure random secret key for session management
app.secret_key = secrets.token_hex(16)

# Configuration constants
SETTINGS_FILE = 'train_settings.json'  # File to store user settings and history
UPLOAD_FOLDER = os.path.join('static', 'uploads')  # Directory for profile image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed image file extensions

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_settings():
    """
    Load user settings and typing history from the settings file.
    
    If the file doesn't exist or contains invalid JSON, returns an empty dictionary.
    
    Returns:
        dict: User settings and typing history
    """
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}  # Return empty dict if JSON is invalid
    return {}  # Return empty dict if file doesn't exist


def save_settings(settings):
    """
    Save user settings and typing history to the settings file.
    
    Args:
        settings (dict): User settings and typing history to save
    """
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)  # Save with pretty formatting


def allowed_file(filename):
    """
    Check if a file has an allowed extension for upload.
    
    Args:
        filename (str): The filename to check
        
    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def format_timestamp(timestamp_str):
    """
    Convert various timestamp formats to a standardized YYYY-MM-DD HH:MM format.
    
    Handles ISO format timestamps, timestamps with microseconds, and other formats.
    If conversion fails, returns the original timestamp string.
    
    Args:
        timestamp_str (str): The timestamp string to format
        
    Returns:
        str: Formatted timestamp in YYYY-MM-DD HH:MM format
    """
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
        return timestamp_str  # Return original if formatting fails


@app.route('/')
def index():
    """
    Main route handler for the home page.
    
    Loads user typing history from settings, ensures all history entries have
    properly formatted timestamps, sorts entries by timestamp (newest first),
    and renders the main page template.
    
    Returns:
        rendered template: The main index.html page with typing history
    """
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

    # Debug output (disabled to reduce console noise)
    # print("Sending history to template:", history)

    return render_template('index.html', history=history)


@app.route('/save', methods=['POST'])
def save():
    """
    API endpoint to save typing test results.
    
    Receives typing test results via JSON POST request, creates a new history entry
    with the current timestamp, and saves it to the settings file. Limits history
    to the 20 most recent entries.
    
    Returns:
        JSON response: Confirmation of save with formatted timestamp
    """
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
    """
    API endpoint to clear typing history.
    
    Clears all typing history entries from the settings file.
    
    Returns:
        JSON response: Confirmation of history clearing
    """
    settings = load_settings()
    settings['history'] = []
    save_settings(settings)
    return jsonify({'status': 'cleared'})


@app.route('/about')
def about():
    """
    Route handler for the About page.
    
    Loads profile image information from settings and determines if the user
    is an admin (based on localhost access) for conditional display of admin features.
    
    Returns:
        rendered template: The about.html page with profile image and admin status
    """
    settings = load_settings()
    profile_image = settings.get('profile_image', None)
    # Simple admin check - you can implement a more secure method if needed
    is_admin = request.remote_addr == '127.0.0.1'
    return render_template('about.html', profile_image=profile_image, is_admin=is_admin)


@app.route('/upload_image', methods=['POST'])
def upload_image():
    """
    Route handler for profile image uploads.
    
    Allows admin users (localhost only) to upload a profile image for the About page.
    Validates the uploaded file, saves it with a secure filename, and updates settings.
    
    Returns:
        redirect: Redirects back to the About page after processing
    """
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


def resolve_browser_path(browser_choice: str):
    """
    Resolve the executable path for the requested browser on Windows.
    Supports 'firefox' and 'edge'. Returns (exe_path, args_for_new_window).
    """
    url_flag = []
    if browser_choice == 'firefox':
        candidates = [
            r"C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            r"C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe",
            shutil.which('firefox')
        ]
        exe = next((c for c in candidates if c and os.path.exists(c)), None)
        return exe, ['-new-window']
    elif browser_choice == 'edge':
        candidates = [
            r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
            r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            shutil.which('msedge')
        ]
        exe = next((c for c in candidates if c and os.path.exists(c)), None)
        return exe, ['--new-window']
    return None, []


def open_browser_and_watch(browser_choice: str, url: str = 'http://127.0.0.1:5000'):
    """
    Launch the chosen browser in a NEW WINDOW to the given URL and watch the process.
    When the browser process exits, terminate the Flask app.
    """
    exe, win_args = resolve_browser_path(browser_choice)
    proc = None
    try:
        if exe:
            # Launch specific browser with new-window argument
            cmd = [exe, *win_args, url]
            proc = subprocess.Popen(cmd)
        else:
            # Fall back to system default browser new window when possible
            import webbrowser
            webbrowser.open_new(url)
    except Exception:
        try:
            import webbrowser
            webbrowser.open_new(url)
        except Exception:
            pass

    # Start watcher thread to exit app when browser window closes
    if proc is not None:
        def _watch():
            try:
                proc.wait()
            finally:
                # Force-exit the process to ensure the dev server stops
                os._exit(0)
        t = threading.Thread(target=_watch, daemon=True)
        t.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Code Typing Trainer')
    parser.add_argument('--browser', choices=['firefox', 'edge'], default=None,
                        help='Choose which browser to launch (firefox or edge). If omitted, tries firefox then edge, else default.')
    # Support commands that inject a standalone '--' separator (e.g., some runners)
    forwarded = [a for a in sys.argv[1:] if a != '--']
    args = parser.parse_args(forwarded)

    # Determine browser preference
    chosen = args.browser
    if chosen is None:
        # Auto-detect: prefer firefox, then edge
        if resolve_browser_path('firefox')[0]:
            chosen = 'firefox'
        elif resolve_browser_path('edge')[0]:
            chosen = 'edge'
        else:
            chosen = None  # use default

    # Launch browser after short delay so server is up
    threading.Timer(1.2, lambda: open_browser_and_watch(chosen if chosen else '', 'http://127.0.0.1:5000')).start()

    # Start the Flask development server without reloader to avoid multiple windows
    app.run(debug=True, use_reloader=False)
