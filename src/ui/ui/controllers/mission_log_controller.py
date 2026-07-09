"""
mission_log_controller.py
-------------------------
Centralized event system controller for managing user-facing dashboard messages.
Ingests log events across multiple severity levels and notifies connected view widgets.
"""

from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QTime

class LogLevel(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class MissionLogController(QObject):
    """Business logic controller managing system diagnostic messages and status relays."""
    
    # PyQt signal emitted whenever a formatted entry gets added to the log pipeline
    message_added = pyqtSignal(str, str, str)  # timestamp, message, level_string

    def __init__(self) -> None:
        super().__init__()
        self._logs: list[tuple[str, str, str]] = []
        print("[DEBUG MISSION_LOG_CONTROLLER] Initialized.")

    def log_info(self, message: str) -> None:
        """Relays a standard informational system update message."""
        self._add_entry(f"ℹ  {message}", LogLevel.INFO)

    def log_success(self, message: str) -> None:
        """Relays a successful workflow or operation completion message."""
        self._add_entry(f"✓  {message}", LogLevel.SUCCESS)

    def log_warning(self, message: str) -> None:
        """Relays a warning message concerning non-critical issues or obstructions."""
        self._add_entry(f"⚠  {message}", LogLevel.WARNING)

    def log_error(self, message: str) -> None:
        """Relays an error message for critical system failures or lost processes."""
        self._add_entry(f"✖  {message}", LogLevel.ERROR)

    def _add_entry(self, message: str, level: LogLevel) -> None:
        """Generates an explicit timestamp and archives the message in memory."""
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        entry = (timestamp, message, level.value)
        
        self._logs.append(entry)
        self.message_added.emit(timestamp, message, level.value)

    @property
    def logs(self) -> list[tuple[str, str, str]]:
        """Provides read-only access to the historical archived event log matrix."""
        return self._logs