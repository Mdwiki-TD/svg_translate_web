from unittest.mock import MagicMock, patch

import mwclient
import pytest

from src.main_app.api_services.upload_bot_new import UploadFile, _RETRY_DELAYS
