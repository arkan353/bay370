"""Локальное хранилище привязки файлов к сессиям."""

import json
import os
import threading

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "file_store.json")
_lock = threading.Lock()


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_file(session_id, original_name, object_name):
    """Сохраняет запись о файле: сессия -> список файлов."""
    with _lock:
        data = _load()
        if session_id not in data:
            data[session_id] = []
        # Генерируем короткий внутренний ID
        file_id = str(len(data[session_id]))
        entry = {
            "id": file_id,
            "original_name": original_name,
            "object_name": object_name,
        }
        data[session_id].append(entry)
        _save(data)
        return file_id


def get_files(session_id):
    """Возвращает список файлов сессии."""
    with _lock:
        data = _load()
        return data.get(session_id, [])


def get_file(session_id, file_id):
    """Возвращает конкретный файл по ID в рамках сессии."""
    with _lock:
        data = _load()
        for f in data.get(session_id, []):
            if f["id"] == file_id:
                return f
        return None
