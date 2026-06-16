#!/usr/bin/env python3
"""Minimal ROS 2 speed bridge for a differential RoboClaw base."""

from __future__ import annotations

import math
import time

from basicmicro import Basicmicro
from geometry_msgs.msg import Twist
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32
from std_msgs.msg import Int32


class RoboclawNode(Node):
    """Convert cmd_vel into RoboClaw M1/M2 speed commands."""

    def __init__(self) -> None:
        super().__init__("roboclaw_node")

        self.declare_parameter("port", "/dev/ttyACM0")
        self.declare_parameter("baud", 115200)
        self.declare_parameter("address", 0x80)
        self.declare_parameter("control_rate_hz", 20.0)
        self.declare_parameter("max_speed", 0.5)
        self.declare_parameter("ticks_per_revolution", 2048.0)
        self.declare_parameter("wheel_radius", 0.05)
        self.declare_parameter("base_width", 0.315)
        self.declare_parameter("cmd_vel_timeout", 0.5)
        self.declare_parameter("invert_left_motor", False)
        self.declare_parameter("invert_right_motor", False)

        self.port = str(self.get_parameter("port").value)
        self.baud = int(self.get_parameter("baud").value)
        self.address = int(self.get_parameter("address").value)
        self.control_rate_hz = max(float(self.get_parameter("control_rate_hz").value), 1.0)
        self.max_speed = abs(float(self.get_parameter("max_speed").value))
        self.ticks_per_revolution = float(self.get_parameter("ticks_per_revolution").value)
        self.wheel_radius = float(self.get_parameter("wheel_radius").value)
        self.base_width = float(self.get_parameter("base_width").value)
        self.cmd_vel_timeout = max(float(self.get_parameter("cmd_vel_timeout").value), 0.0)
        self.invert_left_motor = bool(self.get_parameter("invert_left_motor").value)
        self.invert_right_motor = bool(self.get_parameter("invert_right_motor").value)

        self.ticks_per_meter = self._compute_ticks_per_meter()
        self.controller: Basicmicro | None = None
        self._latest_cmd_vel = Twist()
        self._last_cmd_vel_time = 0.0
        self._last_connection_log_ns = 0
        self._last_timeout_log_ns = 0
        self._last_left_ticks: int | None = None
        self._last_right_ticks: int | None = None

        self.create_subscription(Twist, "cmd_vel", self._cmd_vel_callback, 10)
        self.left_mps_pub = self.create_publisher(Float32, "roboclaw/cmd_speed/left", 10)
        self.right_mps_pub = self.create_publisher(Float32, "roboclaw/cmd_speed/right", 10)
        self.left_ticks_pub = self.create_publisher(Int32, "roboclaw/cmd_ticks/left", 10)
        self.right_ticks_pub = self.create_publisher(Int32, "roboclaw/cmd_ticks/right", 10)

        self.create_timer(1.0 / self.control_rate_hz, self._control_loop)

        self.get_logger().info(
            f"RoboClaw speed bridge on {self.port}, address 0x{self.address:02X}"
        )
        self.get_logger().info(
            f"ticks_per_meter={self.ticks_per_meter:.3f}, "
            f"max_speed={self.max_speed:.3f} m/s, base_width={self.base_width:.3f} m"
        )

    def _compute_ticks_per_meter(self) -> float:
        if self.ticks_per_revolution <= 0.0:
            raise ValueError("ticks_per_revolution must be greater than zero")
        if self.wheel_radius <= 0.0:
            raise ValueError("wheel_radius must be greater than zero")
        if self.base_width <= 0.0:
            raise ValueError("base_width must be greater than zero")
        return self.ticks_per_revolution / (2.0 * math.pi * self.wheel_radius)

    def _cmd_vel_callback(self, msg: Twist) -> None:
        self._latest_cmd_vel = msg
        self._last_cmd_vel_time = time.monotonic()

    def _control_loop(self) -> None:
        left_mps, right_mps = self._compute_wheel_speeds()
        left_ticks = int(left_mps * self.ticks_per_meter)
        right_ticks = int(right_mps * self.ticks_per_meter)

        if self.invert_left_motor:
            left_ticks = -left_ticks
        if self.invert_right_motor:
            right_ticks = -right_ticks

        self._publish_float(self.left_mps_pub, left_mps)
        self._publish_float(self.right_mps_pub, right_mps)
        self._publish_int(self.left_ticks_pub, left_ticks)
        self._publish_int(self.right_ticks_pub, right_ticks)

        if not self._connect():
            return

        try:
            self._send_speed_command(left_ticks, right_ticks)
        except Exception as exc:
            self.get_logger().warning(f"RoboClaw speed command failed: {exc}")
            self._close_controller()

    def _compute_wheel_speeds(self) -> tuple[float, float]:
        cmd = self._latest_cmd_vel
        has_recent_cmd = self._last_cmd_vel_time > 0.0 and (
            self.cmd_vel_timeout <= 0.0
            or time.monotonic() - self._last_cmd_vel_time <= self.cmd_vel_timeout
        )

        if not has_recent_cmd:
            self._throttled_timeout_log()
            return 0.0, 0.0

        left_mps = cmd.linear.x - cmd.angular.z * self.base_width * 0.5
        right_mps = cmd.linear.x + cmd.angular.z * self.base_width * 0.5
        return (
            self._clamp(left_mps, -self.max_speed, self.max_speed),
            self._clamp(right_mps, -self.max_speed, self.max_speed),
        )

    def _connect(self) -> bool:
        if self.controller is not None:
            return True

        try:
            controller = Basicmicro(self.port, self.baud)
            if not controller.Open():
                raise RuntimeError("could not open serial port")

            controller.SpeedM1M2(self.address, 0, 0)
            self.controller = controller
            self._last_left_ticks = None
            self._last_right_ticks = None
            self.get_logger().info("Connected to RoboClaw")
            return True
        except Exception as exc:
            self._throttled_connection_warning(exc)
            self._close_controller()
            return False

    def _send_speed_command(self, left_ticks: int, right_ticks: int) -> None:
        if self.controller is None:
            return

        if left_ticks == self._last_left_ticks and right_ticks == self._last_right_ticks:
            return

        self.controller.SpeedM1M2(self.address, int(left_ticks), int(right_ticks))
        self._last_left_ticks = int(left_ticks)
        self._last_right_ticks = int(right_ticks)

    def _close_controller(self) -> None:
        if self.controller is None:
            return

        try:
            self.controller.close()
        except Exception:
            pass
        finally:
            self.controller = None
            self._last_left_ticks = None
            self._last_right_ticks = None

    def _throttled_connection_warning(self, exc: Exception) -> None:
        now_ns = self.get_clock().now().nanoseconds
        if now_ns - self._last_connection_log_ns >= 5_000_000_000:
            self.get_logger().warning(f"Waiting for RoboClaw connection: {exc}")
            self._last_connection_log_ns = now_ns

    def _throttled_timeout_log(self) -> None:
        now_ns = self.get_clock().now().nanoseconds
        if now_ns - self._last_timeout_log_ns >= 5_000_000_000:
            self.get_logger().info("No recent cmd_vel, commanding zero speed")
            self._last_timeout_log_ns = now_ns

    def _publish_float(self, publisher, value: float) -> None:
        msg = Float32()
        msg.data = float(value)
        publisher.publish(msg)

    def _publish_int(self, publisher, value: int) -> None:
        msg = Int32()
        msg.data = int(value)
        publisher.publish(msg)

    def destroy_node(self) -> bool:
        try:
            self._send_speed_command(0, 0)
        except Exception:
            pass
        self._close_controller()
        return super().destroy_node()

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = RoboclawNode()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
