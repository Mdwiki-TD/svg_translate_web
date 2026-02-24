"""Tests for app.py WSGI entry point."""

import logging
from unittest.mock import MagicMock, patch

# Import the app module components for testing
# Note: We import functions directly to avoid module-level side effects
from src.app import configure_logging


class TestConfigureLogging:
    """Tests for configure_logging function."""

    @patch("app.setup_logging")
    @patch("app.Path")
    @patch.dict("os.environ", {"MAIN_DIR": "/tmp/test_main_dir"}, clear=False)
    def test_configure_logging_creates_log_dir(self, mock_path_class, mock_setup_logging):
        """Test that configure_logging creates log directory."""
        # Setup mocks
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        mock_log_dir = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=mock_log_dir)

        # Call the function
        configure_logging()

        # Verify directory was created
        mock_log_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("app.setup_logging")
    @patch("app.Path")
    @patch.dict("os.environ", {"MAIN_DIR": "/tmp/test_main_dir"}, clear=False)
    def test_configure_logging_with_debug_mode(self, mock_path_class, mock_setup_logging):
        """Test that DEBUG mode sets logging level to DEBUG."""
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        mock_log_dir = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=mock_log_dir)

        with patch("app.DEBUG", True):
            configure_logging()
            # Check that setup_logging was called with DEBUG level
            call_args = mock_setup_logging.call_args
            assert call_args[1]["level"] == logging.DEBUG

    @patch("app.setup_logging")
    @patch("app.Path")
    @patch.dict("os.environ", {"MAIN_DIR": "/tmp/test_main_dir"}, clear=False)
    def test_configure_logging_without_debug_mode(self, mock_path_class, mock_setup_logging):
        """Test that non-DEBUG mode sets logging level to INFO."""
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        mock_log_dir = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=mock_log_dir)

        with patch("app.DEBUG", False):
            configure_logging()
            # Check that setup_logging was called with INFO level
            call_args = mock_setup_logging.call_args
            assert call_args[1]["level"] == logging.INFO

    @patch("app.setup_logging")
    @patch("app.Path")
    @patch.dict("os.environ", {}, clear=False)
    def test_configure_logging_uses_default_main_dir(self, mock_path_class, mock_setup_logging):
        """Test that configure_logging uses default main_dir when env var not set."""
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        mock_log_dir = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=mock_log_dir)

        with patch("app.os.path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = "/home/test"
            configure_logging()
            # Verify Path was called with expanded path
            mock_path_class.assert_called()

    @patch("app.setup_logging")
    @patch("app.Path")
    @patch.dict("os.environ", {"MAIN_DIR": "/tmp/test"}, clear=False)
    def test_configure_logging_sets_log_paths(self, mock_path_class, mock_setup_logging):
        """Test that configure_logging sets correct log file paths."""
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        mock_log_dir = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=mock_log_dir)

        mock_all_log = MagicMock()
        mock_error_log = MagicMock()
        mock_log_dir.__truediv__ = MagicMock(side_effect=[mock_all_log, mock_error_log])

        configure_logging()

        # Verify setup_logging was called
        mock_setup_logging.assert_called_once()
        call_kwargs = mock_setup_logging.call_args[1]
        assert "name" in call_kwargs
        assert call_kwargs["name"] == "main_app"
