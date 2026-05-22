from unittest.mock import MagicMock, patch

from src.main_app.db.services.admin_service import (
    active_coordinators,
    add_coordinator,
    delete_coordinator,
    list_coordinators,
    set_coordinator_active,
)
