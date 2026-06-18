#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="jazzy"
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

source "/opt/ros/${ROS_DISTRO}/setup.bash"
source "${WORKSPACE}/install/setup.bash"

exec ros2 launch caterpillar_bringup interface.launch.py
