from aiogram.types import Message

# Настройка экспорта в модули
__all__ = ('username', )

# Функция получения юзера или ID пользователя
def username(message: Message) -> str:
    """
    Возвращает юзернейм пользователя из сообщения, или ID, если юзернейм не указан.

    :param message: Объект сообщения из aiogram.
    :return: Строка с юзернеймом пользователя или его ID.
    :raises ValueError: Если в сообщении отсутствует информация о пользователе.
    """
    try:
        if message.from_user:
            return f"@{message.from_user.username}" if message.from_user.username else f"@{message.from_user.id}"
        raise ValueError("Информация о пользователе отсутствует в сообщении.")

    except ValueError as e:
        raise e  # Перебрасываем ошибку выше для дальнейшей обработки
