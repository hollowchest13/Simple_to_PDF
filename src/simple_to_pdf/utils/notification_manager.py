from simple_to_pdf.app_dialog import InfoDialog
from typing import Any
import logging

logger = logging.getLogger(__name__)


class NotificationManager:
    def __init__(self, master):
        self.master = master

    def _show_msg(self, scenario_key: str = "info", **kwargs):
        """
        Display a notification dialog to the user.
        Uses a try-except block to prevent application crashes on UI errors.
        """
        try:
            InfoDialog(parent=self.master, scenario_key=scenario_key, **kwargs)
        except Exception as e:
            logger.error(f"Failed to display notification dialog [{scenario_key}]: {e}")

    def info(self, scenario_key: str, **kwargs: Any) -> None:
        """Show info dialog."""
        self._show_msg(f"info.{scenario_key}", **kwargs)

    def warning(self, scenario_key: str, **kwargs: Any) -> None:
        """Show warning dialog."""
        self._show_msg(f"warning.{scenario_key}", **kwargs)

    def error(self, scenario_key: str, **kwargs: Any) -> None:
        """Show error dialog."""
        self._show_msg(f"error.{scenario_key}", **kwargs)
