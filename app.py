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
import math
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
from flask import Flask, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
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

# Process-level reentrant lock for thread-safe settings access
_SETTINGS_LOCK = threading.RLock()

# Allowed image file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Base directory for application code
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
# Optional STM32 HAL project-style source directory to scan as its own language
CORE_SRC_DIR = os.path.join(BASE_DIR, 'Core', 'Src')


def get_data_dir() -> str:
    """
    Get the stable application data directory for user settings and uploads.
    Priority:
    1. CODE_TYPING_TRAINER_DATA_DIR environment variable (if set).
    2. Windows: %APPDATA%/CodeTypingTrainer.
    3. Non-Windows: ~/.local/share/code_typing_trainer or ~/.code_typing_trainer.
    """
    env_dir = os.environ.get('CODE_TYPING_TRAINER_DATA_DIR')
    if env_dir:
        d = os.path.abspath(env_dir)
    elif sys.platform == 'win32':
        appdata = os.environ.get('APPDATA')
        if appdata:
            d = os.path.join(appdata, 'CodeTypingTrainer')
        else:
            d = os.path.join(os.path.expanduser('~'), '.code_typing_trainer')
    else:
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
            d = os.path.join(xdg_data, 'code_typing_trainer')
        else:
            d = os.path.join(os.path.expanduser('~'), '.local', 'share', 'code_typing_trainer')

    os.makedirs(d, exist_ok=True)
    return d


def init_storage(data_dir: str = None):
    """
    Initialize storage paths (SETTINGS_FILE, UPLOAD_FOLDER) against data_dir,
    and perform one-time migration of legacy cwd/base_dir files if present.
    """
    global DATA_DIR, SETTINGS_FILE, UPLOAD_FOLDER
    if data_dir is None:
        DATA_DIR = get_data_dir()
    else:
        DATA_DIR = os.path.abspath(data_dir)
        os.makedirs(DATA_DIR, exist_ok=True)

    SETTINGS_FILE = os.path.join(DATA_DIR, 'train_settings.json')
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Legacy settings migration
    legacy_settings = os.path.join(BASE_DIR, 'train_settings.json')
    if os.path.exists(legacy_settings) and not os.path.exists(SETTINGS_FILE):
        try:
            shutil.copy2(legacy_settings, SETTINGS_FILE)
        except Exception as e:
            print(f"Warning: Failed to migrate legacy settings: {e}")

    # Legacy uploads migration
    legacy_uploads = os.path.join(BASE_DIR, 'static', 'uploads')
    if os.path.isdir(legacy_uploads) and os.path.abspath(legacy_uploads) != os.path.abspath(UPLOAD_FOLDER):
        try:
            for item in os.listdir(legacy_uploads):
                s_item = os.path.join(legacy_uploads, item)
                d_item = os.path.join(UPLOAD_FOLDER, item)
                if os.path.isfile(s_item) and not os.path.exists(d_item):
                    shutil.copy2(s_item, d_item)
        except Exception as e:
            print(f"Warning: Failed to migrate legacy uploads: {e}")


# Initialize storage configuration on startup
init_storage()


def load_settings():
    """
    Load user settings and typing history from the settings file safely.
    Uses process-level lock and handles missing, empty, unreadable,
    and corrupted JSON files with safe recovery.

    Returns:
        dict: User settings and typing history
    """
    with _SETTINGS_LOCK:
        if not os.path.exists(SETTINGS_FILE):
            return {}
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {}
                data = json.loads(content)
                if isinstance(data, dict):
                    return data
                return {}
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
            # Safe recovery: backup corrupted file if possible and return empty dict
            try:
                corrupt_backup = f"{SETTINGS_FILE}.corrupt.{int(time.time())}"
                if os.path.exists(SETTINGS_FILE) and not os.path.exists(corrupt_backup):
                    shutil.copy2(SETTINGS_FILE, corrupt_backup)
            except Exception:
                pass
            return {}


