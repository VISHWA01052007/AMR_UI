"""
navigation_controller.py
------------------------
Orchestrates interaction and execution modes across the active navigation workspace.
Implements an enum-driven state machine for mission synchronization.
"""

from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal

class NavigationState(Enum):
    IDLE = 0
    GOAL_SELECTED = 1
    NAVIGATING = 2
    PAUSED = 3
    ERROR = 4


class NavigationController(QObject):
    """Manages the lifecycle, focus tool locks, and states of active Nav2 operations."""
    
    state_changed = pyqtSignal()
    
    toggle_requested = pyqtSignal(bool, str)
    initial_pose_published = pyqtSignal(float, float, float)
    goal_pose_published = pyqtSignal(float, float, float)
    abort_requested = pyqtSignal()

    def __init__(self, mission_log_controller=None) -> None:
        super().__init__()
        self._running: bool = False
        self._busy: bool = False
        self._locked: bool = False
        
        self._interaction_mode: str = "NONE"  # "NONE", "INITIAL_POSE", "GOAL_SELECTION"
        self._status_text: str = "Stack Offline"
        
        # ✅ Retain injected Event Log Controller reference
        self._mission_log_controller = mission_log_controller
        
        # Staged Operational State Matrices
        self._state = NavigationState.IDLE
        self._pending_goal: tuple | None = None  # Cached locally as (x, y, yaw)
        self._active_goal: tuple | None = None   # Promoted to active upon START click
        self._global_path_points: list = []

    def update_execution_state(self, running: bool, busy: bool, locked: bool = False) -> None:
        self._running = running
        self._busy = busy
        self._locked = locked
        
        if locked:
            self._interaction_mode = "NONE"
            self._state = NavigationState.IDLE
            self._pending_goal = None
            self._active_goal = None
            self._status_text = "SLAM Mode Active"
        elif not running:
            self._interaction_mode = "NONE"
            self._state = NavigationState.IDLE
            self._pending_goal = None
            self._active_goal = None
            self._status_text = "Stack Offline"
        elif running and self._interaction_mode == "NONE":
            self._sync_status_text()
            
        self.state_changed.emit()

    def _sync_status_text(self) -> None:
        """Helper to maintain uniform textual indicators matching state bounds."""
        if self._state == NavigationState.NAVIGATING:
            self._status_text = "Status: Navigating to Target..."
        elif self._state == NavigationState.GOAL_SELECTED:
            self._status_text = "Status: Goal Staged. Ready to Press START."
        else:
            self._status_text = "Status: Localization Ready / Idle"

    def set_interaction_mode(self, mode: str) -> None:
        if not self._running or self._busy or self._locked:
            return
        if self._state == NavigationState.NAVIGATING:
            return
            
        print(f"[DEBUG NAV_CONTROLLER] Interaction tool focus changed -> {mode}")
        self._interaction_mode = mode
        
        if mode == "INITIAL_POSE":
            self._status_text = "Placement Mode: Click & Drag Initial Pose on Map"
        elif mode == "GOAL_SELECTION":
            self._status_text = "Placement Mode: Click & Drag target Navigation Goal"
        elif mode == "NONE":
            self._sync_status_text()
            
        self.state_changed.emit()

    # --- Pending Goal Preview Management API Matrix ---
    def set_pending_goal(self, x: float, y: float, yaw: float) -> None:
        """Passive staging boundary: locks target properties inside internal preview slots."""
        if self._state == NavigationState.NAVIGATING:
            return
            
        print(f"[DEBUG NAV_CONTROLLER] Preview Goal Staged -> x: {x:.2f}, y: {y:.2f}, yaw: {yaw:.2f}")
        self._pending_goal = (x, y, yaw)
        self._state = NavigationState.GOAL_SELECTED
        self.set_interaction_mode("NONE")
        
        # ✅ Appends user-facing update to the logging widget feed
        if self._mission_log_controller is not None:
            self._mission_log_controller.log_info("Goal selected.")
            
        self.state_changed.emit()

    def has_pending_goal(self) -> bool:
        return self._pending_goal is not None

    def clear_pending_goal(self) -> None:
        self._pending_goal = None
        if self._state == NavigationState.GOAL_SELECTED:
            self._state = NavigationState.IDLE
        self.state_changed.emit()

    def request_toggle(self, checked: bool, map_path: str = "") -> None:
        if not self._busy and not self._locked:
            self.update_execution_state(running=self._running, busy=True, locked=False)
            self.toggle_requested.emit(checked, map_path)

    def publish_initial_pose(self, x: float, y: float, yaw: float) -> None:
        if self._state == NavigationState.NAVIGATING:
            return
        print(f"[DEBUG NAV_CONTROLLER] Relaying Initial Pose -> x: {x:.2f}, y: {y:.2f}, yaw: {yaw:.2f}")
        self.initial_pose_published.emit(x, y, yaw)
        self.set_interaction_mode("NONE")
        
        # ✅ Logs localization sync milestone
        if self._mission_log_controller is not None:
            self._mission_log_controller.log_success("Localization initialized.")

    def set_global_plan(self, points: list) -> None:
        self._global_path_points = points
        self.state_changed.emit()

    # --- State Evaluation Accessors ---
    @property
    def state(self) -> NavigationState: return self._state

    def is_idle(self) -> bool: return self._state == NavigationState.IDLE
    def is_goal_selected(self) -> bool: return self._state == NavigationState.GOAL_SELECTED
    def is_navigating(self) -> bool: return self._state == NavigationState.NAVIGATING

    def notify_navigation_completed(self) -> None:
        """Invoked by the network node layer once Nav2 triggers completion parameters."""
        print("[DEBUG NAV_CONTROLLER] Received completion notification. Transitioning back to IDLE.")
        self._state = NavigationState.IDLE
        self._active_goal = None
        self._pending_goal = None
        self._global_path_points = []
        self._sync_status_text()
        
        # ✅ Appends user-friendly task arrival milestone
        if self._mission_log_controller is not None:
            self._mission_log_controller.log_success("Destination reached.")
            
        self.state_changed.emit()

    # --- Unified Execution Triggers ---
    def request_mission_start(self) -> None:
        """Promotes the staged candidate into active telemetry and fires it to the ROS network."""
        if self._state == NavigationState.GOAL_SELECTED and self.has_pending_goal():
            x, y, yaw = self._pending_goal
            print(f"[DEBUG NAV_CONTROLLER] START clicked. Promoting staged candidate to active goal -> x: {x:.2f}, y: {y:.2f}")
            
            self._state = NavigationState.NAVIGATING
            self._active_goal = (x, y, yaw)
            self._sync_status_text()
            
            # ✅ Logs precise navigation execution start
            if self._mission_log_controller is not None:
                self._mission_log_controller.log_success("Navigation started.")
                
            # Fire signal down to UINode transport interface
            self.goal_pose_published.emit(x, y, yaw)
            self.state_changed.emit()

    def request_mission_abort(self) -> None:
        print("[DEBUG NAV_CONTROLLER] Requesting mission target reset...")
        self._state = NavigationState.IDLE
        self._pending_goal = None
        self._active_goal = None
        self._global_path_points = []
        self._interaction_mode = "NONE"
        self._status_text = "Mission Aborted. System Idle."
        
        # ✅ Appends explicit, clear cancel warning log
        if self._mission_log_controller is not None:
            self._mission_log_controller.log_warning("Navigation cancelled.")
            
        self.abort_requested.emit()
        self.state_changed.emit()

    @property
    def running(self) -> bool: return self._running
    @property
    def busy(self) -> bool: return self._busy
    @property
    def locked(self) -> bool: return self._locked
    @property
    def interaction_mode(self) -> str: return self._interaction_mode
    @property
    def status_text(self) -> str: return self._status_text
    @property
    def pending_goal(self) -> tuple | None: return self._pending_goal
    @property
    def active_goal(self) -> tuple | None: return self._active_goal
    @property
    def global_path_points(self) -> list: return self._global_path_points