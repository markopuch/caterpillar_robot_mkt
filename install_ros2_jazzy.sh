#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="jazzy"

if ! command -v sudo >/dev/null 2>&1; then
  SUDO=""
else
  SUDO="sudo"
fi

echo "Installing ROS 2 ${ROS_DISTRO}"

${SUDO} apt update
${SUDO} apt install -y \
  curl \
  gnupg \
  lsb-release \
  software-properties-common

${SUDO} add-apt-repository -y universe
${SUDO} install -d -m 0755 /usr/share/keyrings
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  | ${SUDO} tee /usr/share/keyrings/ros-archive-keyring.gpg >/dev/null

UBUNTU_CODENAME="$(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")"
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu ${UBUNTU_CODENAME} main" \
  | ${SUDO} tee /etc/apt/sources.list.d/ros2.list >/dev/null

${SUDO} apt update
${SUDO} apt install -y "ros-${ROS_DISTRO}-ros-base"

if ! grep -q "source /opt/ros/${ROS_DISTRO}/setup.bash" "${HOME}/.bashrc"; then
  echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> "${HOME}/.bashrc"
fi

echo "ROS 2 ${ROS_DISTRO} installation complete."
