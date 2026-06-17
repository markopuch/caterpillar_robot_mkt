#!/usr/bin/env bash
set -euo pipefail

# Este proyecto esta preparado para ROS 2 Jazzy.
ROS_DISTRO="${ROS_DISTRO:-jazzy}"
if [ "${ROS_DISTRO}" != "jazzy" ]; then
  echo "ERROR: este proyecto debe instalarse con ROS_DISTRO=jazzy."
  echo "Ejemplo: ROS_DISTRO=jazzy ./install_raspberry.sh"
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$(basename "$(dirname "${PROJECT_DIR}")")" = "src" ]; then
  WORKSPACE="${WORKSPACE:-$(dirname "$(dirname "${PROJECT_DIR}")")}"
else
  WORKSPACE="${WORKSPACE:-${PROJECT_DIR}}"
fi

if ! command -v sudo >/dev/null 2>&1; then
  SUDO=""
else
  SUDO="sudo"
fi

echo "Installing Caterpillar Robot dependencies"
echo "ROS_DISTRO=${ROS_DISTRO}"
echo "WORKSPACE=${WORKSPACE}"

${SUDO} apt update
${SUDO} apt install -y \
  curl \
  gnupg \
  lsb-release \
  software-properties-common

if [ ! -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  echo "ROS 2 ${ROS_DISTRO} not found. Installing ROS apt repository and ros-base."
  ${SUDO} add-apt-repository -y universe
  ${SUDO} install -d -m 0755 /usr/share/keyrings
  curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    | ${SUDO} tee /usr/share/keyrings/ros-archive-keyring.gpg >/dev/null

  UBUNTU_CODENAME="$(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")"
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu ${UBUNTU_CODENAME} main" \
    | ${SUDO} tee /etc/apt/sources.list.d/ros2.list >/dev/null

  ${SUDO} apt update
  ${SUDO} apt install -y "ros-${ROS_DISTRO}-ros-base"
fi

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

if ! python3 -m pip install --user --upgrade basicmicro; then
  python3 -m pip install --user --break-system-packages --upgrade basicmicro
fi

if [ -n "${SUDO}" ] && id -nG "${USER}" | tr ' ' '\n' | grep -qx dialout; then
  echo "User ${USER} already belongs to dialout."
elif [ -n "${SUDO}" ]; then
  ${SUDO} usermod -aG dialout "${USER}"
  echo "Added ${USER} to dialout. Log out and back in, or reboot, before using /dev/ttyACM*."
fi

source "/opt/ros/${ROS_DISTRO}/setup.bash"
cd "${WORKSPACE}"

if [ -d src ]; then
  ROSDEP_PATHS="src"
else
  ROSDEP_PATHS="."
fi

rosdep install --from-paths "${ROSDEP_PATHS}" --ignore-src -r -y --rosdistro "${ROS_DISTRO}"
colcon build --symlink-install

if ! grep -q "source /opt/ros/${ROS_DISTRO}/setup.bash" "${HOME}/.bashrc"; then
  echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> "${HOME}/.bashrc"
fi

if ! grep -q "source ${WORKSPACE}/install/setup.bash" "${HOME}/.bashrc"; then
  echo "source ${WORKSPACE}/install/setup.bash" >> "${HOME}/.bashrc"
fi

echo
echo "Installation complete for ROS 2 Jazzy."
echo "Run robot:"
echo "  ${PROJECT_DIR}/run_robot.sh robot"
echo
echo "Run control GUI:"
echo "  ${PROJECT_DIR}/run_robot.sh gui"
