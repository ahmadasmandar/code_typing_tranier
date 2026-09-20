"""
Security boundary, CSRF origin verification, loopback handling, and upload validation tests.
"""

import io
import os
import shutil
import tempfile
import unittest

import app


class SecurityBoundaryTests(unittest.TestCase):
    """Test security boundaries, origin validation, and upload constraints."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix='ctt_test_sec_')
        self.orig_data_dir = getattr(app, 'DATA_DIR', None)
        self.orig_templates_dir = getattr(app, 'CODE_TEMPLATES_DIR', None)

        app.init_storage(self.test_dir)
        self.mock_templates_dir = os.path.join(self.test_dir, 'templates')
        os.makedirs(self.mock_templates_dir, exist_ok=True)
        app.CODE_TEMPLATES_DIR = self.mock_templates_dir

        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def tearDown(self):
        if self.orig_data_dir:
            app.init_storage(self.orig_data_dir)
        if self.orig_templates_dir:
            app.CODE_TEMPLATES_DIR = self.orig_templates_dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_is_loopback_address_matrix(self):
        """is_loopback_address correctly handles IPv4, IPv6, hostnames, and remote IPs."""
        # IPv4 loopback
        self.assertTrue(app.is_loopback_address('127.0.0.1'))
        self.assertTrue(app.is_loopback_address('127.0.0.2'))
        self.assertTrue(app.is_loopback_address('127.100.50.1'))

        # IPv6 loopback
        self.assertTrue(app.is_loopback_address('::1'))
        self.assertTrue(app.is_loopback_address('::ffff:127.0.0.1'))
        self.assertTrue(app.is_loopback_address('localhost'))

        # Remote / Non-loopback
        self.assertFalse(app.is_loopback_address('192.168.1.1'))
        self.assertFalse(app.is_loopback_address('10.0.0.5'))
        self.assertFalse(app.is_loopback_address('8.8.8.8'))
        self.assertFalse(app.is_loopback_address('2001:db8::1'))
        self.assertFalse(app.is_loopback_address('evil.attacker.com'))
        self.assertFalse(app.is_loopback_address(''))
        self.assertFalse(app.is_loopback_address(None))

    def test_save_rejects_untrusted_origin(self):
        """POST /save with external Origin header returns 403 Forbidden."""
        payload = {'wpm': 75, 'errors': 2, 'backspaces': 3}
        resp = self.client.post(
            '/save',
            json=payload,
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://attacker-controlled.site.com'},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn('error', resp.get_json())

    def test_save_rejects_untrusted_referer(self):
        """POST /save with external Referer header returns 403 Forbidden."""
        payload = {'wpm': 75, 'errors': 2, 'backspaces': 3}
        resp = self.client.post(
            '/save',
            json=payload,
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Referer': 'https://evil.org/phish'},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn('error', resp.get_json())

    def test_save_accepts_loopback_origin_and_referer(self):
        """POST /save with loopback Origin and Referer returns 200 OK."""
        payload = {'wpm': 82, 'errors': 1, 'backspaces': 2}
        resp = self.client.post(
            '/save',
            json=payload,
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={
                'Origin': 'http://127.0.0.1:5000',
                'Referer': 'http://127.0.0.1:5000/',
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json().get('status'), 'saved')

    def test_clear_rejects_untrusted_origin(self):
        """POST /clear with external Origin returns 403 Forbidden."""
        resp = self.client.post(
            '/clear',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://evil.com'},
        )
        self.assertEqual(resp.status_code, 403)

    def test_clear_rejects_remote_client_even_without_origin(self):
        """POST /clear from remote IP returns 403 Forbidden."""
        resp = self.client.post(
            '/clear',
            environ_base={'REMOTE_ADDR': '192.168.1.50'},
        )
        self.assertEqual(resp.status_code, 403)

    def test_upload_image_rejects_untrusted_origin(self):
        """POST /upload_image with external Origin redirects to /about without saving."""
        data = {'file': (io.BytesIO(b'dummy-image-content'), 'avatar.png')}
        resp = self.client.post(
            '/upload_image',
            data=data,
            content_type='multipart/form-data',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://phishing-site.test'},
        )
        self.assertEqual(resp.status_code, 302)
        settings = app.load_settings()
        self.assertIsNone(settings.get('profile_image'))

    def test_api_upload_template_rejects_untrusted_origin(self):
        """POST /api/upload_template with external Origin returns 403 Forbidden."""
        data = {
            'language': 'python',
            'file': (io.BytesIO(b'print("hello")'), 'hello.py'),
        }
        resp = self.client.post(
            '/api/upload_template',
            data=data,
            content_type='multipart/form-data',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://malicious.org'},
        )
        self.assertEqual(resp.status_code, 403)

    def test_api_upload_template_rejects_disallowed_extension(self):
        """POST /api/upload_template with executable/script extension (.exe, .sh) returns 400."""
        data = {
            'language': 'python',
            'file': (io.BytesIO(b'echo hello'), 'script.sh'),
        }
        resp = self.client.post(
            '/api/upload_template',
            data=data,
            content_type='multipart/form-data',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
            headers={'Origin': 'http://127.0.0.1:5000'},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('unsupported file extension', resp.get_json().get('error', ''))

    def test_api_upload_template_path_traversal_attempts(self):
        """POST /api/upload_template with path traversal patterns is rejected."""
        traversal_attempts = [
            '../../etc',
            '..\\..\\windows',
            'sub/dir',
            'a b',
            'lang;rm',
        ]
        for bad_lang in traversal_attempts:
            data = {
                'language': bad_lang,
                'file': (io.BytesIO(b'int main() {}'), 'main.c'),
            }
            resp = self.client.post(
                '/api/upload_template',
                data=data,
                content_type='multipart/form-data',
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
                headers={'Origin': 'http://127.0.0.1:5000'},
            )
            self.assertEqual(resp.status_code, 400, f"Expected 400 for language '{bad_lang}', got {resp.status_code}")

    def test_ipv6_loopback_allowed_for_admin_actions(self):
        """IPv6 loopback ::1 is recognized as authorized loopback."""
        resp = self.client.post(
            '/clear',
            environ_base={'REMOTE_ADDR': '::1'},
            headers={'Origin': 'http://[::1]:5000'},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json().get('status'), 'cleared')


if __name__ == '__main__':
    unittest.main()
