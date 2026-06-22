#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="${ROS_DISTRO:-jazzy}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "${PROJECT_DIR}/../../.." && pwd)"

if [ ! -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  echo "ERROR: ROS 2 ${ROS_DISTRO} is not installed."
  exit 1
fi

if [ ! -f "${WORKSPACE}/install/setup.bash" ]; then
  echo "ERROR: workspace is not built. Run ./shortcuts/build_robot.sh first."
  exit 1
fi

set +u
source "/opt/ros/${ROS_DISTRO}/setup.bash"
source "${WORKSPACE}/install/setup.bash"
set -u

exec ros2 launch caterpillar_bringup web_joystick_robot.launch.py "$@"
