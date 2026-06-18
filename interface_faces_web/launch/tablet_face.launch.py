import os

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    web_port = LaunchConfiguration('web_port')
    rosbridge_port = LaunchConfiguration('rosbridge_port')
    host = LaunchConfiguration('host')
    rosbridge_address = LaunchConfiguration('rosbridge_address')
    rosbridge_host = LaunchConfiguration('rosbridge_host')
    run_demo = LaunchConfiguration('run_demo')
    faces_dir = LaunchConfiguration('faces_dir')
    face_topic = LaunchConfiguration('face_topic')
    reconnect_ms = LaunchConfiguration('reconnect_ms')

    def include_rosbridge(_context):
        try:
            rosbridge_launch = os.path.join(
                get_package_share_directory('rosbridge_server'),
                'launch',
                'rosbridge_websocket_launch.xml',
            )
        except PackageNotFoundError:
            return [
                LogInfo(
                    msg='ERROR: No se encontro rosbridge_server. Instale ros-$ROS_DISTRO-rosbridge-server.'
                )
            ]
        return [
            IncludeLaunchDescription(
                AnyLaunchDescriptionSource(rosbridge_launch),
                launch_arguments={
                    'port': rosbridge_port,
                    'address': rosbridge_address,
                }.items(),
            )
        ]

    return LaunchDescription([
        DeclareLaunchArgument('web_port', default_value='8080'),
        DeclareLaunchArgument('rosbridge_port', default_value='9090'),
        DeclareLaunchArgument('host', default_value='0.0.0.0'),
        DeclareLaunchArgument('rosbridge_address', default_value='0.0.0.0'),
        DeclareLaunchArgument('rosbridge_host', default_value=''),
        DeclareLaunchArgument('run_demo', default_value='false'),
        DeclareLaunchArgument('faces_dir', default_value=''),
        DeclareLaunchArgument('face_topic', default_value='/face/expression'),
        DeclareLaunchArgument('reconnect_ms', default_value='2000'),
        OpaqueFunction(function=include_rosbridge),
        Node(
            package='interface_faces_web',
            executable='web_server_node',
            name='interface_faces_web_server',
            output='screen',
            parameters=[{
                'host': host,
                'port': ParameterValue(web_port, value_type=int),
                'faces_dir': faces_dir,
                'rosbridge_port': ParameterValue(rosbridge_port, value_type=int),
                'rosbridge_host': rosbridge_host,
                'face_topic': face_topic,
                'reconnect_ms': ParameterValue(reconnect_ms, value_type=int),
            }],
        ),
        Node(
            package='interface_faces_web',
            executable='face_demo_node',
            name='face_demo_node',
            output='screen',
            condition=IfCondition(run_demo),
            parameters=[{
                'topic': face_topic,
            }],
        ),
    ])
