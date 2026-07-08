"""
navigation_widget.py
---------------------
Visual control block for Nav2 operations matching the classic layout.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QCheckBox, QFileDialog
from ..config import settings

class NavigationWidget(QFrame):
    def __init__(self, controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self.setObjectName("NavigationWidget")
        self.setProperty("panel", True)
        
        self._build_ui()
        self._controller.state_changed.connect(self._on_state_changed)
        self._on_state_changed()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title_label = QLabel("NAVIGATION")
        title_label.setProperty("panelTitle", True)
        header_row.addWidget(title_label)
        header_row.addStretch(1)

        self.navigation_toggle = QCheckBox()
        self.navigation_toggle.setProperty("styleClass", "toggleSwitch")
        self.navigation_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.navigation_toggle.clicked.connect(self._on_toggle_clicked)
        header_row.addWidget(self.navigation_toggle)
        outer.addLayout(header_row)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self.set_initial_pose_button = QPushButton("Set Pose")
        self.set_initial_pose_button.setProperty("styleClass", "navChip")
        self.set_goal_pose_button = QPushButton("Set Goal")
        self.set_goal_pose_button.setProperty("styleClass", "navChip")
        
        self.set_initial_pose_button.clicked.connect(self.on_set_initial_pose)
        self.set_goal_pose_button.clicked.connect(self.on_set_goal_pose)
        
        row1.addWidget(self.set_initial_pose_button)
        row1.addWidget(self.set_goal_pose_button)
        outer.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.waypoints_button = QPushButton("Waypoints")
        self.waypoints_button.setProperty("styleClass", "navChip")
        self.continuous_motion_button = QPushButton("Cont. Mode")
        self.continuous_motion_button.setProperty("styleClass", "navChip")
        
        row2.addWidget(self.waypoints_button)
        row2.addWidget(self.continuous_motion_button)
        outer.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(12)
        self.start_button = QPushButton("START")
        self.start_button.setProperty("styleClass", "startButton")
        self.abort_button = QPushButton("ABORT")
        self.abort_button.setProperty("styleClass", "abortButton")
        
        self.start_button.clicked.connect(self.on_start)
        self.abort_button.clicked.connect(self.on_abort)
        
        row3.addWidget(self.start_button)
        row3.addWidget(self.abort_button)
        outer.addLayout(row3)

    def _on_toggle_clicked(self) -> None:
        if self.navigation_toggle.isChecked():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Navigation Workspace Map Configuration",
                settings.MAPS_EXPORT_DIR, "Map Metadata Files (*.yaml)"
            )
            if not file_path:
                self.navigation_toggle.setChecked(False)
                return
            self._controller.request_toggle(True, file_path)
        else:
            self._controller.request_toggle(False, "")

    def _on_state_changed(self) -> None:
        ctrl = self._controller
        
        self.navigation_toggle.blockSignals(True)
        self.navigation_toggle.setChecked(ctrl.running)
        self.navigation_toggle.blockSignals(False)

        self.set_initial_pose_button.setStyleSheet("")
        self.set_goal_pose_button.setStyleSheet("")

        if ctrl.locked:
            self.navigation_toggle.setEnabled(False)
            self.set_initial_pose_button.setEnabled(False)
            self.set_goal_pose_button.setEnabled(False)
            self.waypoints_button.setEnabled(False)
            self.continuous_motion_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.abort_button.setEnabled(False)
            return

        self.navigation_toggle.setEnabled(not ctrl.busy)
        
        is_ready = ctrl.running and not ctrl.busy
        self.set_initial_pose_button.setEnabled(is_ready)
        self.set_goal_pose_button.setEnabled(is_ready)
        self.waypoints_button.setEnabled(is_ready)
        self.continuous_motion_button.setEnabled(is_ready)
        self.start_button.setEnabled(is_ready)
        self.abort_button.setEnabled(is_ready)

        if ctrl.interaction_mode == "INITIAL_POSE":
            self.set_initial_pose_button.setStyleSheet("background-color: #2a2a2a; border: 2px solid #2196f3; color: #ffffff; font-weight: bold;")
        elif ctrl.interaction_mode == "GOAL_SELECTION":
            self.set_goal_pose_button.setStyleSheet("background-color: #2a2a2a; border: 2px solid #44d8f1; color: #ffffff; font-weight: bold;")

    def on_set_initial_pose(self) -> None:
        self._controller.set_interaction_mode("INITIAL_POSE")

    def on_set_goal_pose(self) -> None:
        self._controller.set_interaction_mode("GOAL_SELECTION")

    def on_waypoints(self) -> None: pass
    def on_continuous_motion(self) -> None: pass
    
    def on_start(self) -> None:
        self._controller.request_mission_start()

    def on_abort(self) -> None:
        self._controller.request_mission_abort()