from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    roboclaw_launch = PathJoinSubstitution(
        [FindPackageShare("roboclaw_ros2"), "launch", "roboclaw_node.launch.py"]
    )
    face_launch = PathJoinSubstitution(
        [FindPackageShare("interface_rpi"), "launch", "interface_rpi.launch.py"]
    )

    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(roboclaw_launch),
                launch_arguments={"port": "/dev/ttyACM0"}.items(),
            ),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(face_launch)),
        ]
    )
