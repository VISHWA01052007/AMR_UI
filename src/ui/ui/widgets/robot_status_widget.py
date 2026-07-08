"""
robot_status_widget.py
----------------------
Displays live robot telemetry data via Dependency Injection.
Refreshes visual layout periodically on the main thread via QTimer polling.
"""

from typing import TYPE_CHECKING
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ..controllers.robot_status_controller import RobotStatusController


class RobotStatusWidget(QFrame):
    """Panel showing robot velocity metrics and an online status dot."""

    def __init__(self, controller: "RobotStatusController", parent: QWidget | None = None) -> None:
        """
        Initializes the telemetry display panel.
        
        :param controller: Injected RobotStatusController dependency handle.
        """
        super().__init__(parent)
        self.setObjectName("RobotStatusWidget")
        self.setProperty("panel", True)
        
        # Capture the injected dependency handle
        self._controller = controller
        
        self._build_ui()
        self.update_status()

        # Setup periodic worker timer polling to update widgets safely on the GUI thread
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_status)
        self._timer.start(100) # 100 ms = 10 FPS refresh rate

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        # --- Header row: title + status dot ---------------------------------
        header_row = QHBoxLayout()
        title_label = QLabel("ROBOT STATUS")
        title_label.setProperty("panelTitle", True)
        header_row.addWidget(title_label)
        header_row.addStretch(1)

        # Saved as field property to modify styling dynamically
        self.status_dot = QLabel()
        self.status_dot.setObjectName("StatusDot")
        header_row.addWidget(self.status_dot)
        outer.addLayout(header_row)

        # --- Metrics grid -----------------------------------------------------
        grid = QGridLayout()
        grid.setSpacing(12)

        velocity_card, self.linear_velocity_label = self._build_metric_card("VELOCITY (M/S)", "\u26A1")
        angular_card, self.angular_velocity_label = self._build_metric_card("ANGULAR (RAD/S)", "\U0001F504")

        grid.addWidget(velocity_card, 0, 0)
        grid.addWidget(angular_card, 0, 1)
        outer.addLayout(grid)

    @staticmethod
    def _build_metric_card(label_text: str, icon_text: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setProperty("metricCard", True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setProperty("metricLabel", True)
        layout.addWidget(label)

        value_row = QHBoxLayout()
        value_row.setSpacing(6)

        icon = QLabel(icon_text)
        icon.setProperty("metricIcon", True)
        value_row.addWidget(icon)

        value_label = QLabel("--")
        value_label.setProperty("metricValue", True)
        value_row.addWidget(value_label)
        value_row.addStretch(1)

        layout.addLayout(value_row)
        return card, value_label

    def update_status(self) -> None:
        """Synchronizes presentation elements with the internal controller tracking values."""
        # 1. Update text displays
        self.linear_velocity_label.setText(f"{self._controller.linear_velocity:.2f}")
        self.angular_velocity_label.setText(f"{self._controller.angular_velocity:.2f}")
        
        # 2. Assign absolute stylesheet geometry directly without unpolish/polish overhead
        if self._controller.online:
            self.status_dot.setStyleSheet("""
                background: #00C853;
                border-radius: 6px;
                min-width: 12px;
                max-width: 12px;
                min-height: 12px;
                max-height: 12px;
            """)
        else:
            self.status_dot.setStyleSheet("""
                background: #F44336;
                border-radius: 6px;
                min-width: 12px;
                max-width: 12px;
                min-height: 12px;
                max-height: 12px;
            """)