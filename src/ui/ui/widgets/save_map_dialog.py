"""
save_map_dialog.py
------------------
A tailored, theme-compliant custom modal window matching industrial HMI design rules.
Centering occurs automatically relative to its parent geometry window.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget
)

class SaveMapDialog(QDialog):
    """Custom dialogue window providing complete thematic design control for map saving routines."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Save Map")
        self.setFixedSize(500, 220)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Main Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Prompt Field Label
        label = QLabel("Map Filename")
        label.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 11px; font-weight: 700; color: #9ecaff; letter-spacing: 1px;")

        # Custom text entry field inheriting system styling rules safely
        self.filename_edit = QLineEdit()
        self.filename_edit.setText("map1")
        self.filename_edit.setMinimumHeight(36)
        self.filename_edit.setStyleSheet(
            "QLineEdit { background-color: #0e0e0e; border: 1px solid rgba(64, 71, 82, 0.55); "
            "border-radius: 6px; color: #e5e2e1; font-family: 'JetBrains Mono'; padding-left: 10px; font-size: 13px; }"
            "QLineEdit:focus { border: 1px solid #9ecaff; }"
        )

        # Control Row Layout Setup
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("styleClass", "secondaryAction")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setMinimumSize(100, 36)

        self.save_button = QPushButton("Save")
        self.save_button.setProperty("styleClass", "primaryAction")
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.setMinimumSize(100, 36)

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        layout.addWidget(label)
        layout.addWidget(self.filename_edit)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.adjustSize()

    def get_filename(self) -> str:
        """Returns the clean string payload from the interactive text layout editor."""
        return self.filename_edit.text().strip()

    def showEvent(self, event) -> None:
        """Overrides the layout event tree to anchor coordinates precisely in the application center."""
        super().showEvent(event)
        if self.parent():
            parent_geo = self.parent().frameGeometry()
            self.move(
                parent_geo.center().x() - self.width() // 2,
                parent_geo.center().y() - self.height() // 2
            )