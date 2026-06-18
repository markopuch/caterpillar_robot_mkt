from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory


SUPPORTED_EXPRESSIONS = [
    'idle',
    'happy',
    'sad',
    'talking',
    'listening',
    'thinking',
    'surprised',
    'angry',
    'sleeping',
    'error',
    'blink',
    'smile',
    'heart',
    'fire',
    'music',
]

SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.json']

# Candidate names are resolved inside the active faces directory. A directory
# candidate means "use all supported files in that directory as animation frames".
FACE_CANDIDATES = {
    'idle': ['idle', 'blink', 'blink/blink_1'],
    'happy': ['happy', 'smile', 'smile/smile_1', 'heart', 'heart/heart_1'],
    'sad': ['sad'],
    'talking': ['talking', 'music', 'music/music_1'],
    'listening': ['listening'],
    'thinking': ['thinking'],
    'surprised': ['surprised'],
    'angry': ['angry', 'fire', 'fire/fire_1'],
    'sleeping': ['sleeping'],
    'error': ['error', 'fire', 'fire/fire_1'],
    'blink': ['blink', 'blink/blink_1'],
    'smile': ['smile', 'smile/smile_1'],
    'heart': ['heart', 'heart/heart_1'],
    'fire': ['fire', 'fire/fire_1'],
    'music': ['music', 'music/music_1'],
}


def build_faces_report(faces_dir_param: str = '') -> dict[str, Any]:
    faces_dir, source, interface_rpi_found, warnings, errors = _resolve_faces_dir(faces_dir_param)
    report: dict[str, Any] = {
        'supported_expressions': SUPPORTED_EXPRESSIONS,
        'supported_extensions': SUPPORTED_EXTENSIONS,
        'faces_dir_source': source,
        'faces_dir': str(faces_dir) if faces_dir else '',
        'using_faces_dir': bool(faces_dir_param),
        'interface_rpi_found': interface_rpi_found,
        'faces': {},
        'warnings': warnings,
        'errors': errors,
    }

    if not faces_dir:
        _fill_missing_faces(report)
        return report

    idle_asset = _find_expression_asset(faces_dir, 'idle')
    if not idle_asset:
        idle_asset = _find_first_asset(faces_dir)
        if idle_asset:
            report['warnings'].append(
                'No se encontro un rostro idle explicito; se usa el primer recurso disponible.'
            )
        else:
            report['errors'].append(f'No se encontraron recursos visuales en {faces_dir}')

    resolved: dict[str, dict[str, Any]] = {}
    for expression in SUPPORTED_EXPRESSIONS:
        asset = _find_expression_asset(faces_dir, expression)
        if asset:
            resolved[expression] = _asset_to_report(asset, faces_dir, found=True)
            continue

        if idle_asset:
            fallback = _asset_to_report(idle_asset, faces_dir, found=False)
            fallback['fallback'] = 'idle'
            fallback['warning'] = f"No se encontro '{expression}', usando idle."
            resolved[expression] = fallback
        else:
            resolved[expression] = {
                'found': False,
                'fallback': 'idle',
                'url': '',
                'path': '',
                'extension': '',
                'frames': [],
                'warning': f"No se encontro '{expression}' y tampoco hay idle disponible.",
            }

    report['faces'] = resolved
    return report


def _resolve_faces_dir(faces_dir_param: str) -> tuple[Path | None, str, bool, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    faces_dir_param = faces_dir_param.strip()

    if faces_dir_param:
        path = Path(faces_dir_param).expanduser().resolve()
        if path.is_dir():
            return path, 'faces_dir', False, warnings, errors
        errors.append(f'faces_dir no existe o no es un directorio: {path}')
        return None, 'faces_dir', False, warnings, errors

    try:
        share_dir = Path(get_package_share_directory('interface_rpi')).resolve()
    except PackageNotFoundError:
        errors.append('No se encontro el paquete interface_rpi en el entorno ROS actual.')
        return None, 'missing', False, warnings, errors

    candidates = [
        share_dir / 'faces',
        share_dir / 'interface_rpi' / 'faces',
        share_dir / 'interface_rpi' / 'interface_rpi' / 'faces',
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve(), 'interface_rpi', True, warnings, errors

    errors.append(
        'Se encontro interface_rpi, pero no se encontro su carpeta faces en el share directory.'
    )
    warnings.append('Use el parametro faces_dir para indicar manualmente la carpeta de rostros.')
    return None, 'interface_rpi', True, warnings, errors


def _find_expression_asset(faces_dir: Path, expression: str) -> dict[str, Any] | None:
    for candidate in FACE_CANDIDATES.get(expression, [expression]):
        asset = _find_candidate(faces_dir, candidate)
        if asset:
            return asset
    return None


def _find_candidate(faces_dir: Path, candidate: str) -> dict[str, Any] | None:
    candidate_path = faces_dir / candidate
    if candidate_path.is_dir():
        frames = _collect_frames(candidate_path)
        if frames:
            return {'path': frames[0], 'frames': frames, 'source': candidate}
        return None

    if candidate_path.suffix.lower() in SUPPORTED_EXTENSIONS and candidate_path.is_file():
        return {'path': candidate_path, 'frames': [candidate_path], 'source': candidate}

    for extension in SUPPORTED_EXTENSIONS:
        file_path = candidate_path.with_suffix(extension)
        if file_path.is_file():
            return {'path': file_path, 'frames': [file_path], 'source': candidate}
    return None


def _collect_frames(directory: Path) -> list[Path]:
    frames = [
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(frames, key=_natural_key)


def _find_first_asset(faces_dir: Path) -> dict[str, Any] | None:
    files = [
        path
        for path in faces_dir.rglob('*')
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    files = sorted(files, key=_natural_key)
    if not files:
        return None
    return {'path': files[0], 'frames': [files[0]], 'source': 'first_available'}


def _asset_to_report(asset: dict[str, Any], faces_dir: Path, found: bool) -> dict[str, Any]:
    frames: list[Path] = asset['frames']
    first_path: Path = asset['path']
    return {
        'found': found,
        'url': _face_url(first_path, faces_dir),
        'path': str(first_path),
        'relative_path': first_path.relative_to(faces_dir).as_posix(),
        'extension': first_path.suffix.lower(),
        'frames': [_face_url(frame, faces_dir) for frame in frames],
        'frame_count': len(frames),
        'candidate': asset.get('source', ''),
    }


def _face_url(path: Path, faces_dir: Path) -> str:
    relative = path.relative_to(faces_dir).as_posix()
    return '/faces/' + quote(relative)


def _fill_missing_faces(report: dict[str, Any]) -> None:
    report['faces'] = {
        expression: {
            'found': False,
            'fallback': 'idle',
            'url': '',
            'path': '',
            'extension': '',
            'frames': [],
            'frame_count': 0,
        }
        for expression in SUPPORTED_EXPRESSIONS
    }


def _natural_key(path: Path) -> list[int | str]:
    parts = re.split(r'(\d+)', path.as_posix())
    return [int(part) if part.isdigit() else part.lower() for part in parts]
