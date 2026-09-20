"""
Persistence, concurrency, and data-directory tests for Code Typing Trainer.

Covers Phase 2 requirements:
- Data directory resolution and environment override (WP-20)
- Stable path resolution for settings and uploads (WP-21)
- Thread-safe locked read-modify-write operations (WP-22)
- Atomic JSON persistence via temporary file and replace (WP-23)
- Error handling, corrupted file backup, and recovery (WP-24)
- Alternate working directories and concurrent saves under multi-threading (WP-25)
"""

import concurrent.futures
import json
import os
import shutil
import tempfile
import unittest

import app


class PersistenceTests(unittest.TestCase):
    """Test suite for settings persistence, data directories, and recovery."""

    def setUp(self):
        """Set up isolated test data directory and environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_dir = os.path.join(self.temp_dir.name, 'data')
        os.makedirs(self.test_data_dir, exist_ok=True)

        self.original_env = os.environ.get('CODE_TYPING_TRAINER_DATA_DIR')
        os.environ['CODE_TYPING_TRAINER_DATA_DIR'] = self.test_data_dir
        app.init_storage(self.test_data_dir)

    def tearDown(self):
        """Restore environment and clean up temporary directory."""
        if self.original_env is not None:
            os.environ['CODE_TYPING_TRAINER_DATA_DIR'] = self.original_env
        else:
            os.environ.pop('CODE_TYPING_TRAINER_DATA_DIR', None)
        app.init_storage()
        self.temp_dir.cleanup()

    def test_data_dir_env_override(self):
        """get_data_dir respects CODE_TYPING_TRAINER_DATA_DIR override."""
        custom_dir = os.path.join(self.temp_dir.name, 'custom_env_dir')
        os.environ['CODE_TYPING_TRAINER_DATA_DIR'] = custom_dir
        try:
            resolved = app.get_data_dir()
            self.assertEqual(os.path.abspath(resolved), os.path.abspath(custom_dir))
            self.assertTrue(os.path.isdir(resolved))
        finally:
            os.environ['CODE_TYPING_TRAINER_DATA_DIR'] = self.test_data_dir

    def test_init_storage_resolves_paths_in_data_dir(self):
        """init_storage configures SETTINGS_FILE and UPLOAD_FOLDER inside data_dir."""
        self.assertTrue(app.SETTINGS_FILE.startswith(os.path.abspath(self.test_data_dir)))
        self.assertTrue(app.UPLOAD_FOLDER.startswith(os.path.abspath(self.test_data_dir)))
        self.assertTrue(os.path.isdir(app.UPLOAD_FOLDER))

    def test_alternate_working_directory(self):
        """Settings load and save succeed when working directory is outside the project."""
        outside_dir = os.path.join(self.temp_dir.name, 'outside_cwd')
        os.makedirs(outside_dir, exist_ok=True)
        old_cwd = os.getcwd()
        try:
            os.chdir(outside_dir)
            # Save from alternate CWD
            app.save_settings({'history': [{'wpm': 100, 'timestamp': '2026-09-20T00:00:00', 'display_timestamp': '2026-09-20 00:00'}]})

            # Load from alternate CWD
            loaded = app.load_settings()
            self.assertEqual(len(loaded.get('history', [])), 1)
            self.assertEqual(loaded['history'][0]['wpm'], 100)

            # Ensure settings file was written to stable data_dir, not outside_dir
            self.assertTrue(os.path.exists(os.path.join(self.test_data_dir, 'train_settings.json')))
            self.assertFalse(os.path.exists(os.path.join(outside_dir, 'train_settings.json')))
        finally:
            os.chdir(old_cwd)

    def test_atomic_write_replaces_cleanly(self):
        """save_settings writes valid JSON and cleans up temporary files."""
        payload = {'history': [{'wpm': 50, 'errors': 1, 'backspaces': 2}]}
        app.save_settings(payload)

        # Confirm destination file contains identical valid JSON
        with open(app.SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data, payload)

        # Confirm no temporary files left in data directory
        temp_files = [f for f in os.listdir(self.test_data_dir) if f.startswith('settings_') and f.endswith('.tmp')]
        self.assertEqual(temp_files, [])

    def test_missing_settings_file_returns_empty_dict(self):
        """load_settings returns empty dict when settings file is absent."""
        if os.path.exists(app.SETTINGS_FILE):
            os.remove(app.SETTINGS_FILE)
        self.assertEqual(app.load_settings(), {})

    def test_empty_settings_file_returns_empty_dict(self):
        """load_settings returns empty dict when settings file is 0 bytes."""
        with open(app.SETTINGS_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        self.assertEqual(app.load_settings(), {})

    def test_corrupted_settings_file_recovery_and_backup(self):
        """load_settings recovers from corrupted JSON and writes a .corrupt backup."""
        corrupt_content = '{"history": [ invalid json payload...'
        with open(app.SETTINGS_FILE, 'w', encoding='utf-8') as f:
            f.write(corrupt_content)

        recovered = app.load_settings()
        self.assertEqual(recovered, {})

        # Check that backup file was created
        backup_files = [f for f in os.listdir(self.test_data_dir) if '.corrupt.' in f]
        self.assertTrue(len(backup_files) >= 1)
        backup_path = os.path.join(self.test_data_dir, backup_files[0])
        with open(backup_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), corrupt_content)

    def test_concurrent_saves_thread_safety(self):
        """Multiple threads executing /save concurrently do not corrupt settings."""
        app.app.config['TESTING'] = True
        client = app.app.test_client()

        num_threads = 10
        saves_per_thread = 5

        def worker(thread_id):
            for i in range(saves_per_thread):
                wpm_val = (thread_id * 10) + i + 1
                res = client.post('/save', json={'wpm': wpm_val, 'errors': 0, 'backspaces': 0})
                if res.status_code != 200:
                    return False
            return True

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, tid) for tid in range(num_threads)]
            results = [f.result() for f in futures]

        self.assertTrue(all(results))

        # Validate final state of settings file
        loaded = app.load_settings()
        history = loaded.get('history', [])
        # History is capped at 20 entries
        self.assertEqual(len(history), 20)
        # All entries must be valid dictionaries with 'wpm' and 'display_timestamp'
        for entry in history:
            self.assertIn('wpm', entry)
            self.assertIn('display_timestamp', entry)
            self.assertIsInstance(entry['wpm'], (int, float))


if __name__ == '__main__':
    unittest.main()
