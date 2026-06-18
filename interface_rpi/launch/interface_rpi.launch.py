from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="interface_rpi",
                executable="interface_rpi",
                name="face_screen",
                output="screen",
            ),
        ]
    )
