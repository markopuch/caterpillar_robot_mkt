from __future__ import annotations

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

from interface_faces_web.face_assets import SUPPORTED_EXPRESSIONS


class FaceDemoNode(Node):
    def __init__(self) -> None:
        super().__init__('face_demo_node')
        self.declare_parameter('topic', '/face/expression')
        self.declare_parameter('period_sec', 2.0)
        topic = str(self.get_parameter('topic').value)
        period_sec = float(self.get_parameter('period_sec').value)

        self.publisher = self.create_publisher(String, topic, 10)
        self.sequence = [
            'idle',
            'happy',
            'talking',
            'listening',
            'thinking',
            'surprised',
            'sad',
            'angry',
            'sleeping',
            'error',
            'idle',
        ]
        self.index = 0
        self.timer = self.create_timer(period_sec, self.publish_next)
        self.get_logger().info(f'Publicando demo en {topic} cada {period_sec:.1f} s')

    def publish_next(self) -> None:
        expression = self.sequence[self.index]
        self.index = (self.index + 1) % len(self.sequence)
        msg = String()
        msg.data = expression
        self.publisher.publish(msg)
        self.get_logger().info(f'Expresion publicada: {expression}')


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = FaceDemoNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
