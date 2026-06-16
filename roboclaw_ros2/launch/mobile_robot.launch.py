from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    params_file = LaunchConfiguration("params_file")
    port = LaunchConfiguration("port")
    start_roboclaw = LaunchConfiguration("start_roboclaw")
    start_face_screen = LaunchConfiguration("start_face_screen")
    start_control_gui = LaunchConfiguration("start_control_gui")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("roboclaw_ros2"), "config", "params.yaml"]
                ),
                description="Path to the robot parameter file.",
            ),
            DeclareLaunchArgument(
                "port",
                default_value="/dev/ttyACM0",
                description="Serial port for the RoboClaw controller.",
            ),
            DeclareLaunchArgument(
                "start_roboclaw",
                default_value="true",
                description="Start the RoboClaw cmd_vel bridge.",
            ),
            DeclareLaunchArgument(
                "start_face_screen",
                default_value="true",
                description="Start the fullscreen face display.",
            ),
            DeclareLaunchArgument(
                "start_control_gui",
                default_value="false",
                description="Start the control GUI on this machine.",
            ),
            Node(
                package="roboclaw_ros2",
                executable="roboclaw_node",
                name="roboclaw_node",
                output="screen",
                parameters=[params_file, {"port": port}],
                condition=IfCondition(start_roboclaw),
            ),
            Node(
                package="interface_rpi",
                executable="interface_rpi",
                name="face_screen",
                output="screen",
                condition=IfCondition(start_face_screen),
            ),
            Node(
                package="interface_pc",
                executable="interface_pc",
                name="robot_control_gui",
                output="screen",
                condition=IfCondition(start_control_gui),
            ),
        ]
    )
