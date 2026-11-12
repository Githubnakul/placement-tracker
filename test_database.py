import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Har test ka alag temporary database.
        # Tera actual applications.db change nahi hoga.
        self.temp_dir = tempfile.TemporaryDirectory()
        test_path = Path(self.temp_dir.name) / "test.db"

        self.db_patch = patch.object(database, "DB_PATH", test_path)
        self.db_patch.start()
        database.init_db()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def add_sample(self):
        database.add_application(
            "DemoTech",
            "Python Intern",
            "Applied",
            "2027-01-20",
        )
        return database.get_applications()[0]["id"]

    def test_new_database_is_empty(self):
        self.assertEqual(database.get_applications(), [])

    def test_add_application(self):
        self.add_sample()
        rows = database.get_applications()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "DemoTech")
        self.assertEqual(rows[0]["status"], "Applied")

    def test_update_status(self):
        app_id = self.add_sample()
        changed = database.update_application_status(app_id, "Interview")

        self.assertEqual(changed, 1)
        self.assertEqual(
            database.get_applications()[0]["status"], "Interview"
        )
        self.assertEqual(len(database.get_applications()), 1)

    def test_delete_application(self):
        app_id = self.add_sample()
        deleted = database.delete_application(app_id)

        self.assertEqual(deleted, 1)
        self.assertEqual(database.get_applications(), [])

    def test_missing_id_does_not_change_data(self):
        self.add_sample()

        self.assertEqual(
            database.update_application_status(999999, "Offer"), 0
        )
        self.assertEqual(database.delete_application(999999), 0)
        self.assertEqual(len(database.get_applications()), 1)


if __name__ == "__main__":
    unittest.main()