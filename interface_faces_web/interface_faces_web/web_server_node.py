from __future__ import annotations

import json
import mimetypes
import os
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import rclpy
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from rclpy.node import Node

from interface_faces_web.face_assets import build_faces_report


class FaceWebServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        web_dir: Path,
        faces_dir_param: str,
        rosbridge_port: int,
        rosbridge_host: str,
        face_topic: str,
        reconnect_ms: int,
    ) -> None:
        super().__init__(server_address, FaceRequestHandler)
        self.web_dir = web_dir
        self.faces_dir_param = faces_dir_param
        self.rosbridge_port = rosbridge_port
        self.rosbridge_host = rosbridge_host
        self.face_topic = face_topic
        self.reconnect_ms = reconnect_ms
        self.faces_report = build_faces_report(faces_dir_param)


class FaceRequestHandler(BaseHTTPRequestHandler):
    server: FaceWebServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == '/api/faces':
            self.server.faces_report = build_faces_report(self.server.faces_dir_param)
            self._send_json(self.server.faces_report)
            return

        if path == '/api/config':
            self._send_json(self._runtime_config())
            return

        if path.startswith('/faces/'):
            self._serve_face(path[len('/faces/'):])
            return

        self._serve_web(path)

    def log_message(self, format_string: str, *args: Any) -> None:
        print(f'[interface_faces_web] {self.address_string()} - {format_string % args}')

    def _runtime_config(self) -> dict[str, Any]:
        hostname = self.server.rosbridge_host.strip()
        if not hostname:
            host_header = self.headers.get('Host', 'localhost')
            hostname = host_header.rsplit(':', 1)[0]
        return {
            'rosbridgeUrl': f'ws://{hostname}:{self.server.rosbridge_port}',
            'faceTopic': self.server.face_topic,
            'reconnectMs': self.server.reconnect_ms,
            'messageType': 'std_msgs/msg/String',
        }

    def _serve_web(self, request_path: str) -> None:
        if request_path in ('', '/'):
            request_path = '/index.html'
        relative = request_path.lstrip('/')
        file_path = _safe_join(self.server.web_dir, relative)
        if file_path is None or not file_path.is_file():
            self._send_error(404, f'Archivo web no encontrado: {request_path}')
            return
        self._send_file(file_path)

    def _serve_face(self, relative_path: str) -> None:
        faces_dir = self.server.faces_report.get('faces_dir', '')
        if not faces_dir:
            self._send_error(404, 'No hay directorio de rostros activo.')
            return

        faces_root = Path(faces_dir).resolve()
        file_path = _safe_join(faces_root, relative_path)
        if file_path is None or not file_path.is_file():
            self._send_error(404, f'Rostro no encontrado: {relative_path}')
            return
        self._send_file(file_path)

    def _send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path) -> None:
        mime_type, _encoding = mimetypes.guess_type(str(file_path))
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime_type or 'application/octet-stream')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, code: int, message: str) -> None:
        body = json.dumps({'error': message}).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class WebServerNode(Node):
    def __init__(self) -> None:
        super().__init__('interface_faces_web_server')
        self.declare_parameter('host', '0.0.0.0')
        self.declare_parameter('port', 8080)
        self.declare_parameter('faces_dir', '')
        self.declare_parameter('rosbridge_port', 9090)
        self.declare_parameter('rosbridge_host', '')
        self.declare_parameter('face_topic', '/face/expression')
        self.declare_parameter('reconnect_ms', 2000)

    def make_server(self) -> FaceWebServer:
        host = self.get_parameter('host').value
        port = int(self.get_parameter('port').value)
        faces_dir = str(self.get_parameter('faces_dir').value)
        rosbridge_port = int(self.get_parameter('rosbridge_port').value)
        rosbridge_host = str(self.get_parameter('rosbridge_host').value)
        face_topic = str(self.get_parameter('face_topic').value)
        reconnect_ms = int(self.get_parameter('reconnect_ms').value)
        web_dir = _get_web_dir()

        report = build_faces_report(faces_dir)
        for warning in report.get('warnings', []):
            self.get_logger().warn(warning)
        for error in report.get('errors', []):
            self.get_logger().error(error)

        self.get_logger().info(f'Sirviendo WebApp desde: {web_dir}')
        self.get_logger().info(f'Host web: {host}:{port}')
        self.get_logger().info(f'rosbridge esperado en puerto: {rosbridge_port}')
        if report.get('faces_dir'):
            self.get_logger().info(f'Directorio de rostros activo: {report["faces_dir"]}')

        return FaceWebServer(
            (host, port),
            web_dir,
            faces_dir,
            rosbridge_port,
            rosbridge_host,
            face_topic,
            reconnect_ms,
        )


def _get_web_dir() -> Path:
    try:
        share_dir = Path(get_package_share_directory('interface_faces_web'))
        web_dir = share_dir / 'web'
        if web_dir.is_dir():
            return web_dir.resolve()
    except PackageNotFoundError:
        pass

    source_web_dir = Path(__file__).resolve().parents[1] / 'web'
    if source_web_dir.is_dir():
        return source_web_dir.resolve()
    raise RuntimeError('No se encontro la carpeta web del paquete interface_faces_web.')


def _safe_join(root: Path, relative_path: str) -> Path | None:
    relative = Path(relative_path)
    if relative.is_absolute() or '..' in relative.parts:
        return None
    return root / relative


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = WebServerNode()
    server = node.make_server()

    def stop_server(_signum: int, _frame: Any) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop_server)
    signal.signal(signal.SIGINT, stop_server)

    try:
        node.get_logger().info('Servidor web iniciado.')
        server.serve_forever()
    finally:
        server.server_close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
