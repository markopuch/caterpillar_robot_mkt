#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import signal
import sys
import time

from geometry_msgs.msg import Twist
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

from PyQt5.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


CMD_VEL_TOPIC = 'cmd_vel'
FACE_TOPIC = 'face_coms_topic'

MAX_LINEAR_SPEED_MPS = 0.50
MAX_ANGULAR_SPEED_RADPS = 1.40
AXIS_DEADZONE = 0.08
PUBLISH_PERIOD_MS = 100
MAX_SPEED_PERCENT = 100

FACE_EXPRESSIONS = ('blink', 'smile', 'heart', 'fire', 'music')


class RobotGuiNode(Node):
    def __init__(self):
        super().__init__('robot_control_gui')

        self.cmd_vel_publisher = self.create_publisher(Twist, CMD_VEL_TOPIC, 10)
        self.face_publisher = self.create_publisher(String, FACE_TOPIC, 10)

        self.last_twist_payload = None
        self.last_twist_sent = 0.0
        self.last_face_sent = 0.0
        self.motion_text = f'{CMD_VEL_TOPIC}: waiting'
        self.face_text = f'{FACE_TOPIC}: waiting'

    def send_twist(self, linear_x, angular_z, force=False):
        linear_x = float(clamp(linear_x, -MAX_LINEAR_SPEED_MPS, MAX_LINEAR_SPEED_MPS))
        angular_z = float(
            clamp(angular_z, -MAX_ANGULAR_SPEED_RADPS, MAX_ANGULAR_SPEED_RADPS)
        )
        payload = (round(linear_x, 3), round(angular_z, 3))
        now = time.monotonic()

        if (
            not force
            and payload == self.last_twist_payload
            and now - self.last_twist_sent < 0.08
        ):
            return

        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.cmd_vel_publisher.publish(msg)

        self.last_twist_payload = payload
        self.last_twist_sent = now
        self.motion_text = (
            f'{CMD_VEL_TOPIC}: linear.x={linear_x:+.2f} m/s, '
            f'angular.z={angular_z:+.2f} rad/s'
        )

    def stop_robot(self):
        self.send_twist(0.0, 0.0, force=True)

    def send_face(self, expression):
        if expression not in FACE_EXPRESSIONS:
            expression = 'blink'

        msg = String()
        msg.data = expression
        self.face_publisher.publish(msg)

        self.last_face_sent = time.monotonic()
        self.face_text = f'{FACE_TOPIC}: {expression}'


