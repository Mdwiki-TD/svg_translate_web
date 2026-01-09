#
import os
import sys
from cryptography.fernet import Fernet
from pathlib import Path
import secrets
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT/"src"))
    sys.path.insert(0, str(ROOT))
# ---
CopySVGTranslation_PATH = os.getenv("CopySVGTranslation_PATH", "I:/SVG_PY/CopySVGTranslation/CopySVGTranslation")
# ---
if CopySVGTranslation_PATH and Path(CopySVGTranslation_PATH).is_dir():
    sys.path.insert(0, str(Path(CopySVGTranslation_PATH).parent))
# ---
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("OAUTH_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
os.environ.setdefault("OAUTH_CONSUMER_KEY", "test-consumer-key")
os.environ.setdefault("OAUTH_CONSUMER_SECRET", "test-consumer-secret")
os.environ.setdefault("OAUTH_MWURI", "https://example.org/w/index.php")

from src import svg_config  # load_dotenv()

import pytest
from typing import Any


@pytest.fixture
def csrf_token():
    """Helper fixture to generate CSRF tokens for tests."""
    def _get_csrf_token(client: Any) -> str:
        """Get a CSRF token by making a GET request and extracting it."""
        import re
        response = client.get('/')
        match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
        if match:
            return match.group(1).decode()
        # If not found in response, try to generate one from the test request context
        from flask_wtf.csrf import generate_csrf
        with client.application.test_request_context():
            return generate_csrf()
    return _get_csrf_token
