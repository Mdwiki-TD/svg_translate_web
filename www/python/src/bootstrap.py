from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class EnvironmentInitializer:
    """Handles environment variable loading and dynamic path registrations."""

    _initialized: bool = False

    @classmethod
    def setup(cls, env_path: Path | str | None = None) -> None:
        """
        Load environment variables and inject required dynamic module paths.
        Ensures execution happens only once per runtime.
        """
        if cls._initialized:
            logger.warning("Environment already initialized")
            return

        cls._load_environment(env_path)
        cls._setup_copy_svg_translation_path()
        cls._initialized = True

    @staticmethod
    def _load_environment(env_path: Path | str | None = None) -> None:
        """Locate and load the .env file into os.environ."""
        if env_path:
            env_path = Path(env_path)

        env_path = env_path if env_path and env_path.is_file() else None

        try:
            load_dotenv(dotenv_path=env_path)
        except Exception as exc:
            logger.warning("Failed to load .env file from %s: %s", env_path, exc)

    @staticmethod
    def _setup_copy_svg_translation_path() -> None:
        """Check for CopySVGTranslation availability and dynamically append its path if configured."""
        try:
            from CopySVGTranslation import SVGTranslationService  # noqa: F401
        except ImportError:
            logger.warning("CopySVGTranslation library not found")
            msg = """
            Please run `pip install CopySVGTranslation`
            """
            logger.error(msg)


__all__ = [
    "EnvironmentInitializer",
]
