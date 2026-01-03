# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence


DEFAULT_BUILTIN_LOGO_PATH = "assets/logo.png"
_ALLOWED_LOGO_SUFFIXES = {".png", ".jpg", ".jpeg"}


def _is_allowed_logo_file(path: Path) -> bool:
    return path.suffix.lower() in _ALLOWED_LOGO_SUFFIXES


def _looks_like_png(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def _looks_like_jpeg(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(3) == b"\xff\xd8\xff"
    except OSError:
        return False


def _has_expected_image_signature(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return _looks_like_png(path)
    if suffix in {".jpg", ".jpeg"}:
        return _looks_like_jpeg(path)
    return False


def _get_app_root() -> Path:
    # src/utils/logo.py -> <repo_root>/src/utils/logo.py
    return Path(__file__).resolve().parents[2]


def _get_builtin_logo_file() -> Path:
    return (_get_app_root() / DEFAULT_BUILTIN_LOGO_PATH).resolve()


def _coerce_to_existing_logo_file(candidate: Optional[str]) -> Optional[Path]:
    if not candidate:
        return None

    candidate_str = str(candidate)

    # Treat "assets/..." as a logical path anchored at the app root (not CWD).
    if candidate_str.startswith("assets/"):
        anchored = _get_app_root() / candidate_str
        if (
            anchored.exists()
            and anchored.is_file()
            and _is_allowed_logo_file(anchored)
            and _has_expected_image_signature(anchored)
        ):
            return anchored.resolve()
        return None

    path = Path(candidate_str).expanduser()

    if path.exists() and path.is_file():
        if not _is_allowed_logo_file(path):
            return None
        if not _has_expected_image_signature(path):
            return None
        return path.resolve()

    return None


def resolve_logo_path(
    *,
    user_logo_path: Optional[str] = None,
    saved_logo_path: Optional[str] = None,
    builtin_logo_path: str = DEFAULT_BUILTIN_LOGO_PATH,
) -> Optional[str]:
    """
    Resuelve una ruta de logo válida, con fallback seguro.

    Prioridad:
    1) user_logo_path (override por export)
    2) saved_logo_path (default persistido)
    3) builtin_logo_path (assets/logo.png)
    """
    for candidate in (user_logo_path, saved_logo_path):
        resolved = _coerce_to_existing_logo_file(candidate)
        if resolved:
            return str(resolved)

    # El builtin se resuelve de forma determinista respecto al app root:
    # - "assets/..." ya está anclado por _coerce_to_existing_logo_file()
    # - cualquier ruta relativa se ancla a app root para no depender del CWD
    builtin_candidate = builtin_logo_path
    if builtin_candidate and not str(builtin_candidate).startswith("assets/"):
        builtin_path = Path(str(builtin_candidate)).expanduser()
        if not builtin_path.is_absolute():
            builtin_candidate = str(_get_app_root() / builtin_path)

    resolved = _coerce_to_existing_logo_file(builtin_candidate)
    if resolved:
        return str(resolved)
    return None


def is_valid_logo_location(location: Optional[str]) -> bool:
    return _coerce_to_existing_logo_file(location) is not None


def coerce_logo_file(location: Optional[str]) -> Optional[str]:
    """
    Convierte una ubicación (archivo) a un path de archivo existente.
    No aplica fallback: si es inválido, retorna None.
    """
    resolved = _coerce_to_existing_logo_file(location)
    return str(resolved) if resolved else None


def normalize_logo_setting_value(location: str) -> str:
    """
    Normaliza el valor a guardar en settings.

    - Mantiene rutas a assets como relativas para que el repo sea portable.
    - Para rutas custom, guarda una ruta absoluta expandida/resuelta.
    """
    if location.startswith("assets/") or location == DEFAULT_BUILTIN_LOGO_PATH:
        return location

    path = Path(location).expanduser()
    try:
        resolved = path.resolve()
        if resolved == _get_builtin_logo_file():
            return DEFAULT_BUILTIN_LOGO_PATH
        return str(resolved)
    except Exception:
        return str(path)
