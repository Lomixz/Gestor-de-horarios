"""Temporary file management for chatbot downloads.

Uses filesystem-based metadata (JSON sidecar files) instead of in-memory registry
so it works across multiple Gunicorn workers.
"""
import os
import uuid
import time
import json
import logging

logger = logging.getLogger('sistema_academico')

EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tmp', 'chatbot_exports')
MAX_AGE_SECONDS = 3600  # 1 hour


def _ensure_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


def save_file(data: bytes, filename: str, user_id: int, mimetype: str = 'application/octet-stream') -> str:
    """Save file data and return a download UUID."""
    _ensure_dir()
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(filename)[1]
    file_path = os.path.join(EXPORT_DIR, f'{file_id}{ext}')
    meta_path = os.path.join(EXPORT_DIR, f'{file_id}.meta.json')

    with open(file_path, 'wb') as f:
        f.write(data)

    meta = {
        'path': file_path,
        'user_id': user_id,
        'created_at': time.time(),
        'filename': filename,
        'mimetype': mimetype,
    }
    with open(meta_path, 'w') as f:
        json.dump(meta, f)

    return file_id


def get_file(file_id: str, user_id: int) -> dict:
    """Get file info if it exists and belongs to the user. Returns None if not found/unauthorized."""
    meta_path = os.path.join(EXPORT_DIR, f'{file_id}.meta.json')

    if not os.path.exists(meta_path):
        return None

    try:
        with open(meta_path, 'r') as f:
            info = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    if info.get('user_id') != user_id:
        return None
    if not os.path.exists(info.get('path', '')):
        return None
    if time.time() - info.get('created_at', 0) > MAX_AGE_SECONDS:
        _cleanup_file(file_id, info)
        return None

    return info


def _cleanup_file(file_id: str, info: dict = None):
    """Remove a single file and its metadata from disk."""
    meta_path = os.path.join(EXPORT_DIR, f'{file_id}.meta.json')

    if info is None and os.path.exists(meta_path):
        try:
            with open(meta_path, 'r') as f:
                info = json.load(f)
        except (json.JSONDecodeError, OSError):
            info = {}

    if info and os.path.exists(info.get('path', '')):
        try:
            os.remove(info['path'])
        except OSError:
            pass

    if os.path.exists(meta_path):
        try:
            os.remove(meta_path)
        except OSError:
            pass


def cleanup_expired():
    """Remove all expired files. Call periodically."""
    _ensure_dir()
    now = time.time()
    cleaned = 0

    for fname in os.listdir(EXPORT_DIR):
        if not fname.endswith('.meta.json'):
            continue

        file_id = fname.replace('.meta.json', '')
        meta_path = os.path.join(EXPORT_DIR, fname)

        try:
            with open(meta_path, 'r') as f:
                info = json.load(f)
            if now - info.get('created_at', 0) > MAX_AGE_SECONDS:
                _cleanup_file(file_id, info)
                cleaned += 1
        except (json.JSONDecodeError, OSError):
            _cleanup_file(file_id)
            cleaned += 1

    if cleaned:
        logger.info(f"Chatbot: limpiados {cleaned} archivos temporales expirados")
