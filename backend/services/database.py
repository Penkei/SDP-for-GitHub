import os
import sqlite3
from contextlib import AbstractContextManager

from config import settings

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - PostgreSQL driver is optional for local SQLite use
    psycopg = None
    dict_row = None


class DatabaseConnection(AbstractContextManager):
    def __init__(self, connection, is_postgres: bool):
        self.connection = connection
        self.is_postgres = is_postgres

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
        finally:
            self.connection.close()

    def execute(self, sql: str, params=None):
        return self.connection.execute(self._prepare_sql(sql), params or ())

    def executemany(self, sql: str, rows):
        if self.is_postgres:
            cursor = self.connection.cursor()
            cursor.executemany(self._prepare_sql(sql), rows)
            return cursor

        return self.connection.executemany(self._prepare_sql(sql), rows)

    def _prepare_sql(self, sql: str) -> str:
        if not self.is_postgres:
            return sql

        return sql.replace("?", "%s")


class Database:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        self.database_url = settings.database_url
        self.is_postgres = bool(self.database_url)

        if self.is_postgres and psycopg is None:
            raise RuntimeError(
                "DATABASE_URL is set but psycopg is not installed. Install psycopg[binary]."
            )

        if not self.is_postgres:
            data_dir = os.path.dirname(self.sqlite_path)
            os.makedirs(data_dir, exist_ok=True)

    @property
    def storage_label(self) -> str:
        if self.is_postgres:
            return "postgresql"

        return self.sqlite_path

    def connect(self):
        if self.is_postgres:
            connection = psycopg.connect(self.database_url, row_factory=dict_row)
            return DatabaseConnection(connection, True)

        connection = sqlite3.connect(self.sqlite_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return DatabaseConnection(connection, False)

    def get_existing_columns(self, connection: DatabaseConnection, table_name: str) -> set[str]:
        if self.is_postgres:
            rows = connection.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = ?
                """,
                (table_name,),
            ).fetchall()
            return {row["column_name"] for row in rows}

        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}

