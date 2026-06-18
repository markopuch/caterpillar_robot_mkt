from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    web_port = LaunchConfiguration("web_port")
    rosbridge_port = LaunchConfiguration("rosbridge_port")
    host = LaunchConfiguration("host")
    rosbridge_address = LaunchConfiguration("rosbridge_address")
    faces_dir = LaunchConfiguration("faces_dir")

    interface_launch = PathJoinSubstitution(
        [FindPackageShare("interface_pc"), "launch", "interface_pc.launch.py"]
    )
    faces_web_launch = PathJoinSubstitution(
        [FindPackageShare("interface_faces_web"), "launch", "tablet_face.launch.py"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("web_port", default_value="8080"),
            DeclareLaunchArgument("rosbridge_port", default_value="9090"),
            DeclareLaunchArgument("host", default_value="0.0.0.0"),
            DeclareLaunchArgument("rosbridge_address", default_value="0.0.0.0"),
            DeclareLaunchArgument("faces_dir", default_value=""),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(interface_launch)),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(faces_web_launch),
                launch_arguments={
                    "web_port": web_port,
                    "rosbridge_port": rosbridge_port,
                    "host": host,
                    "rosbridge_address": rosbridge_address,
                    "faces_dir": faces_dir,
                }.items(),
            ),
        ]
    )
