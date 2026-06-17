#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="${ROS_DISTRO:-jazzy}"
if [ "${ROS_DISTRO}" != "jazzy" ]; then
  echo "ERROR: este proyecto debe ejecutarse con ROS_DISTRO=jazzy."
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$(basename "$(dirname "${PROJECT_DIR}")")" = "src" ]; then
  WORKSPACE="${WORKSPACE:-$(dirname "$(dirname "${PROJECT_DIR}")")}"
else
  WORKSPACE="${WORKSPACE:-${PROJECT_DIR}}"
fi

MODE="${1:-robot}"
PORT="${PORT:-/dev/ttyACM0}"

if [ ! -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  echo "ERROR: falta /opt/ros/${ROS_DISTRO}/setup.bash."
  echo "Ejecuta primero: ${PROJECT_DIR}/install_raspberry.sh"
  exit 1
fi

if [ ! -f "${WORKSPACE}/install/setup.bash" ]; then
  echo "ERROR: falta ${WORKSPACE}/install/setup.bash."
  echo "Compila primero:"
  echo "  cd ${WORKSPACE}"
  echo "  source /opt/ros/${ROS_DISTRO}/setup.bash"
  echo "  colcon build --symlink-install"
  exit 1
fi

source "/opt/ros/${ROS_DISTRO}/setup.bash"
source "${WORKSPACE}/install/setup.bash"

case "${MODE}" in
  robot)
    exec ros2 launch roboclaw_ros2 mobile_robot.launch.py port:="${PORT}"
    ;;
  all)
    exec ros2 launch roboclaw_ros2 mobile_robot.launch.py port:="${PORT}" start_control_gui:=true
    ;;
  gui)
    exec ros2 run interface_pc interface_pc
    ;;
  face)
    exec ros2 run interface_rpi interface_rpi
    ;;
  roboclaw)
    exec ros2 run roboclaw_ros2 roboclaw_node --ros-args -p port:="${PORT}"
    ;;
  build)
    cd "${WORKSPACE}"
    exec colcon build --symlink-install
    ;;
  *)
    echo "Uso: $0 [robot|all|gui|face|roboclaw|build]"
    echo
    echo "Ejemplos:"
    echo "  $0 robot              # RoboClaw + pantalla HDMI"
    echo "  $0 all                # RoboClaw + pantalla HDMI + interfaz"
    echo "  $0 gui                # solo interfaz de control"
    echo "  PORT=/dev/ttyACM1 $0 robot"
    exit 2
    ;;
esac
