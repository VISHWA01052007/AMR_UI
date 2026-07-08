"""
manual_control_widget.py
------------------------
Manual teleoperation UI dashboard controls.
Uses Dependency Injection to accept an external ManualController instance,
keeping this view layer completely isolated from business logic construction.
"""

from typing import Callable, Optional, TYPE_CHECKING
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Guard runtime from circular dependencies by isolating type-only imports
if TYPE_CHECKING:
    from ..controllers.manual_controller import ManualController


class ManualControlWidget(QFrame):
    """Panel with a directional pad and linear/angular velocity steppers."""

    def __init__(self, controller: "ManualController", parent: QWidget | None = None) -> None:
        """
        Initializes the manual control panel widget.
        
        :param controller: The pre-configured business logic controller injected from the outside.
        :param parent: Optional parent QWidget container reference.
        """
        super().__init__(parent)
        self.setObjectName("ManualControlWidget")
        
        # Capture the injected controller dependency
        self._controller = controller
        
        self._build_ui()
        self._update_ui_labels()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        # --- Header row ---------------------------------------------------
        header_row = QHBoxLayout()
        title_label = QLabel("MANUAL CONTROL")
        title_label.setProperty("panelTitle", True)
        header_row.addWidget(title_label)
        header_row.addStretch(1)

        joystick_icon = QLabel("\U0001F579")  # joystick glyph
        joystick_icon.setProperty("panelSubIcon", True)
        header_row.addWidget(joystick_icon)
        outer.addLayout(header_row)

        divider = QFrame()
        divider.setProperty("divider", True)
        divider.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(divider)

        # --- Body: dpad (left) + velocity controls (right) --------------------
        body_row = QHBoxLayout()
        body_row.setSpacing(24)
        body_row.addLayout(self._build_dpad(), stretch=1)
        body_row.addLayout(self._build_velocity_controls(), stretch=1)
        outer.addLayout(body_row, stretch=1)

    # ------------------------------------------------------------------ #
    # Sub-builders
    # ------------------------------------------------------------------ #
    def _build_dpad(self) -> QVBoxLayout:
        wrapper = QVBoxLayout()
        wrapper.addStretch(1)

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.up_button = self._make_dpad_button("\u2191", "dpad")
        self.down_button = self._make_dpad_button("\u2193", "dpad")
        self.left_button = self._make_dpad_button("\u2190", "dpad")
        self.right_button = self._make_dpad_button("\u2192", "dpad")
        self.stop_button = self._make_dpad_button("\u25A0", "dpadStop")

        # Connect UI clicks to explicit event handlers
        self.up_button.clicked.connect(self.on_forward_clicked)
        self.down_button.clicked.connect(self.on_backward_clicked)
        self.left_button.clicked.connect(self.on_left_clicked)
        self.right_button.clicked.connect(self.on_right_clicked)
        self.stop_button.clicked.connect(self.on_stop_clicked)

        grid.addWidget(self.up_button, 0, 1)
        grid.addWidget(self.left_button, 1, 0)
        grid.addWidget(self.stop_button, 1, 1)
        grid.addWidget(self.right_button, 1, 2)
        grid.addWidget(self.down_button, 2, 1)

        row_wrapper = QHBoxLayout()
        row_wrapper.addStretch(1)
        row_wrapper.addLayout(grid)
        row_wrapper.addStretch(1)

        wrapper.addLayout(row_wrapper)
        wrapper.addStretch(1)
        return wrapper

    @staticmethod
    def _make_dpad_button(text: str, style_class: str) -> QPushButton:
        button = QPushButton(text)
        button.setProperty("styleClass", style_class)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def _build_velocity_controls(self) -> QVBoxLayout:
        wrapper = QVBoxLayout()
        wrapper.setSpacing(16)
        wrapper.addStretch(1)

        # Simplified APIs: removed hardcoded defaults since _update_ui_labels dynamically overrides them next
        linear_row, self.linear_speed_value_label, self.linear_speed_minus_button, self.linear_speed_plus_button = (
            self._build_velocity_row("LINEAR SPEED (M/S)")
        )
        angular_row, self.angular_speed_value_label, self.angular_speed_minus_button, self.angular_speed_plus_button = (
            self._build_velocity_row("ANGULAR SPEED (RAD/S)")
        )

        self.linear_speed_minus_button.clicked.connect(self.on_linear_speed_decrease)
        self.linear_speed_plus_button.clicked.connect(self.on_linear_speed_increase)
        self.angular_speed_minus_button.clicked.connect(self.on_angular_speed_decrease)
        self.angular_speed_plus_button.clicked.connect(self.on_angular_speed_increase)

        wrapper.addLayout(linear_row)
        wrapper.addLayout(angular_row)
        wrapper.addStretch(1)
        return wrapper

    @staticmethod
    def _build_velocity_row(caption_text: str):
        column = QVBoxLayout()
        column.setSpacing(6)

        caption = QLabel(caption_text)
        caption.setProperty("velocityCaption", True)
        column.addWidget(caption)

        row_frame = QFrame()
        row_frame.setProperty("velocityRow", True)
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(4, 4, 4, 4)
        row_layout.setSpacing(6)

        minus_button = QPushButton("\u2212")
        minus_button.setProperty("styleClass", "velocityAdjust")
        minus_button.setCursor(Qt.CursorShape.PointingHandCursor)

        value_label = QLabel("--")
        value_label.setProperty("velocityValue", True)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setMinimumHeight(36)

        plus_button = QPushButton("+")
        plus_button.setProperty("styleClass", "velocityAdjust")
        plus_button.setCursor(Qt.CursorShape.PointingHandCursor)

        row_layout.addWidget(minus_button)
        row_layout.addWidget(value_label, stretch=1)
        row_layout.addWidget(plus_button)

        column.addWidget(row_frame)
        return column, value_label, minus_button, plus_button

    def _update_ui_labels(self) -> None:
        """Synchronizes text labels using safe read-only controller property getters."""
        self.linear_speed_value_label.setText(f"{self._controller.current_linear_speed:.2f}")
        self.angular_speed_value_label.setText(f"{self._controller.current_angular_speed:.2f}")

    # ------------------------------------------------------------------ #
    # Connected Controller Executions (UI Event Handlers / Slots)
    # ------------------------------------------------------------------ #
    def on_forward_clicked(self) -> None:
        """Handles D-Pad Up button clicks to trigger forward motion."""
        self._controller.move_forward()

    def on_backward_clicked(self) -> None:
        """Handles D-Pad Down button clicks to trigger backward motion."""
        self._controller.move_backward()

    def on_left_clicked(self) -> None:
        """Handles D-Pad Left button clicks to trigger counter-clockwise rotation."""
        self._controller.turn_left()

    def on_right_clicked(self) -> None:
        """Handles D-Pad Right button clicks to trigger clockwise rotation."""
        self._controller.turn_right()

    def on_stop_clicked(self) -> None:
        """Handles D-Pad Stop button clicks to immediately halt the robot."""
        self._controller.stop()

    def on_linear_speed_increase(self) -> None:
        """Handles Linear Speed + button clicks."""
        self._handle_speed_change(self._controller.increase_linear)

    def on_linear_speed_decrease(self) -> None:
        """Handles Linear Speed - button clicks."""
        self._handle_speed_change(self._controller.decrease_linear)

    def on_angular_speed_increase(self) -> None:
        """Handles Angular Speed + button clicks."""
        self._handle_speed_change(self._controller.increase_angular)

    def on_angular_speed_decrease(self) -> None:
        """Handles Angular Speed - button clicks."""
        self._handle_speed_change(self._controller.decrease_angular)

    # ------------------------------------------------------------------ #
    # Execution Helpers
    # ------------------------------------------------------------------ #
    def _handle_speed_change(self, controller_action: Callable[[], None]) -> None:
        """
        Executes a speed modification action and updates the UI labels.
        Keeps slot handlers readable and unified.
        """
        controller_action()
        self._update_ui_labels()