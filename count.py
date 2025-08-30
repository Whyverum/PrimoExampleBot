from pathlib import Path
from typing import Dict


def count_python_lines(project_path: str = ".", exclude: str = ".venv") -> Dict[str, int]:
    """
    Подсчитывает количество строк кода во всех Python (.py) файлах проекта.

    Args:
        project_path (str): Путь к директории проекта. По умолчанию — текущая папка.
        exclude (str): Имя директории, которую нужно исключить (например, .venv).

    Returns:
        Dict[str, int]: Словарь с двумя ключами:
            - "files": количество найденных файлов .py
            - "lines": общее количество строк во всех .py файлах
    """
    root: Path = Path(project_path)
    total_lines: int = 0
    file_count: int = 0

    # Рекурсивный обход всех файлов
    for file_path in root.rglob("*.py"):
        # Игнорируем .venv и любые подпапки внутри него
        if exclude in file_path.parts:
            continue

        try:
            with file_path.open("r", encoding="utf-8") as f:
                # Считаем количество строк в файле
                line_count = sum(1 for _ in f)
                total_lines += line_count
                file_count += 1
        except (UnicodeDecodeError, PermissionError):
            # Иногда могут встретиться битые файлы или без прав доступа
            continue

    return {"files": file_count, "lines": total_lines}


if __name__ == "__main__":
    stats = count_python_lines()
    print(f"📊 Найдено файлов: {stats['files']}")
    print(f"📄 Всего строк кода: {stats['lines']}")
