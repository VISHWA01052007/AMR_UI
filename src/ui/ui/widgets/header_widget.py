"""
HeaderWidget
------------
Top application bar for the AMR dashboard.

Contains:
    - Robot title / branding
    - WiFi status icon
    - Battery indicator
    - Emergency Stop button

This widget is purely visual for Phase 1. No ROS2 or business logic is
implemented here — the Emergency Stop button is wired to a placeholder
callback only.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class HeaderWidget(QWidget):
    """Top app bar: branding, connectivity status, e-stop, user avatar."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HeaderWidget")
        self.setFixedHeight(64)
        self._build_ui()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        # --- Left: branding -------------------------------------------------
        title_label = QLabel("ROBOTIC_CORE v2.4")
        title_label.setObjectName("HeaderTitle")
        layout.addWidget(title_label)

        layout.addStretch(1)

        # --- Right: status cluster -------------------------------------------
        wifi_label = QLabel("\U0001F4F6")  # antenna bars glyph
        wifi_label.setObjectName("HeaderIconLabel")
        wifi_label.setToolTip("Network status")
        layout.addWidget(wifi_label)

        battery_icon = QLabel("\U0001F50B")  # battery glyph
        battery_icon.setObjectName("HeaderIconLabel")
        layout.addWidget(battery_icon)

        battery_label = QLabel("84%")
        battery_label.setObjectName("BatteryLabel")
        layout.addWidget(battery_label)

        layout.addSpacing(16)

        self.emergency_stop_button = QPushButton("EMERGENCY STOP")
        self.emergency_stop_button.setObjectName("EmergencyStopButton")
        self.emergency_stop_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.emergency_stop_button.clicked.connect(self.on_emergency_stop)
        layout.addWidget(self.emergency_stop_button)

        avatar_label = QLabel()
        avatar_label.setObjectName("AvatarLabel")
        avatar_label.setFixedSize(32, 32)
        layout.addWidget(avatar_label)

    # ------------------------------------------------------------------ #
    # Placeholder callbacks (Phase 1 — no ROS2 / business logic)
    # ------------------------------------------------------------------ #
    def on_emergency_stop(self) -> None:
        pass
