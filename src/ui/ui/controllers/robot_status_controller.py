"""
robot_status_controller.py
--------------------------
Pure Python controller for managing live AMR diagnostic telemetry states.
This class contains ZERO ROS2 or UI dependencies, adhering to architectural separation.
Integrates user-focused connection logs via the MissionLogController with a flood-gate filter.
"""

class RobotStatusController:
    def __init__(self, mission_log_controller=None) -> None:
        self._linear_velocity = 0.0
        self._angular_velocity = 0.0
        self._online = False
        
        # ✅ Retain injected Event Log Controller reference
        self._mission_log_controller = mission_log_controller
        
        # ✅ Track last connection state to prevent flooding the log on every odom callback
        self._last_online_state = False

    # --- Read-Only Property Getters for UI Encapsulation ---
    @property
    def linear_velocity(self) -> float:
        """Returns the current tracked linear velocity of the AMR (m/s)."""
        return self._linear_velocity

    @property
    def angular_velocity(self) -> float:
        """Returns the current tracked angular velocity of the AMR (rad/s)."""
        return self._angular_velocity

    @property
    def online(self) -> bool:
        """Returns True if the AMR is actively streaming live metrics."""
        return self._online

    # --- State Mutation ---
    def update(self, linear: float, angular: float) -> None:
        """Updates internal telemetry metrics and flags the system as online cleanly."""
        self._linear_velocity = linear
        self._angular_velocity = angular
        self._online = True
        
        # ✅ State Latch Filter: Only log once upon initial connection transition
        if self._online != self._last_online_state:
            self._last_online_state = self._online
            if self._mission_log_controller is not None:
                self._mission_log_controller.log_success("Robot connected.")

    def set_offline(self) -> None:
        """ programmatically flags the connection state as lost."""
        self._linear_velocity = 0.0
        self._angular_velocity = 0.0
        self._online = False
        
        # ✅ State Latch Filter: Only log once upon disconnect transition
        if self._online != self._last_online_state:
            self._last_online_state = self._online
            if self._mission_log_controller is not None:
                self._mission_log_controller.log_error("Robot disconnected.")