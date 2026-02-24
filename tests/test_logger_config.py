"""Tests for logger_config module."""

import logging
from unittest.mock import MagicMock

from src.logger_config import prepare_log_file, setup_file_handler, setup_logging


class TestPrepareLogFile:
    """Tests for prepare_log_file function."""

    def test_prepare_log_file_returns_none_for_none_input(self, tmp_path):
        """Test that None input returns None."""
        mock_logger = MagicMock()
        result = prepare_log_file(None, mock_logger)
        assert result is None

    def test_prepare_log_file_creates_directory(self, tmp_path):
        """Test that parent directory is created."""
        mock_logger = MagicMock()
        log_file = tmp_path / "new_dir" / "test.log"
        result = prepare_log_file(str(log_file), mock_logger)
        assert result is not None
        assert log_file.parent.exists()

    def test_prepare_log_file_expands_user_path(self, tmp_path):
        """Test that ~ is expanded to user home."""
        mock_logger = MagicMock()
        result = prepare_log_file("~/test.log", mock_logger)
        assert result is not None
        assert "~" not in str(result)

    def test_prepare_log_file_handles_exception(self, tmp_path):
        """Test that exceptions are logged and None is returned."""
        mock_logger = MagicMock()
        # Create a path that will cause an error (parent is a file)
        existing_file = tmp_path / "existing_file"
        existing_file.write_text("content")
        log_file = existing_file / "test.log"
        result = prepare_log_file(str(log_file), mock_logger)
        assert result is None
        mock_logger.error.assert_called_once()


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_with_string_level(self):
        """Test setup with string level."""
        logger_name = "test_logger_string"
        setup_logging(level="DEBUG", name=logger_name)
        logger = logging.getLogger(logger_name)
        assert logger.level == logging.DEBUG

    def test_setup_logging_with_numeric_level(self):
        """Test setup with numeric level."""
        logger_name = "test_logger_numeric"
        setup_logging(level=logging.WARNING, name=logger_name)
        logger = logging.getLogger(logger_name)
        assert logger.level == logging.WARNING

    def test_setup_logging_skips_if_handlers_exist(self):
        """Test that setup is skipped if handlers already exist."""
        logger_name = "test_logger_skip"
        logger = logging.getLogger(logger_name)
        logger.handlers = []  # Clear any existing handlers
        setup_logging(level="INFO", name=logger_name)
        first_handlers = list(logger.handlers)
        # Second call should not add new handlers
        setup_logging(level="DEBUG", name=logger_name)
        assert len(logger.handlers) == len(first_handlers)

    def test_setup_logging_with_log_file(self, tmp_path):
        """Test setup with log file."""
        logger_name = "test_logger_file"
        log_file = tmp_path / "test.log"
        setup_logging(level="INFO", name=logger_name, log_file=str(log_file))
        logger = logging.getLogger(logger_name)
        # Check that file handler was added
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1

    def test_setup_logging_with_error_log_file(self, tmp_path):
        """Test setup with error log file."""
        logger_name = "test_logger_error_file"
        error_log_file = tmp_path / "error.log"
        setup_logging(level="INFO", name=logger_name, error_log_file=str(error_log_file))
        logger = logging.getLogger(logger_name)
        # Check that file handler was added
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        # Check that handler is set to WARNING level
        assert file_handlers[0].level == logging.WARNING

    def test_setup_logging_propagate_false(self):
        """Test that propagate is set to False."""
        logger_name = "test_logger_propagate"
        setup_logging(level="INFO", name=logger_name)
        logger = logging.getLogger(logger_name)
        assert logger.propagate is False

    def test_setup_logging_with_invalid_level(self):
        """Test setup with invalid level string falls back to INFO."""
        logger_name = "test_logger_invalid"
        setup_logging(level="INVALID_LEVEL", name=logger_name)
        logger = logging.getLogger(logger_name)
        assert logger.level == logging.INFO


class TestSetupFileHandler:
    """Tests for setup_file_handler function."""

    def test_setup_file_handler_adds_handler(self, tmp_path):
        """Test that file handler is added to logger."""
        logger = logging.getLogger("test_file_handler")
        logger.handlers = []  # Clear existing handlers
        log_file = tmp_path / "test.log"
        log_file.write_text("")  # Create empty file
        setup_file_handler(logger, log_file, logging.INFO)
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        assert file_handlers[0].level == logging.INFO
