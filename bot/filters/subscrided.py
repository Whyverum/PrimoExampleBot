from aiogram.types import Message, ResultChatMemberUnion
from aiogram.filters import BaseFilter
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from typing import Union

# Настройки экспорта
__all__ = ("FilterSubscribed",)


class FilterSubscribed(BaseFilter):
    """
    Фильтр для проверки подписки пользователя на один или несколько каналов.
    Поддерживает как публичные каналы (username), так и приватные (ID).

    Пример:
    # Проверка сразу двух каналов: публичный по username и приватный по ID
    @router.message(FilterSubscribed(["@public_channel", -1001234567890]))
    async def only_subscribed(message: Message):
        await message.answer("Ты подписан и на публичный, и на приватный канал ✅")
    """
    def __init__(self, channels: list[Union[str, int]]) -> None:
        self.channels = channels

    async def __call__(self, message: Message, bot: Bot) -> bool:
        for channel in self.channels:
            try:
                member: ResultChatMemberUnion = await bot.get_chat_member(
                    chat_id=channel,
                    user_id=message.from_user.id
                )
                if member.status in ("left", "kicked"):
                    return False

            except (TelegramBadRequest, TelegramForbiddenError):
                # Канал недоступен, либо у бота нет прав
                return False

        return True
