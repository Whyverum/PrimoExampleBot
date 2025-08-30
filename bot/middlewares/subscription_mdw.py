from typing import Callable, Awaitable, Any, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from middleware.loggers import loggers  # ваш логгер


class SubscriptionMiddleware(BaseMiddleware):
    """
    Middleware для проверки подписки пользователя на необходимые каналы.
    Блокирует обработку команд, если пользователь не подписан.

    Зачем нужен:
    - Автоматическая проверка подписки для всех входящих сообщений
    - Единая точка управления подписками
    - Предотвращение доступа к функционалу без подписки
    """

    def __init__(self, bot: Bot, channel_ids: list[int | str]):
        """
        Инициализация middleware проверки подписки.

        Args:
            bot: Экземпляр бота
            channel_ids: Список ID каналов/чатов для проверки подписки
        """
        self.bot = bot
        self.channel_ids = channel_ids
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
        Проверяет подписку пользователя перед обработкой команды.
        """
        # Пропускаем не-сообщения и не-колбэки
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user_id: int = event.from_user.id
        user_str: str = f"@{event.from_user.username}" if event.from_user.username else f"id{user_id}"

        # Логируем начало проверки подписки
        loggers.info(
            text=f"Проверка подписки для пользователя",
            log_type="SUBSCRIPTION_CHECK",
            user=user_str
        )

        # Проверяем подписку на все required каналы
        not_subscribed_channels: list[str] = []

        for channel_id in self.channel_ids:
            try:
                member = await self.bot.get_chat_member(
                    chat_id=channel_id,
                    user_id=user_id
                )
                # Проверяем, что пользователь является участником
                if member.status not in ['member', 'administrator', 'creator']:
                    not_subscribed_channels.append(str(channel_id))

            except TelegramBadRequest as e:
                loggers.error(
                    text=f"Ошибка проверки подписки на канал {channel_id}: {e}",
                    log_type="SUBSCRIPTION_ERROR",
                    user=user_str
                )

        # Если пользователь не подписан на некоторые каналы
        if not_subscribed_channels:
            loggers.warning(
                text=f"Пользователь не подписан на каналы: {', '.join(not_subscribed_channels)}",
                log_type="SUBSCRIPTION_FAILED",
                user=user_str
            )

            warning_text = (
                "📢 Для использования бота необходимо подписаться на наши каналы!\n\n"
                "После подписки нажмите /start для продолжения."
            )

            # Создаем кнопку "Проверить подписку"
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="✅ Я подписался",
                        callback_data="check_subscription"
                    )
                ]]
            )

            if isinstance(event, Message):
                await event.answer(warning_text, reply_markup=keyboard)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(warning_text, reply_markup=keyboard)
                await event.answer()

            return None

        # Логируем успешную проверку подписки
        loggers.info(
            text="Пользователь подписан на все required каналы",
            log_type="SUBSCRIPTION_SUCCESS",
            user=user_str
        )

        # Если подписка есть, продолжаем обработку
        return await handler(event, data)