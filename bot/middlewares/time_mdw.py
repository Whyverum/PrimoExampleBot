from typing import Callable, Awaitable, Any, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, Update
from time import time

from middleware.loggers import loggers  # ваш логгер


class TimingMiddleware(BaseMiddleware):
    """
    Middleware для измерения времени выполнения хендлеров.

    Зачем нужен:
    - Мониторинг производительности хендлеров
    - Выявление медленных запросов
    - Оптимизация кода бота
    """

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
            perm: str = None,
    ) -> Any:
        """
        Измеряет время выполнения хендлера.
        """
        start_time: float = time()

        try:
            result = await handler(event, data)
            return result

        finally:
            execution_time: float = time() - start_time

            # Получаем информацию о пользователе безопасным способом
            user_str: str = "@System"

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

            # Логируем время выполнения
            if execution_time > 1.0 and perm:  # Медленные запросы
                loggers.warning(
                    text=f"Медленный хендлер: {execution_time:.2f}сек",
                    log_type="SLOW_HANDLER",
                    user=user_str
                )
            elif execution_time > 0.5 and perm == "medium":  # Средние запросы
                loggers.info(
                    text=f"Среднее время выполнения: {execution_time:.3f}сек",
                    log_type="HANDLER_TIMING",
                    user=user_str
                )
            elif perm == "fast":  # Быстрые запросы
                loggers.debug(
                    text=f"Быстрое выполнение: {execution_time:.3f}сек",
                    log_type="HANDLER_TIMING_FAST",
                    user=user_str
                )