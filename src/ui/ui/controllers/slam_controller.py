"""
slam_controller.py
-------------------
Manages state flags for SLAM execution and routes requests to the UINode.
"""

from PyQt6.QtCore import QObject, pyqtSignal

class SlamController(QObject):
    """Encapsulates state tracking variables and events for Mapping tasks."""
    
    state_changed = pyqtSignal()
    
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    save_requested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._running: bool = False
        self._busy: bool = False
        self._locked: bool = False
        print("[DEBUG SLAM_CONTROLLER] Initialized.")

    def update_execution_state(self, running: bool, busy: bool, locked: bool = False) -> None:
        """Updates internal states based on UINode process tracking feedback."""
        print(f"[DEBUG SLAM_CONTROLLER] Updating State -> Running: {running}, Busy: {busy}, Locked: {locked}")
        self._running = running
        self._busy = busy
        self._locked = locked
        self.state_changed.emit()

    def request_start(self) -> None:
        if not self._running and not self._busy and not self._locked:
            print("[DEBUG SLAM_CONTROLLER] User clicked Start. Emitting start_requested...")
            self.update_execution_state(running=False, busy=True, locked=False)
            self.start_requested.emit()

    def request_stop(self) -> None:
        if self._running and not self._busy:
            print("[DEBUG SLAM_CONTROLLER] User clicked Stop. Emitting stop_requested...")
            self.update_execution_state(running=True, busy=True, locked=False)
            self.stop_requested.emit()

    def request_save(self, filename: str) -> None:
        if self._running and not self._busy:
            print(f"[DEBUG SLAM_CONTROLLER] User clicked Save for '{filename}'. Emitting save_requested...")
            self.update_execution_state(running=True, busy=True, locked=False)
            self.save_requested.emit(filename)

    @property
    def running(self) -> bool: return self._running
    
    @property
    def busy(self) -> bool: return self._busy

    @property
    def locked(self) -> bool: return self._locked