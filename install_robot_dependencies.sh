#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="jazzy"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$(dirname "${PROJECT_DIR}")")"

if ! command -v sudo >/dev/null 2>&1; then
  SUDO=""
else
  SUDO="sudo"
fi

if [ ! -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  echo "ERROR: ROS 2 ${ROS_DISTRO} is not installed."
  echo "Run first: ./install_ros2_jazzy.sh"
  exit 1
fi

echo "Installing robot dependencies for ROS 2 ${ROS_DISTRO}"

${SUDO} apt update
${SUDO} apt install -y \
  python3-colcon-common-extensions \
  python3-pip \
  python3-pyqt5 \
  python3-rosdep \
  python3-serial \
  python3-setuptools \
  python3-venv \
  python3-vcstool \
  libxcb-cursor0 \
  libxcb-xinerama0 \
  x11-xserver-utils \
  "ros-${ROS_DISTRO}-geometry-msgs" \
  "ros-${ROS_DISTRO}-launch" \
  "ros-${ROS_DISTRO}-launch-ros" \
  "ros-${ROS_DISTRO}-rclpy" \
  "ros-${ROS_DISTRO}-std-msgs"

if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  ${SUDO} rosdep init || true
fi
rosdep update

source "/opt/ros/${ROS_DISTRO}/setup.bash"
cd "${WORKSPACE}"
rosdep install --from-paths src --ignore-src -r -y --rosdistro "${ROS_DISTRO}"

if ! python3 -m pip install --user --upgrade basicmicro; then
  python3 -m pip install --user --break-system-packages --upgrade basicmicro
fi

if [ -n "${SUDO}" ] && id -nG "${USER}" | tr ' ' '\n' | grep -qx dialout; then
  echo "User ${USER} already belongs to dialout."
elif [ -n "${SUDO}" ]; then
  ${SUDO} usermod -aG dialout "${USER}"
  echo "Added ${USER} to dialout. Log out and back in, or reboot, before using /dev/ttyACM0."
fi

echo "Robot dependencies installation complete."
