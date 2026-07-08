"""
ui_node.py
-----------
Application entry point for the AMR dashboard UI.
Manages ROS2 communication interfaces and robust Linux Process Group lifecycles.
"""

import sys
import math
import shlex
import subprocess
import os
import signal
import time
from pathlib import Path
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped, PoseStamped
from nav_msgs.msg import Odometry, OccupancyGrid, Path as RosPath

from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from .main_window import MainWindow
from .controllers.manual_controller import ManualController
from .controllers.robot_status_controller import RobotStatusController
from .controllers.map_controller import MapController
from .controllers.slam_controller import SlamController
from .controllers.navigation_controller import NavigationController
from .config import settings

RESOURCES_DIR = Path(__file__).resolve().parent / "resources"
STYLESHEET_PATH = RESOURCES_DIR / "style.qss"


class ROS2Worker(QThread):
    def __init__(self, node: Node) -> None:
        super().__init__()
        self._node = node

    def run(self) -> None:
        try: 
            rclpy.spin(self._node)
        except Exception: 
            pass


class UINode(Node):
    def __init__(self) -> None:
        super().__init__("amr_ui_node")
        print("\n=== [DEBUG UINODE] INITIALIZING CORE WORKSPACE ===")
        
        self._current_operation_mode: str = "IDLE"
        self._slam_process: subprocess.Popen | None = None
        self._navigation_process: subprocess.Popen | None = None

        # 1. Permanent Communications Channels (Always Alive Infrastructure)
        self._cmd_vel_pub = self.create_publisher(Twist, settings.CMD_VEL_TOPIC, 10)
        self._odom_sub = self.create_subscription(Odometry, settings.ODOM_TOPIC, self.odom_callback, 10)
        
        self._initial_pose_pub = self.create_publisher(PoseWithCovarianceStamped, settings.INITIAL_POSE_TOPIC, 10)
        self._goal_pose_pub = self.create_publisher(PoseStamped, settings.GOAL_POSE_TOPIC, 10)

        map_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )

        print("[DEBUG UINODE] Initializing thread-safe core network subscriptions...")
        self._map_sub = self.create_subscription(OccupancyGrid, "/map", self.map_callback, map_qos)
        self._plan_sub = self.create_subscription(RosPath, settings.GLOBAL_PLAN_TOPIC, self.plan_callback, 10)

        # 2. Permanent Transform Listeners & Internal Permanent Timer
        from tf2_ros import Buffer, TransformListener
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._pose_timer = self.create_timer(0.1, self.lookup_robot_pose_callback)

        # 3. Domain State Machine Controllers
        self._manual_controller = ManualController(publish_callback=self.publish_cmd_vel)
        self._robot_status_controller = RobotStatusController()
        self._map_controller = MapController()
        self._slam_controller = SlamController()
        self._navigation_controller = NavigationController()

        # 4. Bind Signal Routing Actions
        self._slam_controller.start_requested.connect(self.handle_slam_start)
        self._slam_controller.stop_requested.connect(self.handle_slam_stop)
        self._slam_controller.save_requested.connect(self.handle_slam_save)
        
        self._navigation_controller.toggle_requested.connect(self._on_navigation_toggle_triggered)
        self._navigation_controller.initial_pose_published.connect(self.publish_initial_pose_msg)
        self._navigation_controller.goal_pose_published.connect(self.publish_goal_pose_msg)
        self._navigation_controller.abort_requested.connect(self.handle_navigation_abort)

        self.window = None
        print("=== [DEBUG UINODE] CORE WORKSPACE INITIALIZED. STANDING BY FOR WINDOW SEED ===\n")

    def init_ui(self) -> None:
        self.window = MainWindow(
            manual_controller=self._manual_controller,
            robot_status_controller=self._robot_status_controller,
            map_controller=self._map_controller,
            slam_controller=self._slam_controller,
            navigation_controller=self._navigation_controller
        )
        self.window.show()

    def request_mode_transition(self, target_mode: str) -> bool:
        if target_mode == self._current_operation_mode:
            return True
        print(f"[DEBUG UINODE] Request transition: {self._current_operation_mode} -> {target_mode}")
        
        if target_mode == "SLAM":
            self._slam_controller.update_execution_state(running=False, busy=False, locked=False)
            self._navigation_controller.update_execution_state(running=False, busy=False, locked=True)
        elif target_mode == "NAVIGATION":
            self._slam_controller.update_execution_state(running=False, busy=False, locked=True)
            self._navigation_controller.update_execution_state(running=False, busy=False, locked=False)
        elif target_mode == "IDLE":
            self._slam_controller.update_execution_state(running=False, busy=False, locked=False)
            self._navigation_controller.update_execution_state(running=False, busy=False, locked=False)
            
        self._current_operation_mode = target_mode
        return True

    # --- SLAM Managers ---
    def handle_slam_start(self) -> None:
        self.request_mode_transition("SLAM")
        print(f"[DEBUG UINODE] Executing SLAM Start Command: {settings.SLAM_START_COMMAND}")
        try:
            cmd = shlex.split(settings.SLAM_START_COMMAND)
            self._slam_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
            self._slam_controller.update_execution_state(running=True, busy=False)
        except Exception: 
            self.request_mode_transition("IDLE")

    def handle_slam_stop(self) -> None:
        print("[DEBUG UINODE] Initializing SLAM Process Group shutdown routine...")
        if self._slam_process:
            try: 
                pgid = self._slam_process.pid
                print(f"[DEBUG UINODE] Sending SIGTERM to process group PGID: {pgid}")
                os.killpg(pgid, signal.SIGTERM)
                self._slam_process.wait(timeout=1.0)
            except Exception: pass
            self._slam_process = None
        self.request_mode_transition("IDLE")

    def handle_slam_save(self, filename: str) -> None:
        try:
            cmd = shlex.split(f"{settings.SLAM_SAVE_COMMAND_BASE} {filename}")
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5.0)
        except Exception: pass
        self._slam_controller.update_execution_state(running=True, busy=False)

    # --- Navigation Toggle Lifecycle Routing ---
    def _on_navigation_toggle_triggered(self, checked: bool, map_path: str) -> None:
        if checked: self.handle_navigation_start(map_path)
        else: self.handle_navigation_stop()

    def handle_navigation_start(self, map_path: str) -> None:
        self.request_mode_transition("NAVIGATION")
        full_command_str = settings.NAVIGATION_START_COMMAND_TEMPLATE.format(map_path=map_path)
        print(f"[DEBUG UINODE] Launching Navigation Process Group: {full_command_str}")
        try:
            cmd = shlex.split(full_command_str)
            self._navigation_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
            self._navigation_controller.update_execution_state(running=True, busy=False)
        except Exception:
            self._navigation_process = None
            self.request_mode_transition("IDLE")

    def handle_navigation_stop(self) -> None:
        print("[DEBUG UINODE] Terminating Navigation Process Group...")
        if self._navigation_process:
            try: 
                pgid = self._navigation_process.pid
                print(f"[DEBUG UINODE] Sending SIGTERM to navigation group PGID: {pgid}")
                os.killpg(pgid, signal.SIGTERM)
                self._navigation_process.wait(timeout=1.0)
            except Exception: pass
            self._navigation_process = None
        self.request_mode_transition("IDLE")

    def handle_navigation_abort(self) -> None:
        print("[DEBUG UINODE] Navigation goals track flushed.")

    # --- Math Vector Publishers Mapping ---
    def publish_initial_pose_msg(self, x: float, y: float, yaw: float) -> None:
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.06
        self._initial_pose_pub.publish(msg)
        print("[DEBUG UINODE] /initialpose message fired to the network.")

    def publish_goal_pose_msg(self, x: float, y: float, yaw: float) -> None:
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.orientation.z = math.sin(yaw / 2.0)
        msg.pose.orientation.w = math.cos(yaw / 2.0)
        self._goal_pose_pub.publish(msg)
        print("[DEBUG UINODE] /goal_pose message fired to the network.")

    # --- Callbacks (Decoupled & Context-Aware Filters) ---
    def plan_callback(self, msg: RosPath) -> None:
        if self._current_operation_mode != "NAVIGATION":
            return
        pts = [[p.pose.position.x, p.pose.position.y] for p in msg.poses]
        self._navigation_controller.set_global_plan(pts)

    def publish_cmd_vel(self, linear: float, angular: float) -> None:
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self._cmd_vel_pub.publish(msg)

    def odom_callback(self, msg: Odometry) -> None:
        self._robot_status_controller.update(msg.twist.twist.linear.x, msg.twist.twist.angular.z)

    def map_callback(self, msg: OccupancyGrid) -> None:
        # ✅ Always update map whenever it is available on the network
        self._map_controller.set_map(msg)

    def lookup_robot_pose_callback(self) -> None:
        # ✅ Always lookup and update robot pose to handle manual teleoperation anytime
        for base_frame in ['base_footprint', 'base_link']:
            try:
                trans = self._tf_buffer.lookup_transform('map', base_frame, rclpy.time.Time())
                pos = trans.transform.translation
                rot = trans.transform.rotation
                siny_cosp = 2.0 * (rot.w * rot.z + rot.x * rot.y)
                cosy_cosp = 1.0 - 2.0 * (rot.y * rot.y + rot.z * rot.z)
                yaw = math.atan2(siny_cosp, cosy_cosp)
                self._map_controller.set_robot_pose(pos.x, pos.y, yaw)
                return
            except Exception:
                continue


def load_stylesheet(app: QApplication) -> None:
    if STYLESHEET_PATH.exists():
        style_data = STYLESHEET_PATH.read_text(encoding="utf-8")
        resolved_icons_dir = str(RESOURCES_DIR).replace("\\", "/")
        style_data = style_data.replace("{{ICONS_DIR}}", resolved_icons_dir)
        app.setStyleSheet(style_data)


def main(args=None) -> None:
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    load_stylesheet(app)
    
    ui_node = UINode()
    ros2_thread = ROS2Worker(ui_node)
    ros2_thread.start()
    
    ui_node.init_ui()
    exit_code = app.exec()
    
    if ui_node._slam_process: ui_node.handle_slam_stop()
    if ui_node._navigation_process: ui_node.handle_navigation_stop()
    rclpy.shutdown()
    ros2_thread.wait()
    ui_node.destroy_node()
    sys.exit(exit_code)