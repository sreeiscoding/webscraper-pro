"""Local SQLite persistence for saved extraction projects and job history."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import ExtractionConfig, FieldSpec, validate_url
from app.exceptions import ConfigurationError


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "webscraper_pro.db"
DEFAULT_EXPORT_DIR = Path(__file__).resolve().parent.parent / "exports"


@dataclass
class ProjectRecord:
    project_id: int
    name: str
    url: str
    config: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class JobSummary:
    job_id: int
    project_id: int | None
    status: str
    started_at: str
    ended_at: str | None
    record_count: int
    error_summary: str | None
    engine: str
    url: str


class StorageError(RuntimeError):
    """Raised when the local SQLite database cannot be opened or used safely."""


class ProjectStore:
    """A lightweight local SQLite repository for project and job metadata."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError(f"Unable to open database at '{self.db_path}'.") from exc

    def _ensure_schema(self) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        url TEXT NOT NULL,
                        config_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS job_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,
                        status TEXT NOT NULL,
                        started_at TEXT NOT NULL,
                        ended_at TEXT,
                        record_count INTEGER NOT NULL DEFAULT 0,
                        error_summary TEXT,
                        engine TEXT NOT NULL DEFAULT 'static',
                        url TEXT NOT NULL,
                        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL
                    )
                    """
                )
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError("Unable to initialise the local database schema.") from exc

    def create_project(self, name: str, url: str, config: dict[str, Any]) -> ProjectRecord:
        """Create a new saved project after validating its URL and structured configuration."""
        trimmed_name = (name or "").strip()
        if not trimmed_name:
            raise ValueError("Project name is required.")
        if not validate_url(url):
            raise ValueError("Project URL must be a valid public HTTP(S) URL.")

        serialised = self._validate_config(config)
        now = self._utc_now()

        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO projects (name, url, config_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (trimmed_name, url, json.dumps(serialised, sort_keys=True), now, now),
                )
                project_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"A project named '{trimmed_name}' already exists.") from exc
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError("Unable to save the project configuration.") from exc

        return ProjectRecord(
            project_id=project_id,
            name=trimmed_name,
            url=url,
            config=serialised,
            created_at=now,
            updated_at=now,
        )

    def list_projects(self) -> list[ProjectRecord]:
        """Return all saved projects in insertion order."""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT id, name, url, config_json, created_at, updated_at FROM projects ORDER BY updated_at DESC"
                ).fetchall()
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError("Unable to read saved projects.") from exc

        return [
            ProjectRecord(
                project_id=int(row["id"]),
                name=str(row["name"]),
                url=str(row["url"]),
                config=json.loads(row["config_json"]),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    def get_project(self, project_id: int) -> ProjectRecord | None:
        """Return a project by its database ID."""
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT id, name, url, config_json, created_at, updated_at FROM projects WHERE id = ?",
                    (project_id,),
                ).fetchone()
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError("Unable to load the selected project.") from exc
        if row is None:
            return None

        return ProjectRecord(
            project_id=int(row["id"]),
            name=str(row["name"]),
            url=str(row["url"]),
            config=json.loads(row["config_json"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def update_project(self, project_id: int, *, name: str | None = None, url: str | None = None, config: dict[str, Any] | None = None) -> ProjectRecord:
        """Update a saved project while keeping configuration validation in place."""
        row = self.get_project(project_id)
        if row is None:
            raise ValueError(f"Project '{project_id}' does not exist.")

        new_name = row.name if name is None else name.strip()
        new_url = row.url if url is None else url
        new_config = row.config if config is None else self._validate_config(config)

        if not new_name:
            raise ValueError("Project name is required.")
        if not validate_url(new_url):
            raise ValueError("Project URL must be a valid public HTTP(S) URL.")

        updated_at = self._utc_now()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE projects
                    SET name = ?, url = ?, config_json = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new_name, new_url, json.dumps(new_config, sort_keys=True), updated_at, project_id),
                )
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError("Unable to update the selected project.") from exc

        return ProjectRecord(
            project_id=project_id,
            name=new_name,
            url=new_url,
            config=new_config,
            created_at=row.created_at,
            updated_at=updated_at,
        )

    def delete_project(self, project_id: int) -> None:
        """Delete a project and any linked history rows along with it."""
        try:
            with self._connect() as connection:
                cursor = connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                if cursor.rowcount == 0:
                    raise ValueError(f"Project '{project_id}' does not exist.")
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError("Unable to delete the selected project.") from exc

    def add_job_summary(
        self,
        *,
        project_id: int | None,
        status: str,
        started_at: str | None = None,
        ended_at: str | None = None,
        record_count: int = 0,
        error_summary: str | None = None,
        engine: str = "static",
        url: str,
    ) -> JobSummary:
        """Persist a job summary without saving the full scraped dataset."""
        started = started_at or self._utc_now()
        if not url or not validate_url(url):
            raise ValueError("Job URL must be a valid public HTTP(S) URL.")

        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO job_history (project_id, status, started_at, ended_at, record_count, error_summary, engine, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        status,
                        started,
                        ended_at,
                        int(record_count),
                        error_summary[:250] if error_summary else None,
                        engine,
                        url,
                    ),
                )
                job_id = int(cursor.lastrowid)
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError("Unable to save the job summary.") from exc

        return JobSummary(
            job_id=job_id,
            project_id=project_id,
            status=status,
            started_at=started,
            ended_at=ended_at,
            record_count=int(record_count),
            error_summary=error_summary[:250] if error_summary else None,
            engine=engine,
            url=url,
        )

    def list_job_history(self, limit: int = 20) -> list[JobSummary]:
        """Return recent job history entries with timestamps and status metadata."""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT id, project_id, status, started_at, ended_at, record_count, error_summary, engine, url
                    FROM job_history
                    ORDER BY started_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError("Unable to read job history.") from exc

        return [
            JobSummary(
                job_id=int(row["id"]),
                project_id=row["project_id"],
                status=str(row["status"]),
                started_at=str(row["started_at"]),
                ended_at=row["ended_at"],
                record_count=int(row["record_count"]),
                error_summary=row["error_summary"],
                engine=str(row["engine"]),
                url=str(row["url"]),
            )
            for row in rows
        ]

    def prune_history(self, keep_last: int = 100, max_age_days: int | None = None) -> int:
        """Remove older job history rows to keep storage compact."""
        try:
            with self._connect() as connection:
                if max_age_days is not None:
                    cutoff = self._utc_now(offset_days=-max_age_days)
                    cursor = connection.execute(
                        "DELETE FROM job_history WHERE started_at < ? AND id NOT IN (SELECT id FROM job_history ORDER BY started_at DESC LIMIT ?)",
                        (cutoff, keep_last),
                    )
                    return int(cursor.rowcount)

                cursor = connection.execute(
                    "DELETE FROM job_history WHERE id NOT IN (SELECT id FROM job_history ORDER BY started_at DESC LIMIT ?)",
                    (keep_last,),
                )
                return int(cursor.rowcount)
        except sqlite3.Error as exc:  # pragma: no cover - reached only on SQLite failures
            raise StorageError("Unable to prune old job history.") from exc

    def _validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate supported project config structure and normalise it for storage."""
        if not isinstance(config, dict):
            raise ConfigurationError("Project configuration must be a JSON object.")
        if "base_url" not in config and "url" not in config:
            raise ConfigurationError("Project configuration must include a base URL.")

        schema = {
            "base_url": str(config.get("base_url") or config.get("url") or ""),
            "record_selector": str(config.get("record_selector", "")),
            "fields": config.get("fields", {}),
            "pagination": config.get("pagination", {}),
            "engine": config.get("engine", "static"),
        }

        if not validate_url(schema["base_url"]):
            raise ConfigurationError("The configured URL must be a valid public HTTP(S) URL.")
        if not isinstance(schema["fields"], dict):
            raise ConfigurationError("Fields must be stored as a dictionary.")
        if not isinstance(schema["pagination"], dict):
            raise ConfigurationError("Pagination settings must be a dictionary.")

        for field_name, field_value in schema["fields"].items():
            if isinstance(field_value, FieldSpec):
                continue
            if isinstance(field_value, dict):
                FieldSpec(name=str(field_name), **field_value)
                continue
            raise ConfigurationError(f"Field '{field_name}' is not a valid FieldSpec or dictionary definition.")

        return schema

    @staticmethod
    def _utc_now(offset_days: int = 0) -> str:
        timestamp = datetime.now(timezone.utc)
        if offset_days:
            timestamp = timestamp.fromtimestamp(timestamp.timestamp() + offset_days * 86400)
        return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
