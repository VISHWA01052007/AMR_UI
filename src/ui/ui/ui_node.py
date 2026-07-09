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
from rclpy.action import ActionClient
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped, PoseStamped
from nav_msgs.msg import Odometry, OccupancyGrid, Path as RosPath
from nav2_msgs.action import NavigateToPose

from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from .main_window import MainWindow
from .controllers.manual_controller import ManualController
from .controllers.robot_status_controller import RobotStatusController
from .controllers.map_controller import MapController
from .controllers.slam_controller import SlamController
from .controllers.navigation_controller import NavigationController
from .controllers.mission_log_controller import MissionLogController
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
        
        # Action feedback memory handle tracking
        self._navigation_goal_handle = None

        # 1. Permanent Communications Channels (Always Alive Infrastructure)
        self._cmd_vel_pub = self.create_publisher(Twist, settings.CMD_VEL_TOPIC, 10)
        self._odom_sub = self.create_subscription(Odometry, settings.ODOM_TOPIC, self.odom_callback, 10)
        self._initial_pose_pub = self.create_publisher(PoseWithCovarianceStamped, settings.INITIAL_POSE_TOPIC, 10)
        
        # UPGRADE: Initializing a robust Action Client instead of a basic topic publisher
        print("[DEBUG UINODE] Spawning Nav2 application action client wrapper...")
        self._nav_action_client = ActionClient(self, NavigateToPose, settings.NAV2_ACTION_SERVER)

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
        # ✅ FIX: Instantiated central logging source of truth first to feed downstream controllers
        self._mission_log_controller = MissionLogController()
        
        self._manual_controller = ManualController(publish_callback=self.publish_cmd_vel)
        self._robot_status_controller = RobotStatusController(mission_log_controller=self._mission_log_controller)
        self._map_controller = MapController()
        self._slam_controller = SlamController(mission_log_controller=self._mission_log_controller)
        self._navigation_controller = NavigationController(mission_log_controller=self._mission_log_controller)

        # 4. Bind Signal Routing Actions
        self._slam_controller.start_requested.connect(self.handle_slam_start)
        self._slam_controller.stop_requested.connect(self.handle_slam_stop)
        self._slam_controller.save_requested.connect(self.handle_slam_save)
        
        self._navigation_controller.toggle_requested.connect(self._on_navigation_toggle_triggered)
        self._navigation_controller.initial_pose_published.connect(self.publish_initial_pose_msg)
        
        # FIX: Direct the goal_pose_published signal to the action dispatcher method
        self._navigation_controller.goal_pose_published.connect(self.send_navigation_action_goal)
        self._navigation_controller.abort_requested.connect(self.handle_navigation_abort)

        self.window = None
        
        # ✅ Notify system ready state milestone on launch complete
        self._mission_log_controller.log_info("Robot is ready.")
        print("=== [DEBUG UINODE] CORE WORKSPACE INITIALIZED. STANDING BY FOR WINDOW SEED ===\n")

    def init_ui(self) -> None:
        self.window = MainWindow(
            manual_controller=self._manual_controller,
            robot_status_controller=self._robot_status_controller,
            map_controller=self._map_controller,
            slam_controller=self._slam_controller,
            navigation_controller=self._navigation_controller,
            mission_log_controller=self._mission_log_controller
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
            self._mission_log_controller.log_error("Unable to start mapping.")
            self.request_mode_transition("IDLE")

    def handle_slam_stop(self) -> None:
        print("[DEBUG UINODE] Initializing SLAM Process Group shutdown routine...")
        if self._slam_process:
            try: 
                pgid = self._slam_process.pid
                print(f"[DEBUG UINODE] Sending SIGTERM to process group PGID: {pgid}")
                os.killpg(pgid, signal.SIGTERM)
                self._slam_process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                print("[WARNING UINODE] SLAM process hung. Escalating to SIGKILL...")
                try:
                    os.killpg(pgid, signal.SIGKILL)
                    self._slam_process.wait()
                except Exception: pass
            except Exception: pass
            self._slam_process = None
        
        self._map_controller.clear_map()
        self.request_mode_transition("IDLE")

    def handle_slam_save(self, filename: str) -> None:
        try:
            cmd = shlex.split(f"{settings.SLAM_SAVE_COMMAND_BASE} {filename}")
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5.0)
            if res.returncode != 0:
                self._mission_log_controller.log_error("Unable to save map.")
        except Exception:
            self._mission_log_controller.log_error("Unable to save map.")
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
            # ✅ Log operational loading confirmation
            self._mission_log_controller.log_success("Map loaded successfully.")
        except Exception:
            self._navigation_process = None
            self._mission_log_controller.log_error("Failed to load map.")
            self.request_mode_transition("IDLE")

    def handle_navigation_stop(self) -> None:
        print("[DEBUG UINODE] Terminating Navigation Process Group...")
        if self._navigation_process:
            try: 
                pgid = self._navigation_process.pid
                print(f"[DEBUG UINODE] Sending SIGTERM to navigation group PGID: {pgid}")
                os.killpg(pgid, signal.SIGTERM)
                self._navigation_process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                print("[WARNING UINODE] Navigation process hung. Escalating to SIGKILL...")
                try:
                    os.killpg(pgid, signal.SIGKILL)
                    self._navigation_process.wait()
                except Exception: pass
            except Exception: pass
            self._navigation_process = None
        self.request_mode_transition("IDLE")

    # FIX: Handle programmatic Nav2 action cancellation when ABORT is pressed
    def handle_navigation_abort(self) -> None:
        print("[DEBUG UINODE] Navigation cancel requested.")
        if self._navigation_goal_handle:
            print("[DEBUG UINODE] Actively canceling the ongoing Nav2 action goal...")
            self._navigation_goal_handle.cancel_goal_async()
            self._navigation_goal_handle = None

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

    # FIX: Replaced topic publishing with an asynchronous action goal dispatch loop
    def send_navigation_action_goal(self, x: float, y: float, yaw: float) -> None:
        """Assembles and dispatches an asynchronous execution request to the Nav2 action server."""
        print("[DEBUG UINODE] Waiting for Nav2 Action Server to stand up...")
        if not self._nav_action_client.wait_for_server(timeout_sec=3.0):
            # ✅ Direct, clear connection error tracking
            self._mission_log_controller.log_error("Unable to connect to robot navigation systems.")
            self._navigation_controller.request_mission_abort()
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        print(f"[DEBUG UINODE] Dispatching action goal asynchronously to Nav2 server -> Target: ({x:.2f}, {y:.2f})")
        send_goal_future = self._nav_action_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future) -> None:
        try:
            goal_handle = future.result()
            if not goal_handle.accepted:
                # ✅ Append direct user notification on path-finding rejection
                self._mission_log_controller.log_error("Destination unreachable.")
                self._navigation_controller.request_mission_abort()
                return

            print("[DEBUG UINODE] Nav2 Action Server accepted our goal coordinates. Tracking feedback loops...")
            self._navigation_goal_handle = goal_handle
            get_result_future = goal_handle.get_result_async()
            get_result_future.add_done_callback(self.goal_result_callback)
        except Exception:
            self._mission_log_controller.log_error("Destination unreachable.")
            self._navigation_controller.request_mission_abort()

    def goal_result_callback(self, future) -> None:
        """Invoked automatically by rclpy when the robot succeeds, fails, or aborts the navigation task."""
        print("[DEBUG UINODE] Action result transaction returned from server.")
        self._navigation_goal_handle = None
        
        # Force the UI state machine controller to fall back safely into IDLE mode bounds
        self._navigation_controller.notify_navigation_completed()

    # --- Callbacks ---
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
        if self._current_operation_mode == "IDLE":
            return
        self._map_controller.set_map(msg)

    def lookup_robot_pose_callback(self) -> None:
        if self._current_operation_mode == "IDLE":
            return
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