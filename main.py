# main.py — продакшен-версия
import json
import os
import tempfile
import uuid
import hashlib
import secrets
import string
import json
import shortdb
from shortdb import init_db, get_short_link
import threading
import fileDeleteTimer


from bottle import (
    TEMPLATE_PATH,
    HTTPResponse,
    redirect,
    request,
    response,
    route,
    run,
    static_file,
    template,
)

import file_store
import s3

BUCKET_NAME = os.getenv("S3_BUCKIT_NAME")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8080").rstrip("/")

SESSION_COOKIE = "session_id"
DOWNLOAD_EXPIRES = 3600  # 1 час

# ── Инициализация БД при старте ────────────────────────────────────
init_db()


def _get_or_create_session():
    """Получить существующую или создать новую сессию."""
    session_id = request.get_cookie(SESSION_COOKIE)
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(SESSION_COOKIE, session_id, max_age=86400 * 365)
    return session_id


# ─────────────────────────────────────────────
# Статические страницы
# ─────────────────────────────────────────────


@route("/", method="GET")
def index():
    # Проставляем куку при первом заходе
    _get_or_create_session()
    return template("upload.html", site_url=SITE_URL)


@route("/static/<filename:path>")
def serve_static(filename):
    return static_file(filename, root=os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────
# Сокращение ссылок
# ─────────────────────────────────────────────

def _generate_short_code(length: int = 6) -> str:
    """Сгенерировать случайный короткий код (буквы + цифры)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@route("/create_link", method="POST")
def create_link():
    _get_or_create_session()
    original_url = request.forms.get("original_url", "").strip()
    custom_code = request.forms.get("custom_code", "").strip()
    password = request.forms.get("password")

    if not original_url:
        return "<h2 style='color:red'>❌ URL не указан</h2><a href='/'>Назад</a>"

    # Проверяем / используем кастомный код
    if custom_code:
        short_code = custom_code[:10]
        if shortdb.link_exists(short_code):
            return f"""
<h2 style='color:red'>❌ Короткий код «{short_code}» уже занят</h2>
<p><a href='/'>Попробовать другой</a></p>"""
    else:
        # Генерируем уникальный код
        for _ in range(10):
            short_code = _generate_short_code()
            if not shortdb.link_exists(short_code):
                break
        else:
            return "<h2 style='color:red'>❌ Не удалось сгенерировать код</h2><a href='/'>Назад</a>"

    password_hash = None
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()

    shortdb.create_short_link(
        original_url=original_url,
        short_code=short_code,
        password_hash=password_hash,
    )

    short_url = f"{SITE_URL}/go/{short_code}"

    return f"""
<h2>✅ Ссылка успешно создана!</h2>
<p><strong>Оригинал:</strong> <a href="{original_url}" target="_blank">{original_url}</a></p>
<p><strong>Короткая ссылка:</strong></p>
<input type="text" value="{short_url}" readonly
       style="width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;font-size:16px;background:#f9f9f9;"
       onclick="this.select();this.setSelectionRange(0,99999);navigator.clipboard?.writeText(this.value);">
<br><br>
<a href="/" class="submit-btn" style="display:inline-block;text-decoration:none;padding:10px 20px;">🔗 Сократить ещё</a>
"""


@route("/api/shorten", method="POST")
def api_shorten():
    """API-эндпоинт: сокращение ссылки через curl/json."""
    _get_or_create_session()

    try:
        data = request.json
    except Exception:
        data = None

    if data:
        original_url = data.get("url", "").strip()
        custom_code = data.get("code", "").strip()
        password = data.get("password")
    else:
        original_url = request.forms.get("url", "").strip()
        custom_code = request.forms.get("code", "").strip()
        password = request.forms.get("password")

    if not original_url:
        return {"ok": False, "error": "URL не указан"}

    if custom_code:
        short_code = custom_code[:10]
        if shortdb.link_exists(short_code):
            return {"ok": False, "error": f"Код '{short_code}' уже занят"}
    else:
        for _ in range(10):
            short_code = _generate_short_code()
            if not shortdb.link_exists(short_code):
                break
        else:
            return {"ok": False, "error": "Не удалось сгенерировать код"}

    password_hash = None
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()

    shortdb.create_short_link(
        original_url=original_url,
        short_code=short_code,
        password_hash=password_hash,
    )

    return {
        "ok": True,
        "short_url": f"{SITE_URL}/go/{short_code}",
        "short_code": short_code,
        "original_url": original_url,
        "is_protected": password_hash is not None,
    }


@route("/go/<short_code>", method="GET")
def redirect_short_link(short_code):
    link = shortdb.get_short_link(short_code)
    if not link:
        return "<h2 style='color:red'>❌ Ссылка не найдена</h2><a href='/'>Назад</a>"

    if link.password_hash:
        return template("password_prompt.html", short_code=short_code)

    shortdb.increment_clicks(short_code)
    redirect(link.original_url)


@route("/verify_password/<short_code>", method="POST")
def verify_password(short_code):
    """Проверить пароль для приватной ссылки."""
    try:
        data = request.json
        password = data.get("password", "")
    except Exception:
        password = request.forms.get("password", "")

    if not password:
        return {"success": False, "error": "Пароль обязателен"}

    link = shortdb.get_short_link(short_code)
    if not link:
        return {"success": False, "error": "Ссылка не найдена"}

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    if link.password_hash == password_hash:
        shortdb.increment_clicks(short_code)
        return {
            "success": True,
            "redirect_url": link.original_url,
        }
    else:
        return {"success": False, "error": "Неверный пароль"}


@route("/link/<short_code>/stats", method="GET")
def link_stats(short_code):
    """Статистика по ссылке."""
    stats = shortdb.get_stats(short_code)
    if not stats:
        return {"ok": False, "error": "Ссылка не найдена"}
    stats["ok"] = True
    return stats


@route("/favicon.ico")
def favicon():
    return HTTPResponse(status=204)


# ─────────────────────────────────────────────
# Загрузка через форму (браузер)
# ─────────────────────────────────────────────

#TODO: добавить удаление файлов из S3 через определённое время (через Celery или при загрузке новых файлов)
#TODO: добавить проверку на размер файла и ограничить, чтобы не загружать слишком большие файлы (например, >4000 МБ)
@route("/upload", method="POST")
def upload_ui():
    session_id = _get_or_create_session()
    name_hint = request.forms.get("name", "").strip()
    uploaded_file = request.files.get("myfile")

    if not uploaded_file:
        return "<h2 style='color:red'>❌ Файл не найден</h2><a href='/'>Назад</a>"

    # Сохраняем во временный файл
    with tempfile.NamedTemporaryFile(delete=False, mode="wb") as tmp_file:
        uploaded_file.file.seek(0)
        tmp_file.write(uploaded_file.file.read())
        temp_path = tmp_file.name

    try:
        if not s3.bucket_exists(BUCKET_NAME):
            return """
<h2 style='color:orange'>⚠️ Хранилище не найдено</h2>
<p>Пожалуйста, проверьте настройки.</p>
<a href='/'>Назад</a>
            """

        # Генерируем UUID-имя для S3 (чтобы нельзя было угадать чужой файл)
        ext = ""
        original_name = uploaded_file.filename or "file"
        if "." in original_name:
            ext = original_name.rsplit(".", 1)[1]
        object_name = str(uuid.uuid4())
        if ext:
            object_name += f".{ext}"

        upld = s3.upload_file(BUCKET_NAME, temp_path, object_name)
        if upld == 124:
            return f"<h2 style='color:red'>❌ Файл слишком большой для загрузки</h2><p>Максимальный размер: 4000 МБ</p><a href='/'>Назад</a>"
        # Запоминаем в локальном хранилище
        file_id = file_store.add_file(session_id, original_name, object_name)

        metadata = s3.get_object_metadata(BUCKET_NAME, object_name)

        # Ссылка для скачивания — через наш эндпоинт (wget-friendly)
        download_link = f"{SITE_URL}/dl/{session_id}/{file_id}"

        # Прямая presigned-ссылка (с красивым именем)
        presigned = s3.get_download_url_with_name(
            BUCKET_NAME, object_name, original_name
        )

        size_str = ""
        if metadata:
            size_bytes = metadata["size"]
            if size_bytes < 1024:
                size_str = f"{size_bytes} байт"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} КБ"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} МБ"

        return f"""
<h2>✅ Файл успешно загружен!</h2>
<ul>
    <li><strong>Имя:</strong> {original_name}</li>
    <li><strong>Размер:</strong> {size_str}</li>
</ul>

<p style="margin-top:20px;">
    <a href="{presigned}" target="_blank" class="submit-btn" style="display:inline-block;text-decoration:none;padding:14px 28px;font-size:16px;margin-bottom:15px;">
        📥 Скачать файл
    </a>
</p>

<div style="margin-top:20px;padding:16px;background:#f0f9f0;border-radius:12px;border:1px solid #b8e6b8;">
    <strong>🔗 Ссылка для скачивания:</strong><br>
    <input type="text" value="{download_link}" readonly
           style="width:100%;padding:10px;margin-top:8px;border:1px solid #ccc;border-radius:8px;font-size:14px;background:#fff;"
           onclick="this.select();this.setSelectionRange(0,99999);navigator.clipboard?.writeText(this.value);">
    <p style="margin-top:8px;font-size:13px;color:#555;">
        Эту ссылку можно передать кому угодно. Действительна 1 час.
    </p>
</div>

<p style="margin-top:20px;">
    <a href="/">📤 Загрузить ещё файл</a><br>
    <a href="/files">📋 Мои файлы</a>
</p>
"""
    except Exception as e:
        return f"""
<h2 style='color:red'>❌ Ошибка при загрузке</h2>
<p><strong>Ошибка:</strong> {e}</p>
<a href="/">🔙 Назад</a>
        """
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# ─────────────────────────────────────────────
# API-загрузка (для curl)
# ─────────────────────────────────────────────


@route("/api/upload", method="POST")
def upload_api():
    """Загрузка через curl.

    curl -F "file=@photo.jpg" {SITE_URL}/api/upload
    curl -F "file=@photo.jpg" -F "name=myphoto.jpg" {SITE_URL}/api/upload
    """
    session_id = _get_or_create_session()
    uploaded_file = request.files.get("file")
    name_hint = request.forms.get("name", "").strip()

    if not uploaded_file:
        return {"ok": False, "error": 'Файл не найден. Используйте -F "file=@path"'}

    with tempfile.NamedTemporaryFile(delete=False, mode="wb") as tmp_file:
        uploaded_file.file.seek(0)
        tmp_file.write(uploaded_file.file.read())
        temp_path = tmp_file.name

    try:
        if not s3.bucket_exists(BUCKET_NAME):
            return {"ok": False, "error": "Хранилище не найдено"}

        ext = ""
        original_name = uploaded_file.filename or "file"
        if "." in original_name:
            ext = original_name.rsplit(".", 1)[1]
        object_name = str(uuid.uuid4())
        if ext:
            object_name += f".{ext}"

        s3.upload_file(BUCKET_NAME, temp_path, object_name)

        file_id = file_store.add_file(session_id, original_name, object_name)

        download_link = f"{SITE_URL}/dl/{session_id}/{file_id}"

        return {
            "ok": True,
            "name": original_name,
            "download_url": download_link,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# ─────────────────────────────────────────────
# Эндпоинт для скачивания (wget / браузер)
# ─────────────────────────────────────────────


@route("/dl/<session_id>/<file_id>", method="GET")
def download_file(session_id, file_id):
    """Перенаправляет на presigned-ссылку с оригинальным именем файла."""
    entry = file_store.get_file(session_id, file_id)
    if not entry:
        return "<h2 style='color:red'>❌ Файл не найден</h2><a href='/'>Назад</a>"

    url = s3.get_download_url_with_name(
        BUCKET_NAME, entry["object_name"], entry["original_name"]
    )
    if not url:
        return (
            "<h2 style='color:red'>❌ Ссылка недействительна</h2><a href='/'>Назад</a>"
        )

    # wget-friendly: перенаправляем на presigned URL
    redirect(url)


# ─────────────────────────────────────────────
# Мои файлы (только свои, из сессии)
# ─────────────────────────────────────────────


@route("/files", method="GET")
def list_my_files():
    """Показать только файлы текущей сессии."""
    session_id = _get_or_create_session()
    entries = file_store.get_files(session_id)

    if not entries:
        return """
<h2>📂 Мои файлы</h2>
<p>У вас пока нет загруженных файлов.</p>
<a href="/">Загрузить файл</a>
        """

    html = """
<h2>📂 Мои файлы</h2>
<table style="width:100%;border-collapse:collapse;margin:20px 0;">
    <tr style="background:#f0f0f0;">
        <th style="padding:12px;text-align:left;border-bottom:2px solid #ddd;">Имя файла</th>
        <th style="padding:12px;text-align:center;border-bottom:2px solid #ddd;">Скачать</th>
    </tr>
"""
    for entry in entries:
        dl_link = f"{SITE_URL}/dl/{session_id}/{entry['id']}"
        html += f"""
    <tr>
        <td style="padding:12px;border-bottom:1px solid #eee;">{entry["original_name"]}</td>
        <td style="padding:12px;text-align:center;border-bottom:1px solid #eee;">
            <a href="{dl_link}" target="_blank">📥</a>
        </td>
    </tr>
"""
    html += """
</table>
<a href="/">🔙 Назад</a>
    """
    return html


# ─────────────────────────────────────────────
# Пуск
# ─────────────────────────────────────────────

with open("config.json", "r") as f:
    config = json.load(f)

def gen_basic_config():
    return {
        "file_7days_deleting_on": config.get("file_7days_deleting_on", False)
    }

if config.get("file_7days_deleting_on", False):
    pass
else:
    threading.Thread(target=fileDeleteTimer.delete_old_files, args=(bucket_name, 7)).start()  # Запускаем удаление старых файлов в отдельном потоке

public_config = gen_basic_config()
def push_basic_config():
    global public_config
    public_config = gen_basic_config()
    try:
        with open("config.json", "w") as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Ошибка при сохранении конфигурации: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Загрузчик файлов в облако")
    print("=" * 50)

    threading.Thread(target=fileDeleteTimer.delete_old_files, args=(s3.bucket_name, 7)).start()  # Запускаем удаление старых файлов в отдельном потоке
    
    if not BUCKET_NAME:
        print("❌ Ошибка: имя хранилища не задано в .env файле")
    else:
        print(f"✓ Хранилище: {BUCKET_NAME}")
        print(f"✓ Адрес сайта: {SITE_URL}")

        try:
            if s3.bucket_exists(BUCKET_NAME):
                print("✓ Подключение успешно!")
            else:
                print(f"⚠️ Хранилище '{BUCKET_NAME}' не найдено")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")

    print("=" * 50)
    print(f"Сервер запущен на {SITE_URL}")
    print("=" * 50)
    print()
    print("Примеры использования:")
    print(f'  curl -F "file=@photo.jpg" {SITE_URL}/api/upload')
    print()

    TEMPLATE_PATH.insert(0, os.path.dirname(os.path.abspath(__file__)))

    run(host="0.0.0.0", port=8080, debug=False)
