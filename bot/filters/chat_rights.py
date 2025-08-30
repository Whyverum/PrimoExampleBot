from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message, ResultChatMemberUnion
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

# Настройка экспорта
__all__ = ("IsChatCreator", "IsAdmin", "IsModerator",)


class IsChatCreator(BaseFilter):
    """
    Пользователь является создателем чата.

    Example:
        @router.message(IsChatCreator())
        async def handler(msg: Message):
            await msg.answer("Ты создатель этого чата 👑")
    """
    async def __call__(self, message: Message, bot: Bot) -> bool:
        try:
            member: ResultChatMemberUnion = await bot.get_chat_member(message.chat.id, message.from_user.id)
            return member.status == "creator"
        except (TelegramBadRequest, TelegramForbiddenError):
            return False


class IsAdmin(BaseFilter):
    """
    Пользователь является администратором (или создателем).

    Example:
        @router.message(IsAdmin())
        async def handler(msg: Message):
            await msg.answer("Ты админ ✅")
    """
    async def __call__(self, message: Message, bot: Bot) -> bool:
        try:
            member: ResultChatMemberUnion = await bot.get_chat_member(message.chat.id, message.from_user.id)
            return member.status in {"administrator", "creator"}
        except (TelegramBadRequest, TelegramForbiddenError):
            return False


class IsModerator(BaseFilter):
    """
    Администратор с модераторскими правами:
    - удаление сообщений
    - ограничение пользователей
    - закрепление сообщений

    Example:
        @router.message(IsModerator())
        async def handler(msg: Message):
            await msg.answer("Ты модератор ✅")
    """
    async def __call__(self, message: Message, bot: Bot) -> bool:
        try:
            member: ResultChatMemberUnion = await bot.get_chat_member(message.chat.id, message.from_user.id)

            if member.status == "creator":
                return True
            if member.status != "administrator":
                return False

            required_rights: list[bool] = [
                getattr(member, "can_delete_messages", False),
                getattr(member, "can_restrict_members", False),
                getattr(member, "can_pin_messages", False),
            ]
            return all(required_rights)

        except (TelegramBadRequest, TelegramForbiddenError):
            return False
