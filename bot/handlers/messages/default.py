from aiogram import Router
from aiogram.types import Message, CallbackQuery

from bot.utils import type_msg
from middleware.loggers import loggers

# Настройки экспорта и роутера
__all__ = ("router",)
CMD: str = "msg"
router: Router = Router(name=f"{CMD}_cmd_router")


@router.message()
async def default_messages(message: Message | CallbackQuery) -> None:
    """Обработчик всех необработанных сообщений."""
