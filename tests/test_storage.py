from __future__ import annotations

import sqlite3

import pytest

from app.storage import ProjectStore, StorageError


def test_database_initialises_and_creates_projects(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    store = ProjectStore(db_path)

    project = store.create_project(
        "Sample project",
        "https://example.com/catalog",
        {
            "base_url": "https://example.com/catalog",
            "record_selector": "article",
            "fields": {"title": {"selector": "h2", "extraction_type": "text", "required": True}},
            "pagination": {"max_pages": 2},
        },
    )

    assert project.name == "Sample project"
    assert store.list_projects()[0].project_id == project.project_id


def test_update_and_delete_project(tmp_path) -> None:
    store = ProjectStore(tmp_path / "projects.db")
    project = store.create_project(
        "Alpha",
        "https://example.com",
        {"base_url": "https://example.com", "fields": {"title": {"selector": "h1", "extraction_type": "text"}}, "pagination": {}},
    )

    updated = store.update_project(project.project_id, name="Beta")
    assert updated.name == "Beta"

    store.delete_project(project.project_id)
    assert store.list_projects() == []


def test_malformed_config_is_rejected() -> None:
    store = ProjectStore("test_storage.db")

    with pytest.raises(Exception):
        store.create_project("Bad config", "https://example.com", {"fields": "not-a-dict"})


def test_storage_handles_database_errors(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    store = ProjectStore(tmp_path / "db.db")

    def raise_error(*args, **kwargs):
        raise sqlite3.DatabaseError("simulated")

    monkeypatch.setattr("app.storage.sqlite3.connect", raise_error)

    with pytest.raises(StorageError):
        store.list_projects()


def test_job_summary_history_records_status_and_count(tmp_path) -> None:
    store = ProjectStore(tmp_path / "jobs.db")
    job = store.add_job_summary(
        project_id=None,
        status="completed",
        record_count=42,
        error_summary=None,
        engine="static",
        url="https://example.com",
    )

    assert job.record_count == 42
    assert store.list_job_history()[0].status == "completed"
