import sqlite3
from datetime import datetime
from pathlib import Path


class MemoryDatabase:
    """Local SQLite database for ACCESS memory."""

    def __init__(self):
        self.database_directory = (
            Path(__file__).resolve().parent.parent
            / "data"
        )

        self.database_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.database_path = (
            self.database_directory
            / "access.db"
        )

        self._initialize_database()

    def _connect(self):
        """Create a database connection."""

        return sqlite3.connect(
            self.database_path
        )

    def _initialize_database(self):
        """Create required database tables."""

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_message TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add_note(self, content: str) -> str:
        """Store a note."""

        timestamp = datetime.now().isoformat(
            timespec="seconds"
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO notes (content, created_at)
                VALUES (?, ?)
                """,
                (content, timestamp),
            )

        return "Note saved successfully."

    def get_notes(self):
        """Retrieve stored notes."""

        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT id, content, created_at
                FROM notes
                ORDER BY id DESC
                """
            )

            return cursor.fetchall()

    def save_conversation(
        self,
        user_message: str,
        assistant_response: str,
    ):
        """Save a conversation."""

        timestamp = datetime.now().isoformat(
            timespec="seconds"
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversations
                (
                    user_message,
                    assistant_response,
                    created_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_message,
                    assistant_response,
                    timestamp,
                ),
            )

    def get_recent_conversations(self, limit: int = 10):
        """Retrieve recent conversations."""

        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT
                    user_message,
                    assistant_response,
                    created_at
                FROM conversations
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )

            return cursor.fetchall()
