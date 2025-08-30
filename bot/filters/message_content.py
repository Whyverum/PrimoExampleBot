from aiogram.filters import BaseFilter
from aiogram.types import Message

# Настройка экспорта
__all__ = ("IsReply", "IsForwarded", "HasMedia", "ContainsURL",)


class IsReply(BaseFilter):
    """
    Сообщение является ответом.

    Example:
        @router.message(IsReply())
        async def handler(msg: Message):
            await msg.answer("Это реплай ✅")
    """
    async def __call__(self, message: Message) -> bool:
        return message.reply_to_message is not None


class IsForwarded(BaseFilter):
    """
    Сообщение переслано из другого чата/от пользователя.

    Example:
        @router.message(IsForwarded())
        async def handler(msg: Message):
            await msg.answer("Это пересланное сообщение 🔄")
    """
    async def __call__(self, message: Message) -> bool:
        return (message.forward_from is not None) or (message.forward_from_chat is not None)


class HasMedia(BaseFilter):
    """
    Сообщение содержит медиа (фото, видео, документ и т.д.).

    Example:
        @router.message(HasMedia())
        async def handler(msg: Message):
            await msg.answer("Это медиа ✅")
    """
    async def __call__(self, message: Message) -> bool:
        return any([
            message.photo,
            message.video,
            message.document,
            message.audio,
            message.voice,
            message.video_note,
            message.sticker,
        ])


class ContainsURL(BaseFilter):
    """
    Сообщение содержит ссылку (http/https).

    Example:
        @router.message(ContainsURL())
        async def handler(msg: Message):
            await msg.answer("Это сообщение с ссылкой 🔗")
    """
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return "http://" in message.text or "https://" in message.text
