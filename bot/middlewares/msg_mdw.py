import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message
from database import db

logger = logging.getLogger(__name__)

class MessageCounterMiddleware(BaseMiddleware):
    """
    Middleware для подсчёта сообщений в группах и супергруппах.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        # Проверяем, что сообщение пришло из группового чата и не от бота
        if (event.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP) and 
            not event.from_user.is_bot):
            try:
                await self.process_group_message(event)
            except Exception as e:
                logger.error(msg=f"Ошибка при обработке сообщения: {e}", exc_info=True)

        return await handler(event, data)

    @staticmethod
    async def process_group_message(message: Message) -> None:
        """
        Обработка сообщения из группового чата.
        """
        user_id = message.from_user.id
        message_text = message.text or message.caption or ""

        # Добавляем пользователя (если его ещё нет)
        await db.add_user(
            user_id=user_id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

        # Сохраняем сообщение
        await db.add_message(
            user_id=user_id,
            message_text=message_text,
            created_at=message.date,
        )
        logger.info(f"Сообщение от пользователя {user_id} сохранено в БД")
