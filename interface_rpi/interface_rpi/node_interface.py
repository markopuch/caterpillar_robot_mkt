#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import signal
import sys
from pathlib import Path

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from PyQt5 import QtCore, QtGui, QtWidgets
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String


FACE_TOPIC = 'face_coms_topic'
DEFAULT_FACE = 'blink'
FRAME_PERIOD_MS = 100
FRAME_RE = re.compile(r'.*_(\d+)\.png$')


class FaceScreen(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.node = Node('face_screen')
        self.node.create_subscription(String, FACE_TOPIC, self.callback_face, 10)

        self.main_path = self.resolve_faces_path()
        self.sequences = self.discover_sequences(self.main_path)
        self.current_face = DEFAULT_FACE
        self.current_frame = 0
        self.current_pixmap = None

        self.init_ui()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(FRAME_PERIOD_MS)

        self.update_image()

    def resolve_faces_path(self):
        try:
            return Path(get_package_share_directory('interface_rpi')) / 'faces'
        except PackageNotFoundError:
            return Path(__file__).resolve().parent / 'faces'

    def discover_sequences(self, root_path):
        sequences = {}
        if not root_path.exists():
            self.node.get_logger().error(f'Face directory not found: {root_path}')
            return sequences

        for face_dir in sorted(root_path.iterdir()):
            if not face_dir.is_dir():
                continue

            face_name = face_dir.name
            frames = sorted(
                face_dir.glob(f'{face_name}_*.png'),
                key=self.frame_sort_key,
            )
            if frames:
                sequences[face_name] = frames

        if DEFAULT_FACE not in sequences:
            self.node.get_logger().warning(
                f'Default face "{DEFAULT_FACE}" is not available in {root_path}'
            )

        self.node.get_logger().info(
            'Loaded face sequences: '
            + ', '.join(sorted(sequences.keys()))
            if sequences
            else 'No face sequences loaded'
        )
        return sequences

    def frame_sort_key(self, path):
        match = FRAME_RE.match(path.name)
        if not match:
            return 0
        return int(match.group(1))

    def init_ui(self):
        self.setWindowTitle('Robot face')
        self.setStyleSheet('background: #000000;')

        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet('background: #000000; color: #ffffff;')
        self.label.setGeometry(self.rect())

        self.showFullScreen()

    def callback_face(self, msg):
        requested_face = msg.data.strip().lower()
        if requested_face not in self.sequences:
            self.node.get_logger().warning(
                f'Unknown face "{requested_face}", using "{DEFAULT_FACE}"'
            )
            requested_face = DEFAULT_FACE

        self.current_face = requested_face
        self.current_frame = 0
        self.update_image()

    def update_image(self):
        if not self.sequences:
            self.label.setText('No face images')
            return

        if self.current_face not in self.sequences:
            self.current_face = DEFAULT_FACE
            self.current_frame = 0

        frames = self.sequences.get(self.current_face) or next(
            iter(self.sequences.values())
        )

        if self.current_frame >= len(frames):
            if self.current_face != DEFAULT_FACE and DEFAULT_FACE in self.sequences:
                self.current_face = DEFAULT_FACE
                self.current_frame = 0
                frames = self.sequences[self.current_face]
            else:
                self.current_frame = 0

        pixmap = QtGui.QPixmap(str(frames[self.current_frame]))
        if pixmap.isNull():
            self.node.get_logger().warning(
                f'Could not load face image: {frames[self.current_frame]}'
            )
        else:
            self.current_pixmap = pixmap
            self.show_pixmap(pixmap)

        self.current_frame += 1

    def show_pixmap(self, pixmap):
        target_size = self.label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        scaled = pixmap.scaled(
            target_size,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation,
        )
        self.label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.label.setGeometry(self.rect())
        if self.current_pixmap is not None:
            self.show_pixmap(self.current_pixmap)


def main(args=None):
    rclpy.init(args=args)
    app = QtWidgets.QApplication(sys.argv)
    screen = FaceScreen()
    screen.show()

    ros_timer = QtCore.QTimer()
    shutdown_requested = False

    def request_shutdown(*_):
        nonlocal shutdown_requested
        if shutdown_requested:
            return

        shutdown_requested = True
        ros_timer.stop()
        app.quit()

    def spin_ros_once():
        if shutdown_requested or not rclpy.ok():
            request_shutdown()
            return

        try:
            rclpy.spin_once(screen.node, timeout_sec=0.01)
        except (KeyboardInterrupt, ExternalShutdownException):
            request_shutdown()
        except RuntimeError:
            if rclpy.ok():
                raise
            request_shutdown()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)
    ros_timer.timeout.connect(spin_ros_once)
    ros_timer.start(10)

    try:
        return app.exec_()
    finally:
        ros_timer.stop()
        screen.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
