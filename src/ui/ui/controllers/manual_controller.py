from typing import Callable, Optional
from ..config import settings


class ManualController:
    def __init__(self, publish_callback: Optional[Callable[[float, float], None]] = None) -> None:
        self._publish_callback = publish_callback

        # Tracked speed baselines (what the steppers increment/decrement)
        self._linear_speed = settings.DEFAULT_LINEAR_SPEED
        self._angular_speed = settings.DEFAULT_ANGULAR_SPEED

        # Active motion command variables sent to the robot
        self._linear_command = 0.0
        self._angular_command = 0.0

    # --- Getters for UI Encapsulation ---------------------------------
    @property
    def current_linear_speed(self) -> float:
        return self._linear_speed

    @property
    def current_angular_speed(self) -> float:
        return self._angular_speed

    @property
    def current_commands(self) -> tuple[float, float]:
        return self._linear_command, self._angular_command

    # --- Core Velocity Modification Logic ----------------------------
    def increase_linear(self) -> None:
        self._linear_speed = min(
            self._linear_speed + settings.LINEAR_SPEED_STEP, 
            settings.MAX_LINEAR_SPEED
        )
        # Dynamically update command value mid-flight if moving forward or backward
        if self._linear_command != 0.0:
            new_linear = self._linear_speed if self._linear_command > 0 else -self._linear_speed
            self._set_motion(new_linear, self._angular_command)

    def decrease_linear(self) -> None:
        self._linear_speed = max(
            self._linear_speed - settings.LINEAR_SPEED_STEP, 
            settings.MIN_LINEAR_SPEED
        )
        if self._linear_command != 0.0:
            new_linear = self._linear_speed if self._linear_command > 0 else -self._linear_speed
            self._set_motion(new_linear, self._angular_command)

    def increase_angular(self) -> None:
        self._angular_speed = min(
            self._angular_speed + settings.ANGULAR_SPEED_STEP, 
            settings.MAX_ANGULAR_SPEED
        )
        if self._angular_command != 0.0:
            new_angular = self._angular_speed if self._angular_command > 0 else -self._angular_speed
            self._set_motion(self._linear_command, new_angular)

    def decrease_angular(self) -> None:
        self._angular_speed = max(
            self._angular_speed - settings.ANGULAR_SPEED_STEP, 
            settings.MIN_ANGULAR_SPEED
        )
        if self._angular_command != 0.0:
            new_angular = self._angular_speed if self._angular_command > 0 else -self._angular_speed
            self._set_motion(self._linear_command, new_angular)

    # --- Motion Command Actions ----------------------------------------
    def move_forward(self) -> None:
        self._set_motion(self._linear_speed, 0.0)

    def move_backward(self) -> None:
        self._set_motion(-self._linear_speed, 0.0)

    def turn_left(self) -> None:
        self._set_motion(0.0, self._angular_speed)

    def turn_right(self) -> None:
        self._set_motion(0.0, -self._angular_speed)

    def stop(self) -> None:
        self._set_motion(0.0, 0.0)

    # --- Internal Helpers ---------------------------------------------
    def _set_motion(self, linear: float, angular: float) -> None:
        if self._linear_command == linear and self._angular_command == angular:
            return

        self._linear_command = linear
        self._angular_command = angular
        self._execute_publish()

    def _execute_publish(self) -> None:
        if self._publish_callback is not None:
            self._publish_callback(self._linear_command, self._angular_command)