import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "applications.db"


def init_db():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                deadline TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_application(company, role, status, deadline):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO applications (company, role, status, deadline)
            VALUES (?, ?, ?, ?)
            """,
            (company, role, status, deadline),
        )


def get_applications():
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM applications ORDER BY id DESC"
        ).fetchall()

    return [dict(row) for row in rows]


def update_application_status(application_id, new_status):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "UPDATE applications SET status = ? WHERE id = ?",
            (new_status, application_id),
        )
        changed = cursor.rowcount

    return changed


def delete_application(application_id):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM applications WHERE id = ?",
            (application_id,),
        )
        deleted = cursor.rowcount

    return deleted