def save_settings(settings):
    """
    Save user settings and typing history to the settings file atomically.
    Acquires process lock, writes to a temporary file in the same directory,
    flushes and fsyncs, then replaces destination atomically.

    Args:
        settings (dict): User settings and typing history to save
    """
    with _SETTINGS_LOCK:
        settings_dir = os.path.dirname(os.path.abspath(SETTINGS_FILE))
        os.makedirs(settings_dir, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix='settings_', suffix='.tmp', dir=settings_dir)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, cls=DateTimeEncoder)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, SETTINGS_FILE)
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise


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


def _validate_non_negative_number(val, field_name: str, max_val: float = 10000.0, is_int: bool = False):
    """
    Validate that a value is a finite, non-negative number within bounds.
    Rejects booleans and non-numeric types.
    """
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return False, f"field '{field_name}' must be a number"
    if not math.isfinite(val):
        return False, f"field '{field_name}' must be finite"
    if val < 0 or val > max_val:
        return False, f"field '{field_name}' must be between 0 and {max_val}"
    if is_int and isinstance(val, float) and not val.is_integer():
        return False, f"field '{field_name}' must be an integer"
    return True, None


@app.route('/save', methods=['POST'])
def save():
    """
    API endpoint to save typing test results.

    Receives typing test results via JSON POST request, validates payload
    structure and numeric ranges, creates a new history entry with current timestamp,
    and saves it to the settings file. Limits history to the 20 most recent entries.

    Returns:
        JSON response: Confirmation of save with formatted timestamp (200) or error (400)
    """
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({'error': 'invalid JSON payload'}), 400

    wpm_raw = data.get('wpm', 0)
    valid, err = _validate_non_negative_number(wpm_raw, 'wpm', max_val=2000.0)
    if not valid:
        return jsonify({'error': err}), 400

    errors_raw = data.get('errors', 0)
    valid, err = _validate_non_negative_number(errors_raw, 'errors', max_val=100000.0, is_int=True)
    if not valid:
        return jsonify({'error': err}), 400

    backspaces_raw = data.get('backspaces', 0)
    valid, err = _validate_non_negative_number(backspaces_raw, 'backspaces', max_val=100000.0, is_int=True)
    if not valid:
        return jsonify({'error': err}), 400

    # Normalize numeric values
    wpm = int(wpm_raw) if (isinstance(wpm_raw, int) or (isinstance(wpm_raw, float) and wpm_raw.is_integer())) else round(float(wpm_raw), 1)
    errors = int(errors_raw)
    backspaces = int(backspaces_raw)

    # Create a new entry with current datetime in ISO format
    timestamp = datetime.now().isoformat()
    entry = {
        'wpm': wpm,
        'errors': errors,
        'backspaces': backspaces,
        'timestamp': timestamp,
        'display_timestamp': datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M'),
    }

    with _SETTINGS_LOCK:
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
    with _SETTINGS_LOCK:
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
    # Simple admin check - localhost only
    if request.remote_addr != '127.0.0.1':
        return redirect(url_for('about'))

    if 'file' not in request.files:
        return redirect(url_for('about'))

    file = request.files['file']
    if not file or file.filename == '' or not allowed_file(file.filename):
        return redirect(url_for('about'))

    filename = secure_filename(file.filename)
    if not filename:
        return redirect(url_for('about'))

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    with _SETTINGS_LOCK:
        settings = load_settings()
        settings['profile_image'] = filename
        save_settings(settings)

    return redirect(url_for('about'))


@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    """
    Serve uploaded profile images from the stable application UPLOAD_FOLDER.
    """
    return send_from_directory(UPLOAD_FOLDER, secure_filename(filename))


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

    # Strictly validate language folder name: allow only letters, digits, dash and underscore (1-30 chars)
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,30}", language):
        return jsonify({"error": "invalid language name"}), 400
    safe_lang = secure_filename(language).lower()
    safe_name = secure_filename(upfile.filename)
    if not safe_name:
        return jsonify({"error": "invalid file name"}), 400
    lang_dir = os.path.join(CODE_TEMPLATES_DIR, safe_lang)
    os.makedirs(lang_dir, exist_ok=True)
    dest_path = os.path.join(lang_dir, safe_name)
    try:
        upfile.save(dest_path)
    except Exception as e:
        return jsonify({"error": f"failed to save file: {e}"}), 500

    return jsonify({"status": "ok", "path": f"templates/{safe_lang}/{safe_name}"})


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
