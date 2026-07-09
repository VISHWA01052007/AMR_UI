"""
map_widget.py
--------------
Renders custom maps and layers vector strings matching selected interactive focus tools.
Handles robust view scaling inside the native resize window framework.
"""

import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
from PyQt6.QtGui import QPainter, QImage, QPixmap, QColor, QPen, QBrush, QTransform, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QRectF
from nav_msgs.msg import OccupancyGrid

class MapWidget(QWidget):
    def __init__(self, map_controller, navigation_controller) -> None:
        super().__init__()
        self._controller = map_controller
        self._nav_controller = navigation_controller
        self.setObjectName("MapWidget")
        
        self._map_pixmap: QPixmap = None
        self._robot_x: float = 0.0
        self._robot_y: float = 0.0
        self._robot_yaw: float = 0.0
        
        self._zoom_factor: float = 1.0
        self._pan_x: float = 0.0
        self._pan_y: float = 0.0
        self._rotation_angle: float = 0.0
        self._initial_fit_done: bool = False
        
        self._is_panning: bool = False
        self._is_placing_pose: bool = False
        self._last_mouse_pos = QPointF()
        
        self._drag_start_world = QPointF()
        self._drag_current_world = QPointF()

        self._controller.map_updated.connect(self._on_map_updated)
        self._controller.pose_updated.connect(self._on_pose_updated)
        self._nav_controller.state_changed.connect(self.canvas_update_slot)

        self._setup_layout()

    def canvas_update_slot(self) -> None:
        self.canvas.update()

    def _setup_layout(self) -> None:
        self.setMinimumSize(500, 500)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.canvas = QWidget()
        self.canvas.setMouseTracking(True)
        self.canvas.paintEvent = self._canvas_paint_event
        self.canvas.mousePressEvent = self._canvas_mouse_press
        self.canvas.mouseMoveEvent = self._canvas_mouse_move
        self.canvas.mouseReleaseEvent = self._canvas_mouse_release
        self.canvas.wheelEvent = self._canvas_wheel_event
        self.canvas.resizeEvent = self._on_canvas_resized
        
        toolbar = self._build_toolbar()
        main_layout.addWidget(toolbar, stretch=0)
        main_layout.addWidget(self.canvas, stretch=1)

    def _build_toolbar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("MapToolbar")
        frame.setStyleSheet("QFrame#MapToolbar { background-color: #151518; border-bottom: 1px solid #2e2e36; }")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        btn_rot_left = QPushButton("⟲ Rotate Left")
        btn_rot_right = QPushButton("⟳ Rotate Right")
        btn_rot_left.clicked.connect(lambda: self._modify_rotation(-90))
        btn_rot_right.clicked.connect(lambda: self._modify_rotation(90))
        
        layout.addWidget(btn_rot_left)
        layout.addWidget(btn_rot_right)
        return frame

    def _fit_map_to_canvas(self) -> None:
        map_msg = self._controller.latest_map
        if not map_msg or not self._map_pixmap:
            return
            
        width = map_msg.info.width
        height = map_msg.info.height
        canvas_w = self.canvas.width()
        canvas_h = self.canvas.height()
        
        if canvas_w > 0 and canvas_h > 0:
            self._zoom_factor = min(canvas_w / width, canvas_h / height)
            self._pan_x = 0.0
            self._pan_y = 0.0
            self._initial_fit_done = True

    def _on_canvas_resized(self, event) -> None:
        if self._map_pixmap and not self._initial_fit_done:
            self._fit_map_to_canvas()

    def _on_map_updated(self, msg: OccupancyGrid) -> None:
        if msg is None:
            self._map_pixmap = None
            self._initial_fit_done = False
            
            self._zoom_factor = 1.0
            self._pan_x = 0.0
            self._pan_y = 0.0
            self._rotation_angle = 0.0
            
            self.canvas.update()
            return
            
        width, height = msg.info.width, msg.info.height
        rgb_data = bytearray(width * height * 3)
        for i, val in enumerate(msg.data):
            idx = i * 3
            if val == 0:
                rgb_data[idx], rgb_data[idx+1], rgb_data[idx+2] = 40, 120, 255
            elif val == 100:
                rgb_data[idx], rgb_data[idx+1], rgb_data[idx+2] = 255, 60, 60
            else:
                rgb_data[idx], rgb_data[idx+1], rgb_data[idx+2] = 20, 20, 20

        qimg = QImage(rgb_data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
        self._map_pixmap = QPixmap.fromImage(qimg.mirrored(False, True))
        
        if not self._initial_fit_done:
            self._fit_map_to_canvas()
            
        self.canvas.update()

    def _on_pose_updated(self, x: float, y: float, yaw: float) -> None:
        self._robot_x, self._robot_y, self._robot_yaw = x, y, yaw
        self.canvas.update()

    def _modify_rotation(self, angle: float) -> None:
        if self._nav_controller and self._nav_controller.interaction_mode in ["INITIAL_POSE", "GOAL_SELECTION"]:
            return  
        self._rotation_angle = (self._rotation_angle + angle) % 360
        self.canvas.update()

    def _get_transforms(self) -> tuple[QTransform, QTransform]:
        map_msg = self._controller.latest_map
        w = map_msg.info.width if map_msg else 100
        h = map_msg.info.height if map_msg else 100

        fwd = QTransform()
        fwd.translate(self.canvas.width() / 2.0 + self._pan_x, self.canvas.height() / 2.0 + self._pan_y)
        fwd.rotate(self._rotation_angle)
        fwd.scale(self._zoom_factor, self._zoom_factor)
        fwd.translate(-w / 2.0, -h / 2.0)
        
        inv, _ = fwd.inverted()
        return fwd, inv

    def _pixel_to_world(self, pixel_pt: QPointF) -> QPointF:
        map_msg = self._controller.latest_map
        if not map_msg: return QPointF()
        
        _, inv_matrix = self._get_transforms()
        map_pt = inv_matrix.map(pixel_pt)
        flipped_y = map_msg.info.height - map_pt.y()
        
        world_x = map_msg.info.origin.position.x + (map_pt.x() * map_msg.info.resolution)
        world_y = map_msg.info.origin.position.y + (flipped_y * map_msg.info.resolution)
        return QPointF(world_x, world_y)

    def _world_to_map_pixels(self, wx: float, wy: float) -> tuple[float, float]:
        map_msg = self._controller.latest_map
        mx = (wx - map_msg.info.origin.position.x) / map_msg.info.resolution
        my = map_msg.info.height - ((wy - map_msg.info.origin.position.y) / map_msg.info.resolution)
        return mx, my

    def _canvas_wheel_event(self, event) -> None:
        if self._nav_controller and self._nav_controller.interaction_mode in ["INITIAL_POSE", "GOAL_SELECTION"]:
            return  
        factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self._zoom_factor = max(0.05, min(50.0, self._zoom_factor * factor))
        self.canvas.update()

    def _canvas_mouse_press(self, event) -> None:
        if self._nav_controller and self._nav_controller.interaction_mode in ["INITIAL_POSE", "GOAL_SELECTION"]:
            self._is_placing_pose = True
            self._drag_start_world = self._pixel_to_world(event.position())
            self._drag_current_world = self._drag_start_world
        elif event.button() == Qt.MouseButton.LeftButton:
            self._is_panning = True
            self._last_mouse_pos = event.position()

    def _canvas_mouse_move(self, event) -> None:
        if self._is_placing_pose:
            self._drag_current_world = self._pixel_to_world(event.position())
            self.canvas.update()
        elif self._is_panning:
            delta = event.position() - self._last_mouse_pos
            self._pan_x += delta.x()
            self._pan_y += delta.y()
            self._last_mouse_pos = event.position()
            self.canvas.update()

    def _canvas_mouse_release(self, event) -> None:
        if self._is_placing_pose and self._nav_controller:
            self._is_placing_pose = False
            self._drag_current_world = self._pixel_to_world(event.position())
            
            # ✅ FIX: Get the exact map pixel coordinates of the drag endpoints to avoid transformation bugs
            smx, smy = self._world_to_map_pixels(self._drag_start_world.x(), self._drag_start_world.y())
            cmx, cmy = self._world_to_map_pixels(self._drag_current_world.x(), self._drag_current_world.y())
            
            # Calculate delta directly in map pixel space (where Y points down)
            pm_dx = cmx - smx
            pm_dy = cmy - smy
            
            # Convert screen delta to clean ROS world yaw (negate Y because world Y is up)
            yaw = math.atan2(-pm_dy, pm_dx)

            if self._nav_controller.interaction_mode == "INITIAL_POSE":
                self._nav_controller.publish_initial_pose(self._drag_start_world.x(), self._drag_start_world.y(), yaw)
            elif self._nav_controller.interaction_mode == "GOAL_SELECTION":
                self._nav_controller.set_pending_goal(self._drag_start_world.x(), self._drag_start_world.y(), yaw)
                
        elif event.button() == Qt.MouseButton.LeftButton:
            self._is_panning = False

    def _draw_direction_arrow(self, painter: QPainter, start_map: QPointF, end_map: QPointF, base_color: QColor) -> None:
        """Paints a highly legible, anti-aliased solid directional arrow with downscaled industrial proportions."""
        dx = end_map.x() - start_map.x()
        dy = end_map.y() - start_map.y()
        length = math.hypot(dx, dy)
        
        if length < 1e-3:
            return

        angle = math.atan2(dy, dx)

        scaled_head_len = max(10.0, min(25.0, 14.0 * self._zoom_factor))
        scaled_head_width = scaled_head_len * 0.70
        shaft_thickness = max(1.5, min(5.0, 2.5 * self._zoom_factor))

        painter.save()
        painter.translate(start_map)
        painter.rotate(math.degrees(angle))

        # 1. Background Glow Pass Configuration
        glow_color = QColor(base_color.red(), base_color.green(), base_color.blue(), 35)
        glow_shaft = QPen(glow_color, shaft_thickness * 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(glow_shaft)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(0, 0), QPointF(length - scaled_head_len, 0))

        glow_poly = QPolygonF([
            QPointF(length, 0),
            QPointF(length - scaled_head_len, -scaled_head_width * 0.7),
            QPointF(length - scaled_head_len, scaled_head_width * 0.7)
        ])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow_color))
        painter.drawPolygon(glow_poly)

        # 2. Foreground Core Arrow Vector Pass Configuration
        core_color = QColor(base_color.red(), base_color.green(), base_color.blue(), 230)
        core_shaft = QPen(core_color, shaft_thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(core_shaft)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(0, 0), QPointF(length - scaled_head_len, 0))

        core_poly = QPolygonF([
            QPointF(length, 0),
            QPointF(length - scaled_head_len, -scaled_head_width / 2.0),
            QPointF(length - scaled_head_len, scaled_head_width / 2.0)
        ])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(core_color))
        painter.drawPolygon(core_poly)

        painter.restore()

    def _canvas_paint_event(self, event) -> None:
        painter = QPainter(self.canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        painter.fillRect(self.canvas.rect(), QColor("#1c1c1f"))
        map_msg = self._controller.latest_map
        if map_msg is None or self._map_pixmap is None:
            painter.setPen(QColor("#ffffff"))
            painter.drawText(self.canvas.rect(), Qt.AlignmentFlag.AlignCenter, "Waiting for /map data...")
            return

        fwd_matrix, _ = self._get_transforms()
        painter.setTransform(fwd_matrix)

        # 1. Base Map Rendering
        painter.drawPixmap(0, 0, self._map_pixmap)

        # 2. Render Live Paths Track from /plan
        if self._nav_controller and self._nav_controller.global_path_points:
            path_pen = QPen(QColor("#2196f3"), max(1, int(1.5 / self._zoom_factor)))
            painter.setPen(path_pen)
            for i in range(len(self._nav_controller.global_path_points) - 1):
                p1_w, p2_w = self._nav_controller.global_path_points[i], self._nav_controller.global_path_points[i+1]
                m1x, m1y = self._world_to_map_pixels(p1_w[0], p1_w[1])
                m2x, m2y = self._world_to_map_pixels(p2_w[0], p2_w[1])
                painter.drawLine(QPointF(m1x, m1y), QPointF(m2x, m2y))

        # 3. Render Persistent Local Pending Goal Target Preview
        if self._nav_controller and self._nav_controller.pending_goal:
            pgx, pgy, pgyaw = self._nav_controller.pending_goal
            pmx, pmy = self._world_to_map_pixels(pgx, pgy)
            
            arrow_len_pixels = 35.0
            pemx = pmx + arrow_len_pixels * math.cos(pgyaw)
            pemy = pmy - arrow_len_pixels * math.sin(pgyaw) # minus because map coordinates run downwards
            
            self._draw_direction_arrow(painter, QPointF(pmx, pmy), QPointF(pemx, pemy), QColor("#2196F3"))

        # 4. Render Static Confirmed Execution Targets Marker Box
        if self._nav_controller and self._nav_controller.active_goal:
            gx, gy, gyaw = self._nav_controller.active_goal
            gmx, gmy = self._world_to_map_pixels(gx, gy)
            painter.save()
            painter.translate(gmx, gmy)
            painter.rotate(math.degrees(-gyaw))
            painter.setPen(QPen(QColor("#ea2027"), 1))
            painter.setBrush(QBrush(QColor("#ea2027")))
            rad = 5.0
            painter.drawLine(int(-rad), int(-rad), int(rad), int(rad))
            painter.drawLine(int(-rad), int(rad), int(rad), int(-rad))
            painter.restore()

        # 5. Render Active Mouse Drag Placement Vector Tracks
        if self._is_placing_pose and self._nav_controller:
            smx, smy = self._world_to_map_pixels(self._drag_start_world.x(), self._drag_start_world.y())
            cmx, cmy = self._world_to_map_pixels(self._drag_current_world.x(), self._drag_current_world.y())
            
            start_map_pt = QPointF(smx, smy)
            end_map_pt = QPointF(cmx, cmy)
            
            if self._nav_controller.interaction_mode == "INITIAL_POSE":
                self._draw_direction_arrow(painter, start_map_pt, end_map_pt, QColor("#4CAF50")) 
            elif self._nav_controller.interaction_mode == "GOAL_SELECTION":
                self._draw_direction_arrow(painter, start_map_pt, end_map_pt, QColor("#2196F3")) 

        # 6. Render Active Robot Chassis Base Circle
        rx, ry = self._world_to_map_pixels(self._robot_x, self._robot_y)
        painter.save()
        painter.translate(rx, ry)
        painter.rotate(math.degrees(-self._robot_yaw))
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(QBrush(QColor("#ff4757")))
        marker_radius = max(4.0, 6.0 / self._zoom_factor) if self._zoom_factor < 1.0 else 6.0
        painter.drawEllipse(QRectF(-marker_radius, -marker_radius, marker_radius * 2, marker_radius * 2))
        painter.setPen(QPen(QColor("#ffa502"), 2))
        painter.drawLine(0, 0, int(marker_radius * 1.5), 0)
        painter.restore()