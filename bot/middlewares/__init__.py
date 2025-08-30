from aiogram import Dispatcher, Bot

from configs import ImportantID
from .logging_mdw import LoggingMiddleware
from .msg_mdw import MessageCounterMiddleware
from .spam_mdw import RateLimitMiddleware
from .subscription_mdw import SubscriptionMiddleware
from .error_mdw import ErrorHandlingMiddleware
from .time_mdw import TimingMiddleware

# Настройки экспорта
__all__ = (
    "LoggingMiddleware",
    "SubscriptionMiddleware",
    "RateLimitMiddleware",
    "ErrorHandlingMiddleware",
    "TimingMiddleware",
    "MessageCounterMiddleware",
    "setup_middlewares",)


def setup_middlewares(dp: Dispatcher, bot: Bot, channel_ids: list[int | str] = None) -> None:
    """
    Регистрирует все middleware в диспетчере.
    """
    channel_ids: list = channel_ids or []

    # Middleware для ВСЕХ событий (update level)
    middlewares_updates: list = [
        TimingMiddleware(),  # Замер времени
        LoggingMiddleware(),  # Логирование
        ErrorHandlingMiddleware(admin_ids=ImportantID.ADMIN_ID),  # Обработка ошибок
    ]

    # Middleware только для СООБЩЕНИЙ (message level)
    middlewares_msg: list = [
        #RateLimitMiddleware(rate_limit=3, time_period=5.0),  # Антифлуд
        #SubscriptionMiddleware(bot=bot, channel_ids=channel_ids),  # Проверка подписки
        MessageCounterMiddleware(),  # Подсчет сообщений
    ]

    # Регистрируем middleware для всех событий
    for middleware in middlewares_updates:
        dp.update.middleware(middleware)

    # Регистрируем middleware только для сообщений
    for middleware in middlewares_msg:
        dp.message.middleware(middleware)
