"""
map_controller.py
------------------
Manages raw map data and robot coordinates, emitting clean Qt signals for the UI.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from nav_msgs.msg import OccupancyGrid

class MapController(QObject):
    """Stores the latest map data and robot position, signaling updates to widgets."""
    
    map_updated = pyqtSignal(object)
    pose_updated = pyqtSignal(float, float, float)  # x, y, yaw

    def __init__(self) -> None:
        super().__init__()
        self._latest_map: OccupancyGrid = None
        self._robot_x: float = 0.0
        self._robot_y: float = 0.0
        self._robot_yaw: float = 0.0
        print("[DEBUG MAP_CONTROLLER] Initialized.")

    def set_map(self, msg: OccupancyGrid) -> None:
        """Saves the map message and triggers a UI update."""
        self._latest_map = msg
        self.map_updated.emit(msg)

    def set_robot_pose(self, x: float, y: float, yaw: float) -> None:
        """Saves the robot coordinates and triggers a marker redraw."""
        self._robot_x = x
        self._robot_y = y
        self._robot_yaw = yaw
        self.pose_updated.emit(x, y, yaw)

    def clear_map(self) -> None:
        """Resets all metrics and notifies the widget canvas to render fallback states."""
        print("[DEBUG MAP_CONTROLLER] Executing clear_map(). scrubbing state data...")
        self._latest_map = None
        self._robot_x = 0.0
        self._robot_y = 0.0
        self._robot_yaw = 0.0
        self.map_updated.emit(None)
        self.pose_updated.emit(0.0, 0.0, 0.0)

    @property
    def latest_map(self) -> OccupancyGrid:
        return self._latest_map

    @property
    def robot_pose(self) -> tuple:
        return self._robot_x, self._robot_y, self._robot_yaw