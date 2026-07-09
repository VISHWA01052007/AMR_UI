"""
mission_log_widget.py
---------------------
Scrollable mission/event log panel.
Appends live entries dynamically as formatted HTML text blocks.
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QTextCursor


class MissionLogWidget(QFrame):
    """Panel with a scrollable, read-only mission event log."""

    def __init__(self, controller=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MissionLogWidget")
        self.setProperty("panel", True)
        
        self._controller = controller
        self._build_ui()

        # ✅ Safe Injection Mapping Hook
        if self._controller is not None:
            self._controller.message_added.connect(self.append_log_entry)
            self._pre_populate_existing_logs()
        else:
            # Symmetrical fallback if no controller dependency is active yet
            self.log_text_edit.setHtml(
                '<div style="color:#89919d; margin:2px 0;">[00:00:00] Waiting for System core initialization...</div>'
            )

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        # --- Header row ---------------------------------------------------
        header_row = QHBoxLayout()
        title_label = QLabel("MISSION LOG")
        title_label.setProperty("panelTitle", True)
        header_row.addWidget(title_label)
        header_row.addStretch(1)

        terminal_icon = QLabel("\U0001F5A5")  # terminal glyph
        terminal_icon.setProperty("panelSubIcon", True)
        header_row.addWidget(terminal_icon)
        outer.addLayout(header_row)

        # --- Log body -------------------------------------------------------
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setObjectName("MissionLogText")
        self.log_text_edit.setReadOnly(True)
        outer.addWidget(self.log_text_edit, stretch=1)

    def _pre_populate_existing_logs(self) -> None:
        """Populates the text field if items exist prior to panel registration."""
        for timestamp, message, level in self._controller.logs:
            self.append_log_entry(timestamp, message, level)

    # ------------------------------------------------------------------ #
    # Live Logging API Matrix
    # ------------------------------------------------------------------ #
    def append_log_entry(self, timestamp: str, message: str, level: str) -> None:
        """Appends formatted HTML log blocks directly into the viewport."""
        
        # Color profile mapping matching your design rules
        if level == "warning":
            color_hex = "#ffb4ab"      # Light Orange/Red warning text
            time_hex = "#ffb4ab"
        elif level == "success":
            color_hex = "#4CAF50"      # Industrial Green success indicator
            time_hex = "#89919d"
        elif level == "error":
            color_hex = "#ea2027"      # Critical Crimson error notification
            time_hex = "#ea2027"
        else:
            color_hex = "#e5e2e1"      # Uniform light grey text
            time_hex = "#89919d"       # Dark grey timestamp bracket text

        html_block = (
            f'<div style="margin:2px 0; font-family: \'JetBrains Mono\'; font-size: 12px;">'
            f'<span style="color:{time_hex};">[{timestamp}]</span> '
            f'<span style="color:{color_hex};">{message}</span>'
            f'</div>'
        )

        # Append HTML without resetting the view buffer cursor focus positions
        self.log_text_edit.append(html_block)
        
        # Ensure scroll follows latest telemetry events automatically
        self.log_text_edit.moveCursor(QTextCursor.MoveOperation.End)