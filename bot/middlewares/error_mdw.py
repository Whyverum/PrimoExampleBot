from typing import Callable, Awaitable, Any, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, Update

from middleware.loggers import loggers  # ваш логгер


class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Middleware для глобальной обработки ошибок в хендлерах.

    Зачем нужен:
    - Централизованная обработка исключений
    - Уведомление администраторов об ошибках
    - Graceful degradation при сбоях
    """

    def __init__(self, admin_ids: list[int]):
        """
        Инициализация middleware обработки ошибок.

        Args:
            admin_ids: Список ID администраторов для уведомлений
        """
        self.admin_ids = admin_ids
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
        Перехватывает и обрабатывает ошибки в хендлерах.
        """
        try:
            return await handler(event, data)

        except Exception as e:
            # Получаем информацию о пользователе безопасным способом
            user_str = self._extract_user_info(event)

            # Логируем ошибку
            error_message = f"Ошибка в хендлере: {type(e).__name__}: {str(e)}"

            loggers.error(
                text=error_message,
                log_type="HANDLER_ERROR",
                user=user_str
            )

            # Уведомляем администраторов
            await self._notify_admins(error_message, event, user_str)

            # Отправляем пользователю сообщение об ошибке
            await self._send_error_message(event, user_str)

            return None

    @staticmethod
    def _extract_user_info(event: TelegramObject) -> str:
        """
        Безопасно извлекает информацию о пользователе из события.

        Args:
            event: Объект события

        Returns:
            Строка с идентификатором пользователя
        """
        user_str = "@System"

        # Для Message и CallbackQuery
        if isinstance(event, (Message, CallbackQuery)) and hasattr(event, 'from_user') and event.from_user:
            user = event.from_user
            user_str = f"@{user.username}" if user.username else f"id{user.id}"

        # Для Update (который содержит message или callback_query)
        elif isinstance(event, Update):
            # Пытаемся найти пользователя в различных полях Update
            user_object = None
            if event.message and event.message.from_user:
                user_object = event.message.from_user
            elif event.edited_message and event.edited_message.from_user:
                user_object = event.edited_message.from_user
            elif event.callback_query and event.callback_query.from_user:
                user_object = event.callback_query.from_user
            elif event.channel_post and event.channel_post.from_user:
                user_object = event.channel_post.from_user
            elif event.edited_channel_post and event.edited_channel_post.from_user:
                user_object = event.edited_channel_post.from_user

            if user_object:
                user_str = f"@{user_object.username}" if user_object.username else f"id{user_object.id}"

        return user_str

    @staticmethod
    def _extract_event_text(event: TelegramObject) -> str:
        """
        Безопасно извлекает текст из события.

        Args:
            event: Объект события

        Returns:
            Текст события или пустая строка
        """
        event_text = ""

        # Для Message
        if isinstance(event, Message) and hasattr(event, 'text') and event.text:
            event_text = event.text
        # Для CallbackQuery
        elif isinstance(event, CallbackQuery) and hasattr(event, 'data') and event.data:
            event_text = f"callback: {event.data}"
        # Для Update
        elif isinstance(event, Update):
            if event.message and event.message.text:
                event_text = event.message.text
            elif event.callback_query and event.callback_query.data:
                event_text = f"callback: {event.callback_query.data}"
            elif event.edited_message and event.edited_message.text:
                event_text = event.edited_message.text

        return event_text[:100] + "..." if len(event_text) > 100 else event_text

    async def _notify_admins(
            self,
            error_message: str,
            event: TelegramObject,
            user_str: str
    ) -> None:
        """Уведомляет администраторов об ошибке."""
        from aiogram import Bot
        bot: Bot = event.bot if hasattr(event, 'bot') else None

        if bot:
            for admin_id in self.admin_ids:
                try:
                    event_info = f"Событие: {type(event).__name__}"
                    event_text = self._extract_event_text(event)
                    if event_text:
                        event_info += f", текст: {event_text}"

                    full_message = (
                        f"🚨 Ошибка в боте:\n\n"
                        f"Пользователь: {user_str}\n"
                        f"Ошибка: {error_message}\n"
                        f"{event_info}"
                    )

                    await bot.send_message(admin_id, full_message)

                    loggers.info(
                        text=f"Администратор {admin_id} уведомлен об ошибке",
                        log_type="ADMIN_NOTIFIED",
                        user=user_str
                    )

                except Exception as e:
                    loggers.error(
                        text=f"Не удалось уведомить админа {admin_id}: {e}",
                        log_type="ADMIN_NOTIFY_ERROR",
                        user=user_str
                    )

    @staticmethod
    async def _send_error_message(
            event: TelegramObject,
            user_str: str
    ) -> None:
        """Отправляет пользователю сообщение об ошибке."""
        error_text = (
            "⚠️ Произошла непредвиденная ошибка. "
            "Разработчики уже уведомлены и работают над исправлением.\n\n"
            "Попробуйте повторить действие позже или нажмите /start"
        )

        try:
            if isinstance(event, Message):
                await event.answer(error_text)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(error_text)
                await event.answer()
            elif isinstance(event, Update) and event.message:
                await event.message.answer(error_text)

            loggers.info(
                text="Пользователю отправлено сообщение об ошибке",
                log_type="ERROR_MESSAGE_SENT",
                user=user_str
            )

        except Exception as e:
            loggers.error(
                text=f"Не удалось отправить сообщение об ошибке: {e}",
                log_type="ERROR_MESSAGE_FAILED",
                user=user_str
            )