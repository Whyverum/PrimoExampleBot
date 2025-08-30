from typing import Final

from aiogram.types import Message

# Настройка экспорта
__all__ = ("CHAT_TYPES", "CONTENT_TYPE_RU", "type_chat", "type_msg")


# Словарь сопоставлений "chat_type -> русское название"
CHAT_TYPES: Final[dict[str, str]] = {
        "private": "Личный",
        "group": "Группа",
        "supergroup": "Группа",
        "channel": "Канал",
    }

# Словарь сопоставлений "content_type -> русское название"
CONTENT_TYPE_RU: Final[dict[str, str]] = {
    "text": "Текст",
    "animation": "Гиф",
    "audio": "Аудио",
    "document": "Файл",
    "photo": "Фото",
    "sticker": "Стикер",
    "video": "Видео",
    "video_note": "Видеосообщение",
    "voice": "Голосовое сообщение",
    "contact": "Контакт",
    "dice": "Кубик",
    "game": "Игра",
    "poll": "Опрос",
    "venue": "Место",
    "location": "Локация",
    "new_chat_members": "Новые участники чата",
    "left_chat_member": "Участник вышел",
    "new_chat_title": "Новое название чата",
    "new_chat_photo": "Новая картинка чата",
    "delete_chat_photo": "Удалена картинка чата",
    "group_chat_created": "Создана группа",
    "supergroup_chat_created": "Создана супергруппа",
    "channel_chat_created": "Создан канал",
    "message_auto_delete_timer_changed": "Изменён автоудалитель",
    "migrate_to_chat_id": "Группа → супергруппа",
    "migrate_from_chat_id": "Супергруппа → группа",
    "pinned_message": "Закреплённое сообщение",
    "invoice": "Счёт",
    "successful_payment": "Успешный платёж",
    "connected_website": "Подключённый сайт",
    "passport_data": "Данные Telegram Passport",
    "proximity_alert_triggered": "Алерт о приближении",
    "video_chat_scheduled": "Запланированный видеочат",
    "video_chat_started": "Видеочат начался",
    "video_chat_ended": "Видеочат завершён",
    "video_chat_participants_invited": "Приглашены участники видеочата",
    "web_app_data": "Данные из веб-приложения",
    "forum_topic_created": "Создана тема форума",
    "forum_topic_edited": "Изменена тема форума",
    "forum_topic_closed": "Тема форума закрыта",
    "forum_topic_reopened": "Тема форума открыта",
    "general_forum_topic_hidden": "Общая тема скрыта",
    "general_forum_topic_unhidden": "Общая тема снова отображается",
    "giveaway_created": "Создан розыгрыш",
    "giveaway": "Розыгрыш",
    "giveaway_completed": "Розыгрыш завершён",
    "message_reaction": "Реакция на сообщение",
}


def type_msg(message: Message) -> str:
    """
    Определяет и возвращает тип сообщения на русском языке.

    :param message: объект Message от aiogram
    :return: строка с типом сообщения
    """
    return CONTENT_TYPE_RU.get(message.content_type, f"Неизвестный тип ({message.content_type})")

def type_chat(message: Message) -> str:
    """
    Преобразует информацию о чате в его тип на русском языке.

    :param message: Объект сообщения из aiogram, содержащий информацию о чате.
    :return: Тип чата строкой.
    """
    return CHAT_TYPES.get(message.chat.type, f"Неизвестный тип чата {message.chat.type}")
