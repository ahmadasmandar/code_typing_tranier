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

import argparse

# Standard library imports
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime

# Third-party imports
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename


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

# Base directory for on-disk code templates (organized as templates/<language>/*.ext)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
# Optional STM32 HAL project-style source directory to scan as its own language
CORE_SRC_DIR = os.path.join(BASE_DIR, 'Core', 'Src')


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


def _read_text_file(path: str) -> str:
    """Read a text file safely as UTF-8, ignoring errors."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Failed to read template file {path}: {e}")
        return ''


def _strip_comments(lang: str, fname: str, code: str) -> str:
    """
    Remove comments from code for typing practice. Heuristics per language:
    - C/C++/Java/JS/TS/Go: remove /* ... */ and // ... end-of-line
    - Python: remove triple-quoted blocks (docstrings) and # ... end-of-line
    - VHDL: remove -- ... end-of-line
    - HTML: remove <!-- ... -->
    Falls back to returning original code on regex errors.
    """
    try:
        ext = os.path.splitext(fname)[1].lower()
        text = code

        def strip_c_like(txt: str) -> str:
            txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.DOTALL)
            txt = re.sub(r"//.*?$", "", txt, flags=re.MULTILINE)
            return txt

        if ext in {'.c', '.h', '.hpp', '.cpp', '.cc', '.java', '.js', '.ts', '.go'} or lang in {
            'c',
            'cpp',
            'java',
            'javascript',
            'typescript',
            'go',
            'stm32',
        }:
            text = strip_c_like(text)
        elif ext == '.py' or lang == 'python':
            # Triple-quoted strings (often used as comments/docstrings)
            text = re.sub(r"'''[\s\S]*?'''", "", text)
            text = re.sub(r'"""[\s\S]*?"""', "", text)
            text = re.sub(r"#.*?$", "", text, flags=re.MULTILINE)
        elif ext in {'.vhd', '.vhdl'} or lang == 'vhdl':
            text = re.sub(r"--.*?$", "", text, flags=re.MULTILINE)
        elif ext in {'.html', '.htm'} or lang in {'html'}:
            text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        else:
            # Reasonable default: try C-like then Python hashes
            after = strip_c_like(text)
            after = re.sub(r"#.*?$", "", after, flags=re.MULTILINE)
            text = after

        # Normalize multiple blank lines created by stripping
        lines = [ln.rstrip() for ln in text.splitlines()]
        # Remove lines that are empty after stripping trailing spaces
        return "\n".join(ln for ln in lines)
    except Exception:
        return code


def scan_code_templates():
    """
    Scan templates directory for language subfolders and files.

    Expected layout:
      templates/<language>/*.ext

    Returns structure compatible with the frontend picker:
    {
      "languages": [
        {"name": "c", "levels": [{"level": "files", "snippets": [{"title": "main.c", "code": "..."}]}]},
        ...
      ]
    }
    """
    result = {"languages": []}
    if not os.path.isdir(CODE_TEMPLATES_DIR):
        return result

    try:
        for entry in os.listdir(CODE_TEMPLATES_DIR):
            lang_path = os.path.join(CODE_TEMPLATES_DIR, entry)
            if not os.path.isdir(lang_path):
                # ignore files at root like index.html/about.html
                continue
            snippets = []
            try:
                for fname in os.listdir(lang_path):
                    fpath = os.path.join(lang_path, fname)
                    if os.path.isfile(fpath):
                        code = _read_text_file(fpath)
                        snippets.append({"title": fname, "code": code})
            except Exception as e:
                print(f"Error scanning language folder {lang_path}: {e}")
            result["languages"].append({"name": entry, "levels": [{"level": "files", "snippets": snippets}]})

        # Note: intentionally ignoring Core/Src; Core is reserved for local generation only
    except Exception as e:
        print(f"Error scanning templates dir {CODE_TEMPLATES_DIR}: {e}")
    return result


@app.route('/api/templates', methods=['GET'])
def api_templates():
    """Return discovered code templates from the filesystem."""
    data = scan_code_templates()
    return jsonify(data)


@app.route('/api/upload_template', methods=['POST'])
def api_upload_template():
    """
    Upload a code template file into templates/<language>/.

    Form fields:
      language: name of subfolder to store under (e.g., "c", "python").
      file: the uploaded code file (e.g., main.c, main.py).
    """
    # Only allow local admin uploads similar to image upload policy
    if request.remote_addr != '127.0.0.1':
        return jsonify({"error": "not authorized"}), 403

    language = request.form.get('language', '').strip()
    upfile = request.files.get('file')
    if not language or not upfile or upfile.filename == '':
        return jsonify({"error": "missing language or file"}), 400

    # Sanitize language and filename
    safe_lang = secure_filename(language)
    safe_name = secure_filename(upfile.filename)
    lang_dir = os.path.join(CODE_TEMPLATES_DIR, safe_lang)
    os.makedirs(lang_dir, exist_ok=True)
    dest_path = os.path.join(lang_dir, safe_name)
    try:
        upfile.save(dest_path)
    except Exception as e:
        return jsonify({"error": f"failed to save file: {e}"}), 500

    return jsonify({"status": "ok", "path": f"templates/{safe_lang}/{safe_name}"})

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
    if browser_choice == 'chromium':
        # Prefer a bundled portable Chromium launcher within the project, if present
        base_dir = os.path.dirname(os.path.abspath(__file__))
        portable_chromium = os.path.join(base_dir, 'Chromium', 'chrome.exe')
        if os.path.exists(portable_chromium):
            # ChromiumPortable.exe accepts the URL directly
            return portable_chromium, []
        # Fallback: try common chromium executables if available (edge/chrome)
        candidates = [
            shutil.which('chromium'),
            shutil.which('chrome'),
            shutil.which('google-chrome'),
            shutil.which('msedge'),
        ]
        exe = next((c for c in candidates if c and os.path.exists(c)), None)
        return exe, ['--new-window']
    if browser_choice == 'firefox':
        # Prefer a bundled portable Firefox launcher within the project, if present
        base_dir = os.path.dirname(os.path.abspath(__file__))
        portable_launcher = os.path.join(base_dir, 'Firefox', 'FirefoxPortable.exe')
        if os.path.exists(portable_launcher):
            # FirefoxPortable.exe accepts the URL directly; no extra window flags
            return portable_launcher, []
        candidates = [
            r"C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            r"C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe",
            shutil.which('firefox'),
        ]
        exe = next((c for c in candidates if c and os.path.exists(c)), None)
        return exe, ['-new-window']
    elif browser_choice == 'edge':
        candidates = [
            r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
            r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            shutil.which('msedge'),
        ]
        exe = next((c for c in candidates if c and os.path.exists(c)), None)
        return exe, ['--new-window']
    return None, []


def open_browser_and_watch(browser_choice: str, url: str = 'http://127.0.0.1:5000', isolated: bool = True):
    """
    Launch the chosen browser in a NEW WINDOW to the given URL and watch the process.
    When the browser process exits, terminate the Flask app.
    """
    exe, win_args = resolve_browser_path(browser_choice)
    proc = None
    start_time = time.monotonic()
    temp_profile_dir = None
    try:
        if exe:
            # Launch specific browser with new-window argument
            iso_args = []
            if isolated and browser_choice == 'firefox':
                # Create isolated profile for Firefox
                temp_profile_dir = tempfile.mkdtemp(prefix='ctt_ff_')
                # --no-remote allows running a separate instance
                iso_args = ['--no-remote', '-profile', temp_profile_dir]
            elif isolated and browser_choice in ('edge', 'chromium'):
                # Create isolated user data dir for Chromium-based browsers
                # Skip adding isolation flags if using a portable launcher that manages its own profile
                if exe and exe.lower().endswith('chromiumportable.exe'):
                    iso_args = []
                else:
                    temp_profile_dir = tempfile.mkdtemp(prefix='ctt_edge_')
                    iso_args = [f'--user-data-dir={temp_profile_dir}', '--no-first-run', '--no-default-browser-check']

            cmd = [exe, *win_args, *iso_args, url]
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
                # Only exit if this dedicated browser process lived long enough
                # to represent the user's dedicated window (avoid immediate delegate cases)
                lifetime = time.monotonic() - start_time
                if lifetime >= 2.0:
                    os._exit(0)
                # Cleanup temp profile directories
                if temp_profile_dir:
                    try:
                        shutil.rmtree(temp_profile_dir, ignore_errors=True)
                    except Exception:
                        pass

        t = threading.Thread(target=_watch, daemon=True)
        t.start()


def wait_for_server(url: str, timeout_seconds: float = 15.0, interval: float = 0.3) -> bool:
    """Poll the given URL until it responds or timeout elapses."""
    end = time.monotonic() + timeout_seconds
    while time.monotonic() < end:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if 200 <= resp.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(interval)
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Code Typing Trainer')
    parser.add_argument(
        '--browser',
        choices=['chromium', 'firefox', 'edge'],
        default=None,
        help='Choose which browser to launch (chromium, firefox, or edge). If omitted, tries chromium, then firefox, then edge.',
    )
    # Support commands that inject a standalone '--' separator (e.g., some runners)
    forwarded = [a for a in sys.argv[1:] if a != '--']
    args = parser.parse_args(forwarded)

    # Determine browser preference
    chosen = args.browser
    if chosen is None:
        # Auto-detect: prefer chromium, then firefox, then edge
        if resolve_browser_path('chromium')[0]:
            chosen = 'chromium'
        elif resolve_browser_path('firefox')[0]:
            chosen = 'firefox'
        elif resolve_browser_path('edge')[0]:
            chosen = 'edge'
        else:
            chosen = None  # use default

    # Launch browser only after server is reachable to avoid connection errors
    def _wait_then_open():
        url = 'http://127.0.0.1:5000'
        wait_for_server(url, timeout_seconds=20.0, interval=0.3)
        open_browser_and_watch(chosen if chosen else '', url)

    threading.Thread(target=_wait_then_open, daemon=True).start()

    # Start the Flask development server without reloader to avoid multiple windows
    app.run(debug=True, use_reloader=False)
