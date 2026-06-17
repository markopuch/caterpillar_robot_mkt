#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULE_SOURCE="${PROJECT_DIR}/udev/99-roboclaw.rules"
RULE_TARGET="/etc/udev/rules.d/99-roboclaw.rules"

if ! command -v sudo >/dev/null 2>&1; then
  SUDO=""
else
  SUDO="sudo"
fi

if [ ! -f "${RULE_SOURCE}" ]; then
  echo "ERROR: udev rule not found: ${RULE_SOURCE}"
  exit 1
fi

${SUDO} cp "${RULE_SOURCE}" "${RULE_TARGET}"
${SUDO} udevadm control --reload-rules
${SUDO} udevadm trigger

echo "RoboClaw udev rule installed for /dev/ttyACM0."
echo "Disconnect and reconnect the RoboClaw USB cable."
echo "Verify with:"
echo "  ls -l /dev/ttyACM0"
