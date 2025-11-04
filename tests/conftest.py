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
