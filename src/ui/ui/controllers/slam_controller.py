"""
slam_controller.py
-------------------
Manages state flags for SLAM execution and routes requests to the UINode.
Integrates clean, user-focused logs via the MissionLogController.
"""

from PyQt6.QtCore import QObject, pyqtSignal

class SlamController(QObject):
    """Encapsulates state tracking variables and events for Mapping tasks."""
    
    state_changed = pyqtSignal()
    
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    save_requested = pyqtSignal(str)

    def __init__(self, mission_log_controller=None) -> None:
        super().__init__()
        self._running: bool = False
        self._busy: bool = False
        self._locked: bool = False
        
        # ✅ Retain injected Event Log Controller reference
        self._mission_log_controller = mission_log_controller
        print("[DEBUG SLAM_CONTROLLER] Initialized.")

    def update_execution_state(self, running: bool, busy: bool, locked: bool = False) -> None:
        """Updates internal states based on UINode process tracking feedback."""
        print(f"[DEBUG SLAM_CONTROLLER] Updating State -> Running: {running}, Busy: {busy}, Locked: {locked}")
        
        # Capture transition delta to append clean logs dynamically upon completion
        old_running = self._running
        
        self._running = running
        self._busy = busy
        self._locked = locked
        
        # Check if mapping just finished transitioning to an active running state
        if not old_running and self._running and not self._busy:
            if self._mission_log_controller is not None:
                self._mission_log_controller.log_success("Mapping started.")
        
        # Check if mapping just finished transitioning back into idle states
        elif old_running and not self._running and not self._busy:
            if self._mission_log_controller is not None:
                self._mission_log_controller.log_info("Mapping stopped.")

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
            
            # ✅ Log the immediate intention to save the map
            if self._mission_log_controller is not None:
                self._mission_log_controller.log_info("Saving map file...")
                
            self.save_requested.emit(filename)
            
            # Reset busy states back to normal and issue success confirmation
            self.update_execution_state(running=True, busy=False, locked=False)
            if self._mission_log_controller is not None:
                self._mission_log_controller.log_success("Map saved successfully.")

    @property
    def running(self) -> bool: return self._running
    
    @property
    def busy(self) -> bool: return self._busy

    @property
    def locked(self) -> bool: return self._locked