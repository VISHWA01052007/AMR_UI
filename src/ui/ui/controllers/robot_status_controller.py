"""
robot_status_controller.py
--------------------------
Pure Python controller for managing live AMR diagnostic telemetry states.
This class contains ZERO ROS2 or UI dependencies, adhering to architectural separation.
"""

class RobotStatusController:
    def __init__(self) -> None:
        self._linear_velocity = 0.0
        self._angular_velocity = 0.0
        self._online = False

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
        """Updates internal telemetry metrics and flags the system as online."""
        self._linear_velocity = linear
        self._angular_velocity = angular
        self._online = True