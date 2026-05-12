

<h1 align="center">☁️ Cloud File Uploader</h1>

<p align="center">
  <strong>Upload files to the cloud and get a shareable download link in seconds</strong>
  <br>
  <sub>Simple web interface · REST API · Session‑based privacy</sub>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-usage">API Usage</a> •
  <a href="#-url-shortener-api">URL Shortener API</a> •
  <a href="#-project-structure">Project Structure</a>
</p>

<hr>

<!-- ENGLISH -->

<h2>✨ Features</h2>

| | |
|---|---|
| 🌐 **Web Interface** | Drag‑and‑drop upload via browser |
| 🖥️ **REST API** | Upload files from terminal with `curl` |
| 🔗 **Shareable Links** | Get a download URL immediately after upload |
| 🛡️ **Private by Design** | Each user sees only their own files (session‑based) |
| 📥 **wget‑Friendly** | Download links work with `wget`, `curl`, or any browser |
| ☁️ **Cloud Storage** | Files are stored securely in S3‑compatible cloud |
| ⏱️ **1‑Hour Links** | Download URLs expire after 1 hour for security |
| 🔐 **URL Shortener** | Create short, customizable links with optional password protection |
| 📊 **Click Statistics** | Track how many times each short link was opened |

---

<h2>🚀 Quick Start</h2>

### 1. Requirements

- Python 3.10+
- A Beget Cloud account (or any S3‑compatible provider)

### 2. Clone & Configure

```bash
git clone <your-repo-url> && cd bay370
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # if you have one, or install manually:
pip install bottle boto3 python-dotenv requests
```

Create a `.env` file:

```env
S3_URL=https://s3.your-provider.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKIT_NAME=your-bucket-name
SITE_URL=http://localhost:8080
```

### 3. Run

```bash
python3 main.pygit commit -m "Merge remote main with local main"
```

Open **http://localhost:8080** in your browser.

---

<h2>🖥️ API Usage</h2>

### Upload a file via `curl`

```bash
curl -F "file=@photo.jpg" http://localhost:8080/api/upload
```

#### Response

```json
{
  "ok": true,
  "name": "photo.jpg",
  "download_url": "http://localhost:8080/dl/abc123/0"
}
```

### Download a file via `wget`

```bash
# The download_url you received after upload
wget http://localhost:8080/dl/abc123/0
```

The file will be saved with its original name.

### Upload with a custom name

```bash
curl -F "file=@photo.jpg" -F "name=myphoto.jpg" http://localhost:8080/api/upload
```

---

<h2>🔗 URL Shortener API</h2>

### Create a short link via `curl`

```bash
curl -X POST http://localhost:8080/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/url"}'
```

#### Response

```json
{
  "ok": true,
  "short_url": "http://localhost:8080/go/Ab3xYz",
  "short_code": "Ab3xYz",
  "original_url": "https://example.com/very/long/url",
  "is_protected": false
}
```

### Custom short code

```bash
curl -X POST http://localhost:8080/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "code": "my-link"}'
```

### Password‑protected (private) link

```bash
curl -X POST http://localhost:8080/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "password": "secret123"}'
```

### Get link statistics

```bash
curl http://localhost:8080/link/Ab3xYz/stats
```

#### Response

```json
{
  "ok": true,
  "original_url": "https://example.com/very/long/url",
  "short_code": "Ab3xYz",
  "clicks": 42,
  "created_at": "2025-01-01T00:00:00+00:00",
  "is_protected": false
}
```

---

<h2>📁 Project Structure</h2>

```
bay370/
├── main.py              # Web server — routes, sessions, pages
├── s3.py                # Cloud storage client (S3‑compatible)
├── file_store.py        # Local JSON store (session → files mapping)
├── shortdb.py           # Short link database (SQLAlchemy + SQLite)
├── upload.html          # Web interface template
├── password_prompt.html # Password entry page for private links
├── style.css            # Styles
├── .env                 # ⚠️ Configuration (do not commit!)
└── .gitignore
```

---

<h2>🔐 How Privacy Works</h2>

1. When you visit the site for the first time, the server issues a **unique session ID** stored in a cookie.
2. All your uploaded files are linked to this session ID.
3. Other users cannot see your files — they have their own session.
4. Files in the cloud storage are stored under **random UUID names**, making them impossible to guess.

---

<h2>🧪 Run Tests</h2>

```bash
python3 -c "import py_compile; py_compile.compile('main.py', doraise=True); py_compile.compile('s3.py', doraise=True); py_compile.compile('file_store.py', doraise=True); print('✅ All good')"
```

---

<h2>📄 License</h2>

MIT

---

<br>

# ☁️ Загрузчик файлов в облако + сокращатель ссылок

<p align="center">
  <strong>Загружайте файлы в облако и сокращайте ссылки — всё в одном сервисе</strong>
  <br>
  <sub>Веб-интерфейс · REST API · Приватность по сессиям</sub>
