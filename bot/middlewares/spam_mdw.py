from typing import Callable, Awaitable, Any, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import time
from collections import defaultdict

from middleware.loggers import loggers  # ваш логгер


class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов от пользователей (анти-спам).

    Зачем нужен:
    - Защита от DDoS и флуда
    - Предотвращение злоупотребления ботом
    - Контроль нагрузки на сервер
    """

    def __init__(self, rate_limit: int = 10, time_period: float = 2.0):
        """
        Инициализация rate limit middleware.

        Args:
            rate_limit: Максимальное количество запросов за период
            time_period: Период времени в секундах
        """
        self.rate_limit = rate_limit
        self.time_period = time_period
        self.user_calls: Dict[int, list[float]] = defaultdict(list)
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
            log: bool = False,
    ) -> Any:
        """
        Проверяет rate limit перед обработкой запроса.
        """
        # Пропускаем не-сообщения и не-колбэки
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user_id: int = event.from_user.id
        user_str: str = f"@{event.from_user.username}" if event.from_user.username else f"id{user_id}"
        current_time: float = time.time()

        # Очищаем старые запросы
        self.user_calls[user_id] = [
            call_time for call_time in self.user_calls[user_id]
            if current_time - call_time < self.time_period
        ]

        # Логируем текущее состояние rate limit
        if log:
            loggers.debug(
                text=f"Rate limit: {len(self.user_calls[user_id])}/{self.rate_limit} за {self.time_period}сек",
                log_type="RATE_LIMIT_STATUS",
                user=user_str
            )

        # Проверяем текущий лимит
        if len(self.user_calls[user_id]) >= self.rate_limit:
            # Логируем попытку спама
            if log:
                loggers.warning(
                    text=f"Превышен rate limit ({self.rate_limit}/{self.time_period}сек)",
                    log_type="RATE_LIMIT_EXCEEDED",
                    user=user_str
                )

            # Отправляем сообщение о превышении лимита
            if isinstance(event, Message):
                await event.answer(
                    text="⏳ Слишком много запросов! Пожалуйста, подождите немного.",
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    text="⏳ Подождите немного перед следующим действием.",
                    show_alert=True
                )

            return None

        # Добавляем текущий запрос и продолжаем обработку
        self.user_calls[user_id].append(current_time)

        loggers.debug(
            text=f"Запрос добавлен в rate limit",
            log_type="RATE_LIMIT_ADDED",
            user=user_str
        )

        return await handler(event, data)