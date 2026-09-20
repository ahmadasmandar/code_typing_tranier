"""
Baseline route tests for Code Typing Trainer.

Captures initial Phase 0 route contracts and known baseline behavior
prior to Phase 1-6 hardening modifications.
"""

import os
import tempfile
import unittest

import app


class BaselineRouteTests(unittest.TestCase):
    """Regression and baseline contract tests for core Flask routes."""

    def setUp(self):
        """Set up isolated test client and temporary settings file."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_settings_file = os.path.join(self.temp_dir.name, 'test_settings.json')
        self.original_settings_file = app.SETTINGS_FILE
        app.SETTINGS_FILE = self.test_settings_file

        app.app.config['TESTING'] = False  # Allows capturing 500 status codes without raising
        self.client = app.app.test_client()

    def tearDown(self):
        """Restore original settings path and cleanup temporary directory."""
        app.SETTINGS_FILE = self.original_settings_file
        self.temp_dir.cleanup()

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
        response = self.client.get('/api/templates')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertIn('languages', data)
        self.assertIsInstance(data['languages'], list)

    def test_upload_image_remote_redirect(self):
        """POST /upload_image from non-loopback IP redirects (HTTP 302) to /about."""
        response = self.client.post(
            '/upload_image',
            environ_base={'REMOTE_ADDR': '192.168.1.50'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/about'))

    def test_upload_image_local_authorized_baseline_failure(self):
        """
        POST /upload_image from loopback IP (127.0.0.1) documents baseline Finding REL-01.

        In the baseline codebase, the view function ends without a return statement,
        causing Flask to return HTTP 500 (TypeError: view did not return a valid response).
        """
        response = self.client.post(
            '/upload_image',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(response.status_code, 500)

    def test_api_upload_template_remote_forbidden(self):
        """POST /api/upload_template from non-loopback IP returns HTTP 403 Forbidden."""
        response = self.client.post(
            '/api/upload_template',
            environ_base={'REMOTE_ADDR': '10.0.0.1'},
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json(), {'error': 'not authorized'})

    def test_api_upload_template_local_missing_fields(self):
        """POST /api/upload_template from loopback IP without fields returns HTTP 400."""
        response = self.client.post(
            '/api/upload_template',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            data={},
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json(), {'error': 'missing language or file'})

    def test_save_and_clear_history_contract(self):
        """POST /save records test metrics and POST /clear empties history."""
        save_payload = {'wpm': 65, 'errors': 1, 'backspaces': 2}
        save_resp = self.client.post('/save', json=save_payload)
        self.assertEqual(save_resp.status_code, 200)
        save_data = save_resp.get_json()
        self.assertEqual(save_data.get('status'), 'saved')
        self.assertIn('timestamp', save_data)

        clear_resp = self.client.post('/clear')
        self.assertEqual(clear_resp.status_code, 200)
        clear_data = clear_resp.get_json()
        self.assertEqual(clear_data.get('status'), 'cleared')


if __name__ == '__main__':
    unittest.main()
