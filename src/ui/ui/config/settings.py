"""
settings.py
------------
Centralized configuration settings and shell commands for the AMR Ecosystem.
"""

DEFAULT_LINEAR_SPEED = 0.45
DEFAULT_ANGULAR_SPEED = 1.0

MAX_LINEAR_SPEED = 2.0
MIN_LINEAR_SPEED = 0.0

MAX_ANGULAR_SPEED = 3.14
MIN_ANGULAR_SPEED = 0.0

LINEAR_SPEED_STEP = 0.05
ANGULAR_SPEED_STEP = 0.1

CMD_VEL_TOPIC = "cmd_vel"
ODOM_TOPIC = "odom"
MAP_TOPIC = "/map"

SLAM_START_COMMAND = "ros2 launch robot_description slam.launch.py"
MAPS_EXPORT_DIR = "/home/vishwa/team007/src/robot_description/maps"
SLAM_SAVE_COMMAND_BASE = "ros2 run nav2_map_server map_saver_cli -f"

NAVIGATION_START_COMMAND_TEMPLATE = 'ros2 launch nav2_bringup bringup_launch.py map:="{map_path}" use_sim_time:=true'

INITIAL_POSE_TOPIC = "/initialpose"
GOAL_POSE_TOPIC = "/goal_pose"
GLOBAL_PLAN_TOPIC = "/plan"

NAV2_ACTION_SERVER = "navigate_to_pose"