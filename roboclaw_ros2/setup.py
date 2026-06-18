import os

from setuptools import find_packages, setup

package_name = 'roboclaw_ros2'
launch_files = [
    'launch/roboclaw_node.launch.py',
]

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/params.yaml']),
        (os.path.join('share', package_name, 'launch'), launch_files),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='utec',
    maintainer_email='mpuchuri@utec.edu.pe',
    description='ROS 2 control, telemetry and odometry for a RoboClaw mobile base.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'roboclaw_node = roboclaw_ros2.nodes.roboclaw_node:main',
        ],
    },
)
