import uuid
from datetime import datetime, timezone

from services.database import Database


class FeedbackService:
    def __init__(self, db_path: str):
        self.database = Database(db_path)
        self.db_path = self.database.storage_label
        self._initialize_database()

    def create_feedback(
        self,
        name: str = "",
        role: str = "",
        rating: int = 5,
        message: str = ""
    ) -> dict:
        cleaned_name = (name or "").strip()[:80]
        cleaned_role = (role or "").strip()[:80]
        cleaned_message = (message or "").strip()

        if not cleaned_message:
            raise ValueError("Feedback message is required.")

        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")

        feedback = {
            "id": str(uuid.uuid4()),
            "name": cleaned_name,
            "role": cleaned_role,
            "rating": int(rating),
            "message": cleaned_message[:1200],
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO feedback_entries (
                    id,
                    name,
                    role,
                    rating,
                    message,
                    submitted_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback["id"],
                    feedback["name"],
                    feedback["role"],
                    feedback["rating"],
                    feedback["message"],
                    feedback["submitted_at"],
                ),
            )

        return feedback

    def list_feedback(self) -> list:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    role,
                    rating,
                    message,
                    submitted_at
                FROM feedback_entries
                ORDER BY submitted_at DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def _connect(self):
        return self.database.connect()

    def _initialize_database(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback_entries (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    role TEXT,
                    rating INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    submitted_at TEXT NOT NULL
                )
                """
            )
