from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    robot_launch = PathJoinSubstitution(
        [FindPackageShare("caterpillar_bringup"), "launch", "robot.launch.py"]
    )
    interface_launch = PathJoinSubstitution(
        [FindPackageShare("caterpillar_bringup"), "launch", "interface.launch.py"]
    )

    return LaunchDescription(
        [
            IncludeLaunchDescription(PythonLaunchDescriptionSource(robot_launch)),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(interface_launch)),
        ]
    )
