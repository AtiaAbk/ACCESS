import sqlite3
from pathlib import Path
from datetime import datetime


class MemoryDatabase:
    """Local SQLite memory system for ACCESS."""

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).resolve().parent / "access_memory.db"

        self.db_path = db_path
        self._memory_connection = None

        if db_path == ":memory:":
            self._memory_connection = sqlite3.connect(":memory:")
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._initialize()

    def _connect(self):
        """Return the database connection."""
        if self._memory_connection is not None:
            return self._memory_connection

        return sqlite3.connect(self.db_path)

    def _initialize(self):
        """Create the memories table."""
        conn = self._connect()

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

        if self._memory_connection is None:
            conn.close()

    def save(self, user_input: str, response: str):
        """Save a command and its response."""
        conn = self._connect()

        conn.execute(
            """
            INSERT INTO memories
            (user_input, response, created_at)
            VALUES (?, ?, ?)
            """,
            (
                user_input,
                response,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()

        if self._memory_connection is None:
            conn.close()

    def recent(self, limit=10):
        """Return recent memories."""
        conn = self._connect()

        cursor = conn.execute(
            """
            SELECT user_input, response, created_at
            FROM memories
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )

        results = cursor.fetchall()

        if self._memory_connection is None:
            conn.close()

        return results

    def search(self, query: str, limit=10):
        """Search stored memories."""
        conn = self._connect()

        cursor = conn.execute(
            """
            SELECT user_input, response, created_at
            FROM memories
            WHERE user_input LIKE ?
               OR response LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                f"%{query}%",
                f"%{query}%",
                limit,
            ),
        )

        results = cursor.fetchall()

        if self._memory_connection is None:
            conn.close()

        return results

    def close(self):
        """Close the in-memory connection."""
        if self._memory_connection is not None:
            self._memory_connection.close()
            self._memory_connection = None
