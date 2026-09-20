"""
Route contract and validation tests for Code Typing Trainer.

Covers Phase 0 baseline contracts and Phase 1 response contracts, validation,
and failure modes for /save, /clear, /upload_image, /api/upload_template,
and template discovery.
"""

import io
import json
import os
import tempfile
import unittest

import app


class RouteContractTests(unittest.TestCase):
    """Regression, contract, and validation tests for all Flask routes."""

    def setUp(self):
        """Set up isolated test client with temporary settings, uploads, and templates directories."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_settings_file = os.path.join(self.temp_dir.name, 'test_settings.json')
        self.test_upload_folder = os.path.join(self.temp_dir.name, 'uploads')
        self.test_templates_dir = os.path.join(self.temp_dir.name, 'templates')

        os.makedirs(self.test_upload_folder, exist_ok=True)
        os.makedirs(self.test_templates_dir, exist_ok=True)

        self.original_settings_file = app.SETTINGS_FILE
        self.original_upload_folder = app.UPLOAD_FOLDER
        self.original_code_templates_dir = app.CODE_TEMPLATES_DIR

        app.SETTINGS_FILE = self.test_settings_file
        app.UPLOAD_FOLDER = self.test_upload_folder
        app.CODE_TEMPLATES_DIR = self.test_templates_dir

        app.app.config['TESTING'] = False
        self.client = app.app.test_client()

    def tearDown(self):
        """Restore original global paths and clean up isolated temporary directory."""
        app.SETTINGS_FILE = self.original_settings_file
        app.UPLOAD_FOLDER = self.original_upload_folder
        app.CODE_TEMPLATES_DIR = self.original_code_templates_dir
        self.temp_dir.cleanup()

    # --- Core Page Route Tests ---

    def test_index_get(self):
        """GET / returns HTTP 200 and renders the main HTML interface."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
        self.assertIn(b'Code Typing Trainer', response.data)

    def test_about_get(self):
        """GET /about returns HTTP 200 and renders the about page."""
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)

    def test_api_templates_get(self):
        """GET /api/templates returns HTTP 200 and a JSON payload with languages list."""
        # Create a sample language snippet in test templates dir
        c_lang_dir = os.path.join(self.test_templates_dir, 'c')
        os.makedirs(c_lang_dir, exist_ok=True)
        with open(os.path.join(c_lang_dir, 'hello.c'), 'w', encoding='utf-8') as f:
            f.write('int main() { return 0; }')

        response = self.client.get('/api/templates')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertIn('languages', data)
        self.assertEqual(len(data['languages']), 1)
        self.assertEqual(data['languages'][0]['name'], 'c')
        self.assertEqual(data['languages'][0]['levels'][0]['snippets'][0]['title'], 'hello.c')

    # --- /save Validation & History Contract Tests ---

    def test_save_valid_payload_integers(self):
        """POST /save with valid integer metrics returns 200 and formatted timestamp."""
        payload = {'wpm': 65, 'errors': 2, 'backspaces': 4}
        response = self.client.post('/save', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get('status'), 'saved')
        self.assertIn('timestamp', data)

        settings = app.load_settings()
        self.assertEqual(len(settings.get('history', [])), 1)
        entry = settings['history'][0]
        self.assertEqual(entry['wpm'], 65)
        self.assertEqual(entry['errors'], 2)
        self.assertEqual(entry['backspaces'], 4)

    def test_save_valid_payload_floats_and_defaults(self):
        """POST /save with valid float WPM and empty defaults returns 200."""
        payload = {'wpm': 82.4}
        response = self.client.post('/save', json=payload)
        self.assertEqual(response.status_code, 200)

        settings = app.load_settings()
        entry = settings['history'][0]
        self.assertEqual(entry['wpm'], 82.4)
        self.assertEqual(entry['errors'], 0)
        self.assertEqual(entry['backspaces'], 0)

    def test_save_malformed_non_json(self):
        """POST /save with non-JSON payload returns HTTP 400."""
        response = self.client.post('/save', data='plain text body', content_type='text/plain')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)
        self.assertIn('error', response.get_json())

    def test_save_malformed_json_array(self):
        """POST /save with JSON array instead of object returns HTTP 400."""
        response = self.client.post('/save', json=[1, 2, 3])
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)

    def test_save_invalid_negative_numeric_values(self):
        """POST /save with negative metrics returns HTTP 400."""
        cases = [
            {'wpm': -10, 'errors': 0, 'backspaces': 0},
            {'wpm': 50, 'errors': -1, 'backspaces': 0},
            {'wpm': 50, 'errors': 0, 'backspaces': -5},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.client.post('/save', json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.get_json())

    def test_save_invalid_boolean_values(self):
        """POST /save with booleans for numeric fields returns HTTP 400."""
        cases = [
            {'wpm': True, 'errors': 0, 'backspaces': 0},
            {'wpm': 50, 'errors': False, 'backspaces': 0},
            {'wpm': 50, 'errors': 0, 'backspaces': True},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.client.post('/save', json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.get_json())

    def test_save_invalid_string_or_non_finite_values(self):
        """POST /save with string or non-finite numbers returns HTTP 400."""
        cases = [
            {'wpm': 'fast'},
            {'wpm': float('inf')},
            {'wpm': float('nan')},
            {'wpm': 999999},  # exceeds max_val
            {'errors': 2.5},   # non-integer error count
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.client.post('/save', json=payload)
                self.assertEqual(response.status_code, 400)

    def test_save_history_retention_and_ordering(self):
        """POST /save caps history at 20 entries and orders them newest first."""
        for i in range(25):
            resp = self.client.post('/save', json={'wpm': i + 1, 'errors': 0, 'backspaces': 0})
            self.assertEqual(resp.status_code, 200)

        settings = app.load_settings()
        history = settings.get('history', [])
        self.assertEqual(len(history), 20)
        self.assertEqual(history[0]['wpm'], 25)  # newest entry
        self.assertEqual(history[-1]['wpm'], 6)  # oldest retained entry

    # --- /clear Route Tests ---

    def test_clear_history(self):
        """POST /clear removes all history entries and returns status cleared."""
        # Seed history
        self.client.post('/save', json={'wpm': 70, 'errors': 1, 'backspaces': 0})
        self.assertEqual(len(app.load_settings().get('history', [])), 1)

        response = self.client.post('/clear')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'cleared'})
        self.assertEqual(len(app.load_settings().get('history', [])), 0)

    def test_save_optional_learning_metrics(self):
        """Optional accuracy, duration, completion, and character fields persist."""
        response = self.client.post('/save', json={
            'wpm': 72,
            'accuracy': 96.5,
            'duration': 12.34,
            'completion': 100,
            'characters': 240,
            'errors': 3,
            'backspaces': 2,
        })
        self.assertEqual(response.status_code, 200)
        entry = app.load_settings()['history'][0]
        self.assertEqual(entry['accuracy'], 96.5)
        self.assertEqual(entry['duration'], 12.34)
        self.assertEqual(entry['completion'], 100.0)
        self.assertEqual(entry['characters'], 240)

    def test_export_history_json_and_csv(self):
        """History export returns supported JSON and CSV formats."""
        self.client.post('/save', json={'wpm': 70, 'errors': 1, 'backspaces': 0})

        json_response = self.client.get('/export_history?format=json')
        self.assertEqual(json_response.status_code, 200)
        self.assertEqual(json_response.mimetype, 'application/json')
        self.assertIn('attachment; filename=typing-history.json', json_response.headers['Content-Disposition'])

        csv_response = self.client.get('/export_history?format=csv')
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response.mimetype, 'text/csv')
        self.assertIn('wpm', csv_response.get_data(as_text=True))

        invalid_response = self.client.get('/export_history?format=xml')
        self.assertEqual(invalid_response.status_code, 400)

    # --- /upload_image Route Tests ---

    def test_upload_image_remote_unauthorized(self):
        """POST /upload_image from remote IP redirects to /about without saving."""
        data = {'file': (io.BytesIO(b'fake image bytes'), 'avatar.png')}
        response = self.client.post(
            '/upload_image',
            environ_base={'REMOTE_ADDR': '192.168.1.100'},
            data=data,
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/about'))
        settings = app.load_settings()
        self.assertNotIn('profile_image', settings)

    def test_upload_image_local_missing_or_empty_file(self):
        """POST /upload_image from loopback with missing/empty file redirects safely."""
        # Case 1: No file in form
        resp1 = self.client.post('/upload_image', environ_base={'REMOTE_ADDR': '127.0.0.1'}, data={})
        self.assertEqual(resp1.status_code, 302)

        # Case 2: Empty filename
        data = {'file': (io.BytesIO(b''), '')}
        resp2 = self.client.post(
            '/upload_image',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            data=data,
            content_type='multipart/form-data',
        )
        self.assertEqual(resp2.status_code, 302)

    def test_upload_image_local_disallowed_extension(self):
        """POST /upload_image from loopback with disallowed extension redirects without saving."""
        data = {'file': (io.BytesIO(b'executable content'), 'malicious.exe')}
        response = self.client.post(
            '/upload_image',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            data=data,
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(os.path.exists(os.path.join(self.test_upload_folder, 'malicious.exe')))
        self.assertNotIn('profile_image', app.load_settings())

    def test_upload_image_local_success(self):
        """POST /upload_image from loopback with valid image saves file and updates settings."""
        data = {'file': (io.BytesIO(b'PNG_RAW_IMAGE_DATA'), 'profile.png')}
        response = self.client.post(
            '/upload_image',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            data=data,
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 302)
        saved_file = os.path.join(self.test_upload_folder, 'profile.png')
        self.assertTrue(os.path.exists(saved_file))
        with open(saved_file, 'rb') as f:
            self.assertEqual(f.read(), b'PNG_RAW_IMAGE_DATA')

        settings = app.load_settings()
        self.assertEqual(settings.get('profile_image'), 'profile.png')

        image_response = self.client.get('/static/uploads/profile.png')
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response.data, b'PNG_RAW_IMAGE_DATA')
        image_response.close()

    # --- /api/upload_template Route Tests ---

    def test_api_upload_template_remote_forbidden(self):
        """POST /api/upload_template from remote IP returns 403 Forbidden."""
        data = {
            'language': 'python',
            'file': (io.BytesIO(b'print("hello")'), 'test.py'),
        }
        response = self.client.post(
            '/api/upload_template',
            environ_base={'REMOTE_ADDR': '10.0.0.1'},
            data=data,
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {'error': 'not authorized'})

    def test_api_upload_template_missing_fields(self):
        """POST /api/upload_template without required fields returns 400 Bad Request."""
        # Missing file
        resp1 = self.client.post(
            '/api/upload_template',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            data={'language': 'python'},
        )
        self.assertEqual(resp1.status_code, 400)
        self.assertEqual(resp1.get_json(), {'error': 'missing language or file'})

        # Missing language
        resp2 = self.client.post(
            '/api/upload_template',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            data={'file': (io.BytesIO(b'code'), 'test.py')},
            content_type='multipart/form-data',
        )
        self.assertEqual(resp2.status_code, 400)
        self.assertEqual(resp2.get_json(), {'error': 'missing language or file'})

    def test_api_upload_template_invalid_language_name(self):
        """POST /api/upload_template with invalid/traversal language folder returns 400."""
        invalid_langs = ['../c', 'c/sub', 'c@lang!', 'a' * 35]
        for lang in invalid_langs:
            with self.subTest(lang=lang):
                data = {
                    'language': lang,
                    'file': (io.BytesIO(b'code'), 'snippet.c'),
                }
                resp = self.client.post(
                    '/api/upload_template',
                    environ_base={'REMOTE_ADDR': '127.0.0.1'},
                    data=data,
                    content_type='multipart/form-data',
                )
                self.assertEqual(resp.status_code, 400)
                self.assertEqual(resp.get_json(), {'error': 'invalid language name'})

    def test_api_upload_template_success(self):
        """POST /api/upload_template with valid language and file saves snippet and returns 200."""
        data = {
            'language': 'python',
            'file': (io.BytesIO(b'def hello():\n    return "world"\n'), 'sample.py'),
        }
        response = self.client.post(
            '/api/upload_template',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            data=data,
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.get_json()
        self.assertEqual(res_json.get('status'), 'ok')
        self.assertEqual(res_json.get('path'), 'templates/python/sample.py')

        saved_path = os.path.join(self.test_templates_dir, 'python', 'sample.py')
        self.assertTrue(os.path.exists(saved_path))
        with open(saved_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), 'def hello():\n    return "world"\n')


if __name__ == '__main__':
    unittest.main()
