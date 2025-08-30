from __future__ import annotations

from typing import Optional
from configs import BotSettings

__all__ = ("is_command", "find_argument")


def is_command(message: Optional[str]) -> bool:
    """
    Проверяет, является ли сообщение командой.

    Сообщение считается командой, если:
      1. Оно не пустое;
      2. Начинается с префикса команды, указанного в настройках.

    Args:
        message (Optional[str]): Входное сообщение.

    Returns:
        bool: True, если сообщение является командой, иначе False.

    Пример:
        >>> is_command("/start")
        True
        >>> is_command("hello")
        False
    """
    if not message:
        return False
    return message.strip().startswith(BotSettings.PREFIX)


def find_argument(message: Optional[str]) -> Optional[str]:
    """
    Извлекает аргумент команды из сообщения.

    Аргументом считается текст после первой команды и пробела.
    Если аргумента нет — возвращает None.

    Args:
        message (Optional[str]): Входное сообщение.

    Returns:
        Optional[str]: Аргумент команды или None, если его нет.

    Пример:
        >>> find_argument("/start referrer")
        'referrer'
        >>> find_argument("/start")
        None
        >>> find_argument("hello")
        None
    """
    if not is_command(message):
        return None

    parts = message.strip().split(maxsplit=1)
    return parts[1] if len(parts) > 1 else None
