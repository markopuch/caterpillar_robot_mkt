from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="interface_pc",
                executable="interface_pc",
                name="robot_control_gui",
                output="screen",
            ),
        ]
    )
