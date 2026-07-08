"""
WaypointWidget
---------------
Saved-location shortcuts and location management:
    - Home Base
    - Charging Dock
    - Add Location
    - Delete Location
    - Map Folder (browse saved maps)

No functionality — Phase 1 wires every control to an empty placeholder
callback.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class WaypointWidget(QFrame):
    """Panel with saved-location tiles (home, dock, add, delete)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WaypointWidget")
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        # --- Header row: title + map folder button ---------------------------
        header_row = QHBoxLayout()
        title_label = QLabel("WAYPOINTS / LOCATIONS")
        title_label.setProperty("panelTitle", True)
        header_row.addWidget(title_label)
        header_row.addStretch(1)

        self.map_folder_button = QPushButton("\U0001F4C1  MAP FILES")
        self.map_folder_button.setProperty("styleClass", "mapFolder")
        self.map_folder_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.map_folder_button.clicked.connect(self.on_open_map_folder)
        header_row.addWidget(self.map_folder_button)
        outer.addLayout(header_row)

        divider = QFrame()
        divider.setProperty("divider", True)
        divider.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(divider)

        # --- Tile grid ----------------------------------------------------
        grid = QGridLayout()
        grid.setSpacing(10)

        self.home_base_button = self._make_tile("\U0001F3E0", "Home Base", "waypointTile")
        self.charging_dock_button = self._make_tile("\U0001F50C", "Charging Dock", "waypointTile")
        self.add_location_button = self._make_tile("\u2795", "Add Location", "waypointAdd")
        self.delete_location_button = self._make_tile("\u2716", "Delete Loc", "waypointDelete")

        self.home_base_button.clicked.connect(self.on_home_base)
        self.charging_dock_button.clicked.connect(self.on_charging_dock)
        self.add_location_button.clicked.connect(self.on_add_location)
        self.delete_location_button.clicked.connect(self.on_delete_location)

        grid.addWidget(self.home_base_button, 0, 0)
        grid.addWidget(self.charging_dock_button, 0, 1)
        grid.addWidget(self.add_location_button, 1, 0)
        grid.addWidget(self.delete_location_button, 1, 1)

        outer.addLayout(grid, stretch=1)

    @staticmethod
    def _make_tile(icon_text: str, label_text: str, style_class: str) -> QPushButton:
        button = QPushButton()
        button.setProperty("styleClass", style_class)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(56)

        layout = QVBoxLayout(button)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(4)

        icon = QLabel(icon_text)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")

        text = QLabel(label_text)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet("font-size: 10px; font-weight: 700; background: transparent; border: none;")

        layout.addWidget(icon)
        layout.addWidget(text)
        return button

    # ------------------------------------------------------------------ #
    # Placeholder callbacks (Phase 1 — no ROS2 / business logic)
    # ------------------------------------------------------------------ #
    def on_open_map_folder(self) -> None:
        pass

    def on_home_base(self) -> None:
        pass

    def on_charging_dock(self) -> None:
        pass

    def on_add_location(self) -> None:
        pass

    def on_delete_location(self) -> None:
        pass
