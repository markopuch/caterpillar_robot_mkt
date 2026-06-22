#!/usr/bin/env bash
set -euo pipefail

source "/opt/ros/jazzy/setup.bash"
source "/home/utec/robot_ws/install/setup.bash"

exec ros2 launch roboclaw_ros2 roboclaw_node.launch.py
exec ros2 launch joystick_logitech_f710_gamepad f710_gamepad.launch.py
exec ros2 launch interface_faces_web tablet_face.launch.py