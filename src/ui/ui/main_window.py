"""
main_window.py
--------------
Assembles the AMR dashboard from independent widgets.
Configures robust global application-wide keyboard shortcuts for teleoperation.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

# Relative imports for package components
from .widgets.header_widget import HeaderWidget
from .widgets.manual_control_widget import ManualControlWidget
from .widgets.mission_log_widget import MissionLogWidget
from .widgets.navigation_widget import NavigationWidget
from .widgets.robot_status_widget import RobotStatusWidget
from .widgets.slam_mapping_widget import SlamMappingWidget
from .widgets.waypoint_widget import WaypointWidget
from .widgets.map_widget import MapWidget


class MainWindow(QMainWindow):
    """Top-level window that assembles all dashboard widgets."""

    def __init__(self, manual_controller, robot_status_controller, map_controller, slam_controller, navigation_controller) -> None:
        super().__init__()

        self._manual_controller = manual_controller
        self._robot_status_controller = robot_status_controller
        self._map_controller = map_controller
        self._slam_controller = slam_controller
        self._navigation_controller = navigation_controller

        self.setWindowTitle("ROBOTIC_CORE v2.4 — AMR Dashboard")
        self.resize(1440, 900)
        
        # ✅ Initialize and link the application-scoped hotkeys layout map
        self._setup_keyboard_shortcuts()
        
        self._assemble_ui()

    def _setup_keyboard_shortcuts(self) -> None:
        """Registers keyboard shortcuts for manual robot control with global context."""
        
        # --- Move Forward (W) ---
        self.shortcut_forward = QShortcut(QKeySequence("W"), self)
        self.shortcut_forward.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_forward.activated.connect(self._manual_controller.move_forward)

        # --- Move Backward (S) ---
        self.shortcut_backward = QShortcut(QKeySequence("S"), self)
        self.shortcut_backward.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_backward.activated.connect(self._manual_controller.move_backward)

        # --- Turn Left (A) ---
        self.shortcut_left = QShortcut(QKeySequence("A"), self)
        self.shortcut_left.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_left.activated.connect(self._manual_controller.turn_left)

        # --- Turn Right (D) ---
        self.shortcut_right = QShortcut(QKeySequence("D"), self)
        self.shortcut_right.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_right.activated.connect(self._manual_controller.turn_right)

        # --- Hard Stop (Space) ---
        self.shortcut_stop = QShortcut(QKeySequence("Space"), self)
        self.shortcut_stop.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_stop.activated.connect(self._manual_controller.stop)

        # --- Emergency Stop Fallback (Escape) ---
        self.shortcut_escape = QShortcut(QKeySequence("Escape"), self)
        self.shortcut_escape.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_escape.activated.connect(self._manual_controller.stop)

    def _assemble_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Header -----------------------------------------------------
        self.header_widget = HeaderWidget()
        root_layout.addWidget(self.header_widget)

        # --- Body: left column (map + footer) | right sidebar ---------------
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        root_layout.addLayout(body_layout, stretch=1)

        body_layout.addLayout(self._build_left_column(), stretch=7)
        body_layout.addWidget(self._build_right_sidebar(), stretch=3)

    def _build_left_column(self) -> QVBoxLayout:
        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(0)

        # --- Top Area: Live Map Display (Takes maximum available space) -------
        self.map_widget = MapWidget(map_controller=self._map_controller, navigation_controller=self._navigation_controller)
        left_column.addWidget(self.map_widget, stretch=1)

        # --- Footer bar: Manual Control | Waypoints ---------------------------
        footer_widget = QWidget()
        footer_widget.setObjectName("FooterBar")
        footer_widget.setFixedHeight(300)

        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(24, 24, 24, 24)
        footer_layout.setSpacing(16)

        self.manual_control_widget = ManualControlWidget(controller=self._manual_controller)
        self.waypoint_widget = WaypointWidget()

        footer_layout.addWidget(self.manual_control_widget, stretch=1)
        footer_layout.addWidget(self.waypoint_widget, stretch=1)

        left_column.addWidget(footer_widget, stretch=0)
        return left_column

    def _build_right_sidebar(self) -> QScrollArea:
        self.robot_status_widget = RobotStatusWidget(controller=self._robot_status_controller)
        self.slam_mapping_widget = SlamMappingWidget(controller=self._slam_controller)
        self.navigation_widget = NavigationWidget(controller=self._navigation_controller)
        self.mission_log_widget = MissionLogWidget()

        sidebar_content = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_content)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(16)

        sidebar_layout.addWidget(self.robot_status_widget)
        sidebar_layout.addWidget(self.slam_mapping_widget)
        sidebar_layout.addWidget(self.navigation_widget)
        sidebar_layout.addWidget(self.mission_log_widget, stretch=1)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("RightSidebar")
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(320)
        scroll_area.setWidget(sidebar_content)
        return scroll_area