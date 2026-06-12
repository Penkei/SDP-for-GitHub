import uuid
from datetime import datetime, timezone

from config import settings
from services.database import Database, DatabaseConnection


class PredictionHistoryService:
    def __init__(self, db_path=None):
        self.database = Database(db_path or settings.prediction_history_db_path)
        self.db_path = self.database.storage_label
        self._initialize_database()

    def save_prediction(self, prediction_response: dict) -> str:
        history_id = str(uuid.uuid4())
        results = prediction_response.get("results", [])
        summary = self._build_summary(results)
        scanned_at = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO prediction_runs (
                    id,
                    repo_url,
                    commit_sha,
                    prediction_threshold,
                    scanned_at,
                    total_files_scanned,
                    high_risk_count,
                    medium_risk_count,
                    low_risk_count,
                    defective_count,
                    average_risk_probability
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    history_id,
                    prediction_response.get("repo_url", ""),
                    prediction_response.get("commit_sha", ""),
                    prediction_response.get("prediction_threshold"),
                    scanned_at,
                    prediction_response.get("total_files_scanned", len(results)),
                    summary["high_risk_count"],
                    summary["medium_risk_count"],
                    summary["low_risk_count"],
                    summary["defective_count"],
                    summary["average_risk_probability"],
                ),
            )

            connection.executemany(
                """
                INSERT INTO prediction_results (
                    id,
                    run_id,
                    file_path,
                    language,
                    prediction_label,
                    defect_risk_probability,
                    risk_level,
                    recommendation,
                    file_change_count,
                    file_bug_fix_count,
                    recent_file_change_count,
                    days_since_last_change,
                    last_change_churn,
                    author_file_change_count,
                    top_contributing_metrics,
                    readable_explanation,
                    confidence_warning,
                    is_potential_test_file,
                    test_file_reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        str(uuid.uuid4()),
                        history_id,
                        result.get("file_path", ""),
                        result.get("language", ""),
                        result.get("prediction_label", ""),
                        result.get("defect_risk_probability", 0),
                        result.get("risk_level", ""),
                        result.get("recommendation", ""),
                        result.get("file_change_count", 0),
                        result.get("file_bug_fix_count", 0),
                        result.get("recent_file_change_count", 0),
                        result.get("days_since_last_change", 0),
                        result.get("last_change_churn", 0),
                        result.get("author_file_change_count", 0),
                        result.get("top_contributing_metrics", ""),
                        result.get("readable_explanation", ""),
                        result.get("confidence_warning", ""),
                        1 if result.get("is_potential_test_file", False) else 0,
                        result.get("test_file_reason", ""),
                    )
                    for result in results
                ],
            )

        return history_id

    def list_predictions(self) -> list:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    repo_url,
                    commit_sha,
                    prediction_threshold,
                    scanned_at,
                    total_files_scanned,
                    high_risk_count,
                    medium_risk_count,
                    low_risk_count,
                    defective_count,
                    average_risk_probability
                FROM prediction_runs
                ORDER BY scanned_at DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def get_prediction(self, history_id: str) -> dict:
        with self._connect() as connection:
            run = connection.execute(
                """
                SELECT
                    id,
                    repo_url,
                    commit_sha,
                    prediction_threshold,
                    scanned_at,
                    total_files_scanned
                FROM prediction_runs
                WHERE id = ?
                """,
                (history_id,),
            ).fetchone()

            if not run:
                return None

            result_rows = connection.execute(
                """
                SELECT
                    file_path,
                    language,
                    prediction_label,
                    defect_risk_probability,
                    risk_level,
                    recommendation,
                    file_change_count,
                    file_bug_fix_count,
                    recent_file_change_count,
                    days_since_last_change,
                    last_change_churn,
                    author_file_change_count,
                    top_contributing_metrics,
                    readable_explanation,
                    confidence_warning,
                    is_potential_test_file,
                    test_file_reason
                FROM prediction_results
                WHERE run_id = ?
                ORDER BY defect_risk_probability DESC
                """,
                (history_id,),
            ).fetchall()

        run_dict = dict(run)

        return {
            "history_id": run_dict["id"],
            "repo_url": run_dict["repo_url"],
            "commit_sha": run_dict["commit_sha"],
            "prediction_threshold": run_dict["prediction_threshold"],
            "scanned_at": run_dict["scanned_at"],
            "total_files_scanned": run_dict["total_files_scanned"],
            "results": [dict(row) for row in result_rows],
        }

    def delete_prediction(self, history_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM prediction_runs WHERE id = ?",
                (history_id,),
            )

        return cursor.rowcount > 0

    def _connect(self):
        return self.database.connect()

    def _initialize_database(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_runs (
                    id TEXT PRIMARY KEY,
                    repo_url TEXT NOT NULL,
                    commit_sha TEXT NOT NULL,
                    prediction_threshold REAL,
                    scanned_at TEXT NOT NULL,
                    total_files_scanned INTEGER NOT NULL,
                    high_risk_count INTEGER NOT NULL,
                    medium_risk_count INTEGER NOT NULL,
                    low_risk_count INTEGER NOT NULL,
                    defective_count INTEGER NOT NULL,
                    average_risk_probability REAL NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_results (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    language TEXT,
                    prediction_label TEXT NOT NULL,
                    defect_risk_probability REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    recommendation TEXT,
                    file_change_count INTEGER DEFAULT 0,
                    file_bug_fix_count INTEGER DEFAULT 0,
                    recent_file_change_count INTEGER DEFAULT 0,
                    days_since_last_change INTEGER DEFAULT 0,
                    last_change_churn INTEGER DEFAULT 0,
                    author_file_change_count INTEGER DEFAULT 0,
                    top_contributing_metrics TEXT,
                    readable_explanation TEXT,
                    confidence_warning TEXT,
                    is_potential_test_file INTEGER DEFAULT 0,
                    test_file_reason TEXT,
                    FOREIGN KEY (run_id)
                        REFERENCES prediction_runs (id)
                        ON DELETE CASCADE
                )
                """
            )

            self._ensure_column(
                connection,
                "prediction_runs",
                "prediction_threshold",
                "REAL"
            )

            for column_name in [
                "file_change_count",
                "file_bug_fix_count",
                "recent_file_change_count",
                "days_since_last_change",
                "last_change_churn",
                "author_file_change_count",
                "confidence_warning",
                "is_potential_test_file",
                "test_file_reason",
            ]:
                column_type = "INTEGER DEFAULT 0" if column_name == "is_potential_test_file" else "TEXT"

                if column_name in {
                    "file_change_count",
                    "file_bug_fix_count",
                    "recent_file_change_count",
                    "days_since_last_change",
                    "last_change_churn",
                    "author_file_change_count",
                }:
                    column_type = "INTEGER DEFAULT 0"

                self._ensure_column(
                    connection,
                    "prediction_results",
                    column_name,
                    column_type
                )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_prediction_results_run_id
                ON prediction_results (run_id)
                """
            )

    def _ensure_column(
        self,
        connection: DatabaseConnection,
        table_name: str,
        column_name: str,
        column_definition: str
    ):
        existing_columns = self.database.get_existing_columns(connection, table_name)

        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            )

    def _build_summary(self, results: list) -> dict:
        total_probability = sum(
            result.get("defect_risk_probability", 0)
            for result in results
        )
        total_results = len(results)

        return {
            "high_risk_count": sum(1 for result in results if result.get("risk_level") == "High"),
            "medium_risk_count": sum(1 for result in results if result.get("risk_level") == "Medium"),
            "low_risk_count": sum(1 for result in results if result.get("risk_level") == "Low"),
            "defective_count": sum(1 for result in results if result.get("prediction_label") == "Defective"),
            "average_risk_probability": total_probability / total_results if total_results else 0,
        }
