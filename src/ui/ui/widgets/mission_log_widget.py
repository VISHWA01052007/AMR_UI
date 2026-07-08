"""
MissionLogWidget
------------------
Scrollable mission/event log panel.

Phase 1 shows static placeholder log entries. A later phase will append
live entries as ROS2 events (navigation, mapping, obstacle detection,
etc.) occur.
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget

_PLACEHOLDER_LOG_ENTRIES = [
    ("14:20:01", "System initialized. All sensors online.", "normal"),
    ("14:20:05", "Mapping mode enabled. Scanning environment...", "normal"),
    ("14:21:12", "Goal pose received: (x: 12.4, y: -5.2).", "normal"),
    ("14:21:30", "Obstacle detected at 2.5m. Recalculating path.", "warning"),
    ("14:21:35", "Path updated. Resuming navigation.", "normal"),
    ("14:22:00", "Approaching waypoint WP_01.", "normal"),
]


class MissionLogWidget(QFrame):
    """Panel with a scrollable, read-only mission event log."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MissionLogWidget")
        self.setProperty("panel", True)
        self._build_ui()

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
        self.log_text_edit.setHtml(self._render_placeholder_entries())
        outer.addWidget(self.log_text_edit, stretch=1)

    @staticmethod
    def _render_placeholder_entries() -> str:
        rows = []
        for timestamp, message, level in _PLACEHOLDER_LOG_ENTRIES:
            if level == "warning":
                rows.append(
                    f'<div style="margin:2px 0;">'
                    f'<span style="color:#ffb4ab;">[{timestamp}]</span> '
                    f'<span style="color:#ffb4ab;">{message}</span>'
                    f"</div>"
                )
            else:
                rows.append(
                    f'<div style="margin:2px 0;">'
                    f'<span style="color:#89919d;">[{timestamp}]</span> '
                    f'<span style="color:#e5e2e1;">{message}</span>'
                    f"</div>"
                )
        return "".join(rows)

    # ------------------------------------------------------------------ #
    # Placeholder API (Phase 1 — no ROS2 / business logic)
    # ------------------------------------------------------------------ #
    def append_log_entry(self, timestamp: str, message: str, level: str = "normal") -> None:
        """Reserved for a later phase to append live log entries."""
        pass
