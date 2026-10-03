# Logoped AI

Интеллектуальный логопедический помощник (веб-приложение). Проект представляет собой платформу для взаимодействия и помощи в логопедических задачах.

## Технологии

- **Backend**: Python, Flask
- **База данных**: SQLite (с использованием Flask-SQLAlchemy)
- **Безопасность**: Werkzeug (хеширование паролей)

## Структура проекта

- `app.py` — основной файл приложения (настройка Flask, маршруты, модели БД).
- `requirements.txt` — список зависимостей Python.
- `templates/` — HTML-шаблоны веб-интерфейса.
- `static/` — статические файлы (CSS, JavaScript, изображения).
- `data/` — директория для хранения базы данных `logoped.db`.
- `Dataset/` — наборы данных.
- `Dockerfile` — инструкции для сборки Docker-образа.

## Установка и запуск

### Локальный запуск

1. Склонируйте репозиторий:
   ```bash
   git clone https://git.kpi.fei.tuke.sk/kpi-zp/2026/bp.roman.nazarchuk/workspace/logoped-ai.git
   cd logoped-ai
   ```

2. Создайте виртуальное окружение и активируйте его (рекомендуется):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Для macOS/Linux
   # venv\Scripts\activate   # Для Windows
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Запустите приложение:
   ```bash
   python app.py
   # или flask run
   ```

5. Откройте браузер и перейдите по адресу [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Запуск через Docker

1. Соберите образ:
   ```bash
   docker build -t logoped-ai .
   ```

2. Запустите контейнер:
   ```bash
   docker run -p 5000:5000 logoped-ai
   ```

## Автор
Roman Nazarchuk