</p>

<p align="center">
  <a href="#-возможности">Возможности</a> •
  <a href="#-быстрый-старт">Быстрый старт</a> •
  <a href="#-использование-api">Использование API</a> •
  <a href="#-api-сокращения-ссылок">API сокращения ссылок</a> •
  <a href="#-структура-проекта">Структура проекта</a>
</p>

<hr>

<h2>✨ Возможности</h2>

| | |
|---|---|
| 🌐 **Веб-интерфейс** | Загружайте файлы через браузер |
| 🖥️ **REST API** | Загружайте из терминала через `curl` |
| 🔗 **Ссылка для скачивания** | Получайте готовую ссылку сразу после загрузки |
| 🛡️ **Приватность** | Каждый видит только свои файлы (по сессиям) |
| 📥 **wget-дружелюбно** | Ссылки работают с `wget`, `curl` и любым браузером |
| ☁️ **Облачное хранилище** | Файлы хранятся в S3-совместимом облаке |
| ⏱️ **Ссылки на 1 час** | Временные ссылки автоматически истекают |
| 🔐 **Сокращение ссылок** | Создавайте короткие ссылки с кастомным кодом и паролем |
| 📊 **Статистика переходов** | Отслеживайте количество кликов по ссылке |

---

<h2>🚀 Быстрый старт</h2>

### 1. Требования

- Python 3.10+
- Аккаунт в облаке Beget (или любой S3-совместимый провайдер)

### 2. Клонирование и настройка

```bash
git clone <your-repo-url> && cd bay370
python3 -m venv .venv && source .venv/bin/activate
pip install bottle boto3 python-dotenv requests
```

Создайте файл `.env`:

```env
S3_URL=https://s3.your-provider.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKIT_NAME=your-bucket-name
SITE_URL=http://localhost:8080
```

### 3. Запуск

```bash
python3 main.py
```

Откройте **http://localhost:8080** в браузере.

---

<h2>🖥️ Использование API</h2>

### Загрузка через `curl`

```bash
curl -F "file=@photo.jpg" http://localhost:8080/api/upload
```

#### Ответ

```json
{
  "ok": true,
  "name": "photo.jpg",
  "download_url": "http://localhost:8080/dl/abc123/0"
}
```

### Скачивание через `wget`

```bash
# Ссылка, которую вы получили после загрузки
wget http://localhost:8080/dl/abc123/0
```

Файл сохранится с оригинальным именем.

### Загрузка с другим именем

```bash
curl -F "file=@photo.jpg" -F "name=myphoto.jpg" http://localhost:8080/api/upload
```

---

<h2>🔗 API сокращения ссылок</h2>

### Создать короткую ссылку

```bash
curl -X POST http://localhost:8080/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/url"}'
```

#### Ответ

```json
{
  "ok": true,
  "short_url": "http://localhost:8080/go/Ab3xYz",
  "short_code": "Ab3xYz",
  "original_url": "https://example.com/very/long/url",
  "is_protected": false
}
```

### Свой короткий код

```bash
curl -X POST http://localhost:8080/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "code": "my-link"}'
```

### Приватная ссылка (с паролем)

```bash
curl -X POST http://localhost:8080/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "password": "secret123"}'
```

### Статистика по ссылке

```bash
curl http://localhost:8080/link/Ab3xYz/stats
```

#### Ответ

```json
{
  "ok": true,
  "original_url": "https://example.com/very/long/url",
  "short_code": "Ab3xYz",
  "clicks": 42,
  "created_at": "2025-01-01T00:00:00+00:00",
  "is_protected": false
}
```

---

<h2>📁 Структура проекта</h2>

```
bay370/
├── main.py              # Веб-сервер — маршруты, сессии, страницы
├── s3.py                # Клиент облачного хранилища (S3‑совместимый)
├── file_store.py        # Локальное JSON-хранилище (сессия → файлы)
├── shortdb.py           # База данных коротких ссылок (SQLAlchemy + SQLite)
├── upload.html          # Шаблон веб-интерфейса
├── password_prompt.html # Страница ввода пароля для приватных ссылок
├── style.css            # Стили
├── .env                 # ⚠️ Настройки (не коммитить!)
└── .gitignore
```

---

<h2>🔐 Как работает приватность</h2>

1. При первом посещении сайт выдаёт **уникальный ключ сессии**, который сохраняется в куки.
2. Все загруженные вами файлы привязываются к этому ключу.
3. Другие пользователи не видят ваши файлы — у каждого своя сессия.
4. В облачном хранилище файлы хранятся под **случайными UUID-именами**, которые невозможно угадать.

---

<h2>🧪 Проверка</h2>

```bash
python3 -c "import py_compile; py_compile.compile('main.py', doraise=True); py_compile.compile('s3.py', doraise=True); py_compile.compile('file_store.py', doraise=True); print('✅ Всё в порядке')"
```

---

<h2>📄 Лицензия</h2>

MIT
