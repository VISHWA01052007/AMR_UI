"""
slam_mapping_widget.py
-----------------------
Clean UI buttons for mapping execution routines matching the global core QSS design rules.
"""

import os
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from ..config import settings
from .save_map_dialog import SaveMapDialog

class SlamMappingWidget(QFrame):
    """Panel rendering SLAM runtime controls styled cleanly to integrate into the sidebar."""

    def __init__(self, controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self.setObjectName("SlamMappingWidget")
        self.setProperty("panel", True)
        
        self._build_ui()
        self._controller.state_changed.connect(self._on_state_changed)
        self._on_state_changed()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title_label = QLabel("SLAM MAPPING")
        title_label.setProperty("panelTitle", True)
        header_row.addWidget(title_label)
        outer.addLayout(header_row)

        grid = QGridLayout()
        grid.setSpacing(8)

        self.start_mapping_button = QPushButton("Start Mapping")
        self.start_mapping_button.setProperty("styleClass", "primaryAction")

        self.stop_mapping_button = QPushButton("Stop Mapping")
        self.stop_mapping_button.setProperty("styleClass", "secondaryAction")

        self.save_map_button = QPushButton("Save Map File")
        self.save_map_button.setProperty("styleClass", "secondaryAction")

        # Connect slots
        self.start_mapping_button.clicked.connect(self._controller.request_start)
        self.stop_mapping_button.clicked.connect(self._controller.request_stop)
        self.save_map_button.clicked.connect(self._on_save_button_clicked)

        grid.addWidget(self.start_mapping_button, 0, 0)
        grid.addWidget(self.stop_mapping_button, 0, 1)
        grid.addWidget(self.save_map_button, 1, 0, 1, 2)

        outer.addLayout(grid)

    def _on_save_button_clicked(self) -> None:
        """Prompts for filename using our bespoke, cleanly integrated theme modal window."""
        dialog = SaveMapDialog(self)
        
        if dialog.exec():
            filename = dialog.get_filename()
            if filename:
                full_path = os.path.join(settings.MAPS_EXPORT_DIR, filename)
                self._controller.request_save(full_path)

    def _on_state_changed(self) -> None:
        """Modifies button accessibility and text based on global QSS properties."""
        ctrl = self._controller

        self.start_mapping_button.setStyleSheet("")
        self.stop_mapping_button.setStyleSheet("")
        self.save_map_button.setStyleSheet("")

        if ctrl.locked:
            self.start_mapping_button.setEnabled(False)
            self.stop_mapping_button.setEnabled(False)
            self.save_map_button.setEnabled(False)
            self.start_mapping_button.setText("Nav Mode Active")
            self.start_mapping_button.setStyleSheet("background-color: #1c1b1b; color: #555555; border: 1px solid #2a2a2a;")
            return

        if ctrl.busy:
            self.start_mapping_button.setEnabled(False)
            self.stop_mapping_button.setEnabled(False)
            self.save_map_button.setEnabled(False)
            if not ctrl.running:
                self.start_mapping_button.setText("Launching...")
            else:
                self.start_mapping_button.setText("Stopping...")
        else:
            self.start_mapping_button.setText("Start Mapping")
            self.stop_mapping_button.setText("Stop Mapping")
            
            self.start_mapping_button.setEnabled(not ctrl.running)
            self.stop_mapping_button.setEnabled(ctrl.running)
            self.save_map_button.setEnabled(ctrl.running)

            self.start_mapping_button.setProperty("active", ctrl.running)
            self.stop_mapping_button.setProperty("active", not ctrl.running and not ctrl.busy)
            
            self.start_mapping_button.style().polish(self.start_mapping_button)
            self.stop_mapping_button.style().polish(self.stop_mapping_button)
            self.save_map_button.style().polish(self.save_map_button)