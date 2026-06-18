from __future__ import annotations

import sys

import rclpy
from rclpy.utilities import remove_ros_args
from std_msgs.msg import String

from interface_faces_web.face_assets import SUPPORTED_EXPRESSIONS


def main(args: list[str] | None = None) -> None:
    argv = remove_ros_args(args=sys.argv if args is None else args)
    user_args = argv[1:]

    if not user_args:
        print('Uso: ros2 run interface_faces_web set_face_node <expresion> [topic]')
        print('Ejemplo: ros2 run interface_faces_web set_face_node happy')
        return

    expression = user_args[0].strip()
    topic = user_args[1].strip() if len(user_args) > 1 else '/face/expression'

    rclpy.init(args=args)
    node = rclpy.create_node('set_face_node')
    publisher = node.create_publisher(String, topic, 10)

    if expression not in SUPPORTED_EXPRESSIONS:
        node.get_logger().warn(
            f"'{expression}' no esta en la lista soportada; la WebApp deberia usar fallback a idle."
        )

    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.1)

    msg = String()
    msg.data = expression
    publisher.publish(msg)
    node.get_logger().info(f"Expresion publicada en {topic}: {expression}")

    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
