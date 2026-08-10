"""Tests for the interactive translate session manager."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.main_app.shared.copysvg_wrapper.mapping import ExtractorData
from src.main_app.shared.copysvg_wrapper.translate_session import (
    TranslateSession,
    cleanup_old_sessions,
)


class TestTranslateSessionCreate:
    """Tests for TranslateSession.create()."""

    def test_creates_with_uuid(self):
        session = TranslateSession.create(source_type="commons", commons_title="File:Test.svg")
        assert len(session.session_id) == 32  # UUID hex
        assert session.source_type == "commons"
        assert session.commons_title == "File:Test.svg"

    def test_creates_with_mapping(self):
        mapping = ExtractorData(new={"Hello": {"ar": "مرحبا"}})
        session = TranslateSession.create(source_type="upload", mapping=mapping)

        assert session.mapping_json["new"]["Hello"]["ar"] == "مرحبا"

    def test_creates_upload_session(self):
        session = TranslateSession.create(
            source_type="upload",
            upload_filename="myfile.svg",
        )
        assert session.upload_filename == "myfile.svg"
        assert session.commons_title == ""


class TestTranslateSessionPersistence:
    """Tests for save/load/delete."""

    def test_save_and_load(self, tmp_path):
        mapping = ExtractorData(new={"Hello": {"fr": "Bonjour"}})
        session = TranslateSession.create(
            source_type="commons",
            commons_title="File:Example.svg",
            mapping=mapping,
            created_at="2025-01-01T00:00:00Z",
        )

        session.save(tmp_path)
        loaded = TranslateSession.load(session.session_id, tmp_path)

        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.source_type == "commons"
        assert loaded.commons_title == "File:Example.svg"
        assert loaded.created_at == "2025-01-01T00:00:00Z"

    def test_load_nonexistent_returns_none(self, tmp_path):
        result = TranslateSession.load("nonexistent-id", tmp_path)
        assert result is None

    def test_load_invalid_session_id_returns_none(self, tmp_path):
        # Path traversal attempt
        result = TranslateSession.load("../etc/passwd", tmp_path)
        assert result is None

        result = TranslateSession.load("", tmp_path)
        assert result is None

    def test_delete_removes_directory(self, tmp_path):
        session = TranslateSession.create(source_type="upload")
        session.save(tmp_path)

        # Create a dummy SVG file in session dir
        svg_path = session.svg_path(tmp_path)
        svg_path.write_text("<svg></svg>")

        assert session.session_dir(tmp_path).exists()

        session.delete(tmp_path)
        assert not session.session_dir(tmp_path).exists()

    def test_delete_nonexistent_is_safe(self, tmp_path):
        session = TranslateSession.create(source_type="upload")
        # Should not raise
        session.delete(tmp_path)


class TestTranslateSessionPaths:
    """Tests for path helper methods."""

    def test_svg_path(self, tmp_path):
        session = TranslateSession.create(source_type="upload")
        svg = session.svg_path(tmp_path)
        assert svg.name == "source.svg"
        assert str(session.session_id) in str(svg)

    def test_output_path(self, tmp_path):
        session = TranslateSession.create(source_type="upload")
        output = session.output_path(tmp_path)
        assert output.name == "output.svg"

    def test_sessions_root_created(self, tmp_path):
        TranslateSession.create(source_type="upload").save(tmp_path)
        sessions_root = tmp_path / "translate_sessions"
        assert sessions_root.exists()
        assert sessions_root.is_dir()


class TestTranslateSessionMapping:
    """Tests for mapping get/set helpers."""

    def test_get_mapping(self):
        mapping = ExtractorData(new={"Hello": {"ar": "مرحبا"}})
        session = TranslateSession.create(source_type="upload", mapping=mapping)

        retrieved = session.get_mapping()
        assert isinstance(retrieved, ExtractorData)
        assert retrieved.new["Hello"]["ar"] == "مرحبا"

    def test_set_mapping(self):
        session = TranslateSession.create(source_type="upload")

        new_mapping = ExtractorData(new={"World": {"fr": "Monde"}})
        session.set_mapping(new_mapping)

        retrieved = session.get_mapping()
        assert retrieved.new["World"]["fr"] == "Monde"

    def test_get_mapping_empty_session(self):
        session = TranslateSession.create(source_type="upload")
        mapping = session.get_mapping()
        assert mapping.is_empty()


class TestCleanupOldSessions:
    """Tests for cleanup_old_sessions()."""

    def test_cleanup_no_sessions(self, tmp_path):
        removed = cleanup_old_sessions(tmp_path, max_age_hours=24)
        assert removed == 0

    def test_cleanup_keeps_fresh_sessions(self, tmp_path):
        session = TranslateSession.create(source_type="upload")
        session.save(tmp_path)

        removed = cleanup_old_sessions(tmp_path, max_age_hours=24)
        assert removed == 0
        assert session.session_dir(tmp_path).exists()

    def test_cleanup_removes_old_sessions(self, tmp_path):
        session = TranslateSession.create(source_type="upload")
        session.save(tmp_path)

        # Manually set the mtime to the past
        meta_path = session.session_dir(tmp_path) / "session.json"
        old_time = time.time() - (48 * 3600)  # 48 hours ago
        import os

        os.utime(str(meta_path), (old_time, old_time))

        removed = cleanup_old_sessions(tmp_path, max_age_hours=24)
        assert removed == 1
        assert not session.session_dir(tmp_path).exists()

    def test_cleanup_removes_orphan_directories(self, tmp_path):
        sessions_root = tmp_path / "translate_sessions"
        sessions_root.mkdir(parents=True)

        # Create an orphan directory (no session.json)
        orphan = sessions_root / "abcdef1234567890abcdef1234567890"
        orphan.mkdir()

        removed = cleanup_old_sessions(tmp_path, max_age_hours=24)
        assert removed == 1
        assert not orphan.exists()
