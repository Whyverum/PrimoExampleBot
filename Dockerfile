# Используем официальный образ Python с подходящей версией
FROM python:3.12-slim

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы Poetry
COPY pyproject.toml poetry.lock* ./

# Настраиваем Poetry (не создавать виртуальное окружение внутри контейнера)
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости через Poetry
RUN poetry install --no-interaction --no-ansi --no-root

# Копируем все файлы проекта внутрь контейнера
COPY . .

# Устанавливаем переменную окружения для буферизации
ENV PYTHONUNBUFFERED=1

# Команда запуска — запуск скрипта main.py
CMD ["python", "main.py"]
