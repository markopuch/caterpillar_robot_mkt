import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'interface_faces_web'


def package_files(target_dir, source_dir):
    data = []
    for root, _dirs, files in os.walk(source_dir):
        if not files:
            continue
        install_dir = os.path.join('share', package_name, target_dir, os.path.relpath(root, source_dir))
        data.append((install_dir, [os.path.join(root, filename) for filename in files]))
    return data


setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'README.md']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ] + package_files('web', 'web'),
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Marko Puchuri',
    maintainer_email='mpuchuri@utec.edu.pe',
    description='Web face interface for a tablet controlled from ROS 2 through rosbridge.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'web_server_node = interface_faces_web.web_server_node:main',
            'face_demo_node = interface_faces_web.face_demo_node:main',
            'set_face_node = interface_faces_web.set_face_node:main',
        ],
    },
)
