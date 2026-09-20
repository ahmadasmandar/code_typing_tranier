"""
Automated smoke test for the packaged PyInstaller application.
Verifies execution from an external working directory, endpoint responsiveness,
and externalized data storage.
"""

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.request


def find_free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class PackagedAppSmokeTests(unittest.TestCase):
    """Smoke tests for the compiled PyInstaller binary."""

    @classmethod
    def setUpClass(cls):
        # Locate packaged executable
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.exe_path = os.path.join(repo_root, 'dist', 'app', 'app.exe')
        if not os.path.exists(cls.exe_path):
            raise unittest.SkipTest(f"Packaged executable not found at {cls.exe_path}")

    def setUp(self):
        self.external_work_dir = tempfile.mkdtemp(prefix='ctt_smoke_work_')
        self.external_data_dir = tempfile.mkdtemp(prefix='ctt_smoke_data_')
        self.port = find_free_port()
        self.proc = None

    def tearDown(self):
        if self.proc:
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
            if self.proc.stdout:
                self.proc.stdout.close()
            if self.proc.stderr:
                self.proc.stderr.close()

        if os.path.exists(self.external_work_dir):
            shutil.rmtree(self.external_work_dir, ignore_errors=True)
        if os.path.exists(self.external_data_dir):
            shutil.rmtree(self.external_data_dir, ignore_errors=True)

    def test_packaged_app_execution_and_external_storage(self):
        """Packaged binary runs outside repo, serves HTTP, and writes data to external data dir."""
        env = os.environ.copy()
        env['CODE_TYPING_TRAINER_DATA_DIR'] = self.external_data_dir
        env['CTT_PORT'] = str(self.port)
        env['CTT_HOST'] = '127.0.0.1'

        cmd = [self.exe_path, '--no-browser', '--port', str(self.port)]
        self.proc = subprocess.Popen(
            cmd,
            cwd=self.external_work_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        base_url = f'http://127.0.0.1:{self.port}'

        # Wait for server ready
        ready = False
        start = time.monotonic()
        while time.monotonic() - start < 15.0:
            if self.proc.poll() is not None:
                out, err = self.proc.communicate()
                self.fail(f"Packaged process exited early with code {self.proc.returncode}: {err.decode('utf-8', errors='ignore')}")
            try:
                with urllib.request.urlopen(f'{base_url}/', timeout=1.0) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.3)

        self.assertTrue(ready, "Packaged server did not become responsive within timeout")

        # 1. Verify GET /
        with urllib.request.urlopen(f'{base_url}/') as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode('utf-8')
            self.assertIn('Code Typing Trainer', body)

        # 2. Verify GET /about
        with urllib.request.urlopen(f'{base_url}/about') as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode('utf-8')
            self.assertIn('About', body)

        # 3. Verify GET /api/templates
        with urllib.request.urlopen(f'{base_url}/api/templates') as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertIn('languages', data)

        # 4. Verify POST /save writes to external data dir
        save_req = urllib.request.Request(
            f'{base_url}/save',
            data=json.dumps({'wpm': 88, 'errors': 0, 'backspaces': 1}).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Origin': base_url,
                'Referer': f'{base_url}/',
            },
            method='POST',
        )
        with urllib.request.urlopen(save_req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertEqual(data.get('status'), 'saved')

        # Confirm train_settings.json was created inside external_data_dir
        settings_file = os.path.join(self.external_data_dir, 'train_settings.json')
        self.assertTrue(os.path.exists(settings_file), f"Expected settings file at {settings_file}")
        with open(settings_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            self.assertIn('history', saved_data)
            self.assertEqual(len(saved_data['history']), 1)
            self.assertEqual(saved_data['history'][0]['wpm'], 88)


if __name__ == '__main__':
    unittest.main()
