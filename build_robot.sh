#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="jazzy"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$(dirname "${PROJECT_DIR}")")"

if [ ! -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  echo "ERROR: ROS 2 ${ROS_DISTRO} is not installed."
  echo "Run first: ./install_ros2_jazzy.sh"
  exit 1
fi

source "/opt/ros/${ROS_DISTRO}/setup.bash"
cd "${WORKSPACE}"
colcon build --symlink-install

echo "Robot workspace build complete."
