from aiogram.filters import BaseFilter
from aiogram.types import Message

# Настройка экспорта
__all__ = ("IsPrivate", "IsGroup",)


class IsPrivate(BaseFilter):
    """
    Сообщение в личке с ботом.

    Example:
        @router.message(IsPrivate())
        async def handler(msg: Message):
            await msg.answer("Это ЛС ✅")
    """
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == "private"


class IsGroup(BaseFilter):
    """
    Сообщение в группе или супергруппе.

    Example:
        @router.message(IsGroup())
        async def handler(msg: Message):
            await msg.answer("Это сообщение в группе ✅")
    """
    async def __call__(self, message: Message) -> bool:
        return message.chat.type in {"group", "supergroup"}