class AnalogPad(QWidget):
    valueChanged = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        self._linear_axis = 0.0
        self._angular_axis = 0.0
        self.setMinimumSize(260, 260)
        self.setMouseTracking(True)

    def reset(self, emit_signal=True):
        self._linear_axis = 0.0
        self._angular_axis = 0.0
        if emit_signal:
            self.valueChanged.emit(0.0, 0.0)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._update_from_position(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._update_from_position(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.reset()

    def paintEvent(self, _event):
        size = min(self.width(), self.height()) - 24
        radius = size / 2.0
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        rect = QRectF(center.x() - radius, center.y() - radius, size, size)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor('#f7f8fa'))

        painter.setPen(QPen(QColor('#c8ced8'), 2))
        painter.setBrush(QColor('#ffffff'))
        painter.drawEllipse(rect)

        painter.setPen(QPen(QColor('#dde2ea'), 1))
        painter.drawEllipse(
            QRectF(
                center.x() - radius * 0.55,
                center.y() - radius * 0.55,
                radius * 1.1,
                radius * 1.1,
            )
        )
        painter.drawLine(
            QPointF(center.x() - radius, center.y()),
            QPointF(center.x() + radius, center.y()),
        )
        painter.drawLine(
            QPointF(center.x(), center.y() - radius),
            QPointF(center.x(), center.y() + radius),
        )

        painter.setPen(QPen(QColor('#4c566a'), 1))
        painter.setFont(QFont('Sans Serif', 9))
        painter.drawText(
            QRectF(center.x() - 42, center.y() - radius - 6, 84, 18),
            Qt.AlignCenter,
            'ADELANTE',
        )
        painter.drawText(
            QRectF(center.x() - 42, center.y() + radius - 12, 84, 18),
            Qt.AlignCenter,
            'ATRAS',
        )
        painter.drawText(
            QRectF(center.x() - radius - 4, center.y() - 9, 62, 18),
            Qt.AlignCenter,
            'IZQ',
        )
        painter.drawText(
            QRectF(center.x() + radius - 58, center.y() - 9, 62, 18),
            Qt.AlignCenter,
            'DER',
        )

        knob_x = center.x() - self._angular_axis * radius
        knob_y = center.y() - self._linear_axis * radius
        knob_radius = max(18.0, radius * 0.16)
        painter.setPen(QPen(QColor('#1d4ed8'), 2))
        painter.setBrush(QColor('#3b82f6'))
        painter.drawEllipse(QPointF(knob_x, knob_y), knob_radius, knob_radius)

    def _update_from_position(self, position):
        size = min(self.width(), self.height()) - 24
        radius = max(size / 2.0, 1.0)
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        dx = position.x() - center_x
        dy = position.y() - center_y
        distance = math.hypot(dx, dy)
        if distance > radius:
            scale = radius / distance
            dx *= scale
            dy *= scale

        self._linear_axis = clamp(-dy / radius, -1.0, 1.0)
        self._angular_axis = clamp(-dx / radius, -1.0, 1.0)
        self.valueChanged.emit(self._linear_axis, self._angular_axis)
        self.update()


class RobotGui(QMainWindow):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.pad_linear_axis = 0.0
        self.pad_angular_axis = 0.0
        self.button_linear_axis = 0.0
        self.button_angular_axis = 0.0

        self.setWindowTitle('Robot diferencial')
        self.setMinimumSize(800, 560)
        self.setStyleSheet("""
            QMainWindow { background: #eef1f5; }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #d7dce5;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QPushButton {
                background: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                padding: 9px 12px;
                font-weight: 600;
            }
            QPushButton:pressed {
                background: #dbeafe;
                border-color: #3b82f6;
            }
            QLabel { color: #1f2937; }
        """)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(0)
        self.speed_slider.setMaximum(MAX_SPEED_PERCENT)
        self.speed_slider.setValue(35)
        self.speed_slider.valueChanged.connect(self.update_speed_limit)

        self.speed_label = QLabel()
        self.limit_label = QLabel()
        self.update_speed_limit(self.speed_slider.value())

        root_layout = QVBoxLayout()
        root_layout.addWidget(self.build_base_controls(), 1)
        root_layout.addWidget(self.build_face_controls())
        root_layout.addWidget(self.build_status_panel())

        root = QWidget()
        root.setLayout(root_layout)
        self.setCentralWidget(root)

        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.publish_active_motion)
        self.command_timer.start(PUBLISH_PERIOD_MS)

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start(200)

    def build_base_controls(self):
        base_box = QGroupBox('Base diferencial')
        base_layout = QVBoxLayout()

        motion_layout = QHBoxLayout()
        motion_layout.addWidget(self.build_button_controls(), 0)
        motion_layout.addWidget(self.build_analog_controls(), 1)
        base_layout.addLayout(motion_layout)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.speed_label)
        slider_layout.addWidget(self.speed_slider, 1)
        slider_layout.addWidget(self.limit_label)
        base_layout.addLayout(slider_layout)

        base_box.setLayout(base_layout)
        return base_box

    def build_button_controls(self):
        button_box = QGroupBox('Botones')
        button_box.setFixedWidth(250)
        layout = QGridLayout()

        forward = QPushButton('Adelante')
        backward = QPushButton('Atras')
        left = QPushButton('Girar izq')
        right = QPushButton('Girar der')
        stop = QPushButton('STOP')

        for button in (forward, backward, left, right, stop):
            button.setMinimumHeight(56)

        forward.pressed.connect(lambda: self.set_button_axes(1.0, 0.0))
        forward.released.connect(lambda: self.set_button_axes(0.0, 0.0))
        backward.pressed.connect(lambda: self.set_button_axes(-1.0, 0.0))
        backward.released.connect(lambda: self.set_button_axes(0.0, 0.0))
        left.pressed.connect(lambda: self.set_button_axes(0.0, 1.0))
        left.released.connect(lambda: self.set_button_axes(0.0, 0.0))
        right.pressed.connect(lambda: self.set_button_axes(0.0, -1.0))
        right.released.connect(lambda: self.set_button_axes(0.0, 0.0))
        stop.clicked.connect(self.stop_motion)

        layout.addWidget(forward, 0, 1)
        layout.addWidget(left, 1, 0)
        layout.addWidget(stop, 1, 1)
        layout.addWidget(right, 1, 2)
        layout.addWidget(backward, 2, 1)
        button_box.setLayout(layout)
        return button_box

    def build_analog_controls(self):
        analog_box = QGroupBox('Joystick')
        layout = QHBoxLayout()

        self.analog_pad = AnalogPad()
        self.analog_pad.valueChanged.connect(self.set_pad_axes)

        readout_layout = QVBoxLayout()
        self.axes_label = QLabel('Entrada: lineal=+0.00, angular=+0.00')
        self.command_label = QLabel(self.node.motion_text)
        self.face_label = QLabel(self.node.face_text)
        self.max_speed_label = QLabel()
        self.max_speed_label.setText(self.limit_label.text())

        for label in (
            self.axes_label,
            self.command_label,
            self.face_label,
            self.max_speed_label,
        ):
            label.setWordWrap(True)
            label.setMinimumHeight(28)

        readout_layout.addWidget(self.axes_label)
        readout_layout.addWidget(self.command_label)
        readout_layout.addWidget(self.face_label)
        readout_layout.addWidget(self.max_speed_label)
        readout_layout.addStretch(1)

        layout.addWidget(self.analog_pad, 0)
        layout.addLayout(readout_layout, 1)
        analog_box.setLayout(layout)
        return analog_box

    def build_face_controls(self):
        face_box = QGroupBox('Rostro')
        face_layout = QGridLayout()

        labels = {
            'blink': 'Normal',
            'smile': 'Sonrisa',
            'heart': 'Corazon',
            'fire': 'Fuego',
            'music': 'Musica',
        }

        for index, expression in enumerate(FACE_EXPRESSIONS):
            button = QPushButton(labels[expression])
            button.setMinimumHeight(46)
            button.clicked.connect(
                lambda _=False, face=expression: self.node.send_face(face)
            )
            face_layout.addWidget(button, 0, index)

        face_box.setLayout(face_layout)
        return face_box

    def build_status_panel(self):
        status_box = QGroupBox('Estado')
        status_layout = QGridLayout()

        self.motion_badge = self.make_badge()
        self.face_badge = self.make_badge()

        status_layout.addWidget(QLabel('Base'), 0, 0)
        status_layout.addWidget(self.motion_badge, 0, 1)
        status_layout.addWidget(QLabel('Rostro'), 0, 2)
        status_layout.addWidget(self.face_badge, 0, 3)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        status_layout.addWidget(separator, 1, 0, 1, 4)

        self.motion_status_label = QLabel(self.node.motion_text)
        self.face_status_label = QLabel(self.node.face_text)
        self.motion_status_label.setWordWrap(True)
        self.face_status_label.setWordWrap(True)

        status_layout.addWidget(self.motion_status_label, 2, 0, 1, 4)
        status_layout.addWidget(self.face_status_label, 3, 0, 1, 4)

        status_box.setLayout(status_layout)
        return status_box

    def make_badge(self):
        label = QLabel('WAIT')
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(28)
        label.setMinimumWidth(120)
        return label

    def update_speed_limit(self, value):
        scale = value / 100.0
        self.speed_label.setText(f'Limite: {value}%')
        self.limit_label.setText(
            f'max {MAX_LINEAR_SPEED_MPS * scale:.2f} m/s, '
            f'{MAX_ANGULAR_SPEED_RADPS * scale:.2f} rad/s'
        )
        if hasattr(self, 'max_speed_label'):
            self.max_speed_label.setText(self.limit_label.text())
        self.send_current_motion(force=True)

    def set_pad_axes(self, linear_axis, angular_axis):
        self.pad_linear_axis = float(linear_axis)
        self.pad_angular_axis = float(angular_axis)
        self.send_current_motion(force=True)

    def set_button_axes(self, linear_axis, angular_axis):
        self.button_linear_axis = float(linear_axis)
        self.button_angular_axis = float(angular_axis)
        self.send_current_motion(force=True)

    def publish_active_motion(self):
        if self.motion_is_active():
            self.send_current_motion()

    def send_current_motion(self, force=False):
        linear_axis, angular_axis = self.effective_axes()
        self.axes_label.setText(
            f'Entrada: lineal={linear_axis:+.2f}, angular={angular_axis:+.2f}'
        )

        if not self.motion_is_active():
            if force:
                self.node.stop_robot()
            return

        scale = self.speed_slider.value() / 100.0
        linear_x = linear_axis * MAX_LINEAR_SPEED_MPS * scale
        angular_z = angular_axis * MAX_ANGULAR_SPEED_RADPS * scale
        self.node.send_twist(linear_x, angular_z, force=force)

    def stop_motion(self):
        self.pad_linear_axis = 0.0
        self.pad_angular_axis = 0.0
        self.button_linear_axis = 0.0
        self.button_angular_axis = 0.0
        self.analog_pad.reset(emit_signal=False)
        self.axes_label.setText('Entrada: lineal=+0.00, angular=+0.00')
        self.node.stop_robot()

    def motion_is_active(self):
        linear_axis, angular_axis = self.effective_axes()
        return max(abs(linear_axis), abs(angular_axis)) > AXIS_DEADZONE

    def effective_axes(self):
        linear_axis = clamp(
            self.pad_linear_axis + self.button_linear_axis,
            -1.0,
            1.0,
        )
        angular_axis = clamp(
            self.pad_angular_axis + self.button_angular_axis,
            -1.0,
            1.0,
        )
        if abs(linear_axis) <= AXIS_DEADZONE:
            linear_axis = 0.0
        if abs(angular_axis) <= AXIS_DEADZONE:
            angular_axis = 0.0
        return linear_axis, angular_axis

    def refresh_status(self):
        now = time.monotonic()

        self.command_label.setText(self.node.motion_text)
        self.face_label.setText(self.node.face_text)
        self.motion_status_label.setText(self.node.motion_text)
        self.face_status_label.setText(self.node.face_text)

        motion_fresh = now - self.node.last_twist_sent <= 1.0
        if self.motion_is_active():
            self.set_badge(
                self.motion_badge,
                'ok' if motion_fresh else 'error',
                'TX' if motion_fresh else 'TIMEOUT',
            )
        elif self.node.last_twist_sent:
            self.set_badge(self.motion_badge, 'ok', 'STOP')
        else:
            self.set_badge(self.motion_badge, 'wait', 'WAIT')

        self.set_badge(
            self.face_badge,
            'ok' if self.node.last_face_sent else 'wait',
            'SENT' if self.node.last_face_sent else 'WAIT',
        )

    @staticmethod
    def set_badge(label, state, text):
        styles = {
            'ok': ('#15803d', '#dcfce7'),
            'error': ('#b91c1c', '#fee2e2'),
            'wait': ('#475569', '#e2e8f0'),
        }
        color, background = styles[state]
        label.setText(text)
        label.setStyleSheet(
            f'background: {background}; color: {color}; '
            f'border: 1px solid {color}; border-radius: 7px; '
            'font-weight: 700; padding: 4px 8px;'
        )


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    node = RobotGuiNode()
    window = RobotGui(node)
    window.show()

    ros_timer = QTimer()
    shutdown_requested = False

    def request_shutdown(*_):
        nonlocal shutdown_requested
        if shutdown_requested:
            return

        shutdown_requested = True
        if rclpy.ok():
            node.stop_robot()
        ros_timer.stop()
        app.quit()

    def spin_ros_once():
        if shutdown_requested or not rclpy.ok():
            request_shutdown()
            return

        try:
            rclpy.spin_once(node, timeout_sec=0.01)
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
        node.stop_robot()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
