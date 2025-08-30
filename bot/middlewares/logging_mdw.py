from typing import Callable, Awaitable, Any, Dict, Optional, Tuple, Set
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery, MaybeInaccessibleMessageUnion, User

from bot.utils import type_msg
from middleware.loggers import loggers  # ваш глобальный логгер
from configs import BotSettings, COMMANDS  # импортируем настройки и команды


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования апдейтов с определением типа события,
    пользователя и добавлением префикса проекта к типу лога.

    Автоматически добавляет префикс проекта (например, 'PRIMO-') к типам логов:
        - PRIMO-UPDATE: общий апдейт без определенного типа
        - PRIMO-MSG: текстовое сообщение от пользователя
        - PRIMO-CMD: команда (сообщение, начинающееся с любого префикса)
        - PRIMO-CBD: callback query от инлайн-кнопок
    """

    # Префикс проекта для логов
    PROJECT_PREFIX: str = "PRIMO"

    # Кэш для всех команд из COMMANDS
    _all_commands: Optional[Set[str]] = None

    def __init__(self):
        super().__init__()
        # Предварительно загружаем все команды
        self._load_all_commands()

    def _load_all_commands(self) -> None:
        """Загружает все команды из COMMANDS в множество для быстрого поиска."""
        if self._all_commands is None:
            self._all_commands = set()
            for command_list in COMMANDS.values():
                self._all_commands.update(command_list)

    def _is_command(self, text: str) -> bool:
        """
        Проверяет, является ли текст командой с любым префиксом.

        Args:
            text: Текст для проверки

        Returns:
            True если это команда, False если нет
        """
        if not text:
            return False

        # Проверяем все префиксы из BotSettings
        for prefix in BotSettings.PREFIX:
            if text.startswith(prefix):
                # Извлекаем команду без префикса
                command_without_prefix = text[len(prefix):].strip()
                # Проверяем, есть ли такая команда в нашем списке
                if command_without_prefix in self._all_commands:
                    return True

        # Также проверяем команды с префиксом / (стандартные)
        if text.startswith('/'):
            command_without_slash = text[1:].strip()
            if command_without_slash in self._all_commands:
                return True

        return False

    @staticmethod
    def _extract_command_name(text: str) -> str:
        """
        Извлекает название команды из текста.

        Args:
            text: Текст команды с префиксом

        Returns:
            Название команды без префикса
        """
        for prefix in BotSettings.PREFIX:
            if text.startswith(prefix):
                return text[len(prefix):].strip()

        if text.startswith('/'):
            return text[1:].strip()

        return text

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает входящее событие, определяет его тип, логирует с префиксом проекта
        и передает следующему обработчику.

        Args:
            handler: Следующий обработчик в цепочке middleware
            event: Входящее событие для обработки (Update, Message, CallbackQuery)
            data: Словарь с контекстными данными FSM

        Returns:
            Результат выполнения следующего обработчика

        Raises:
            Exception: Любое исключение, возникшее при обработке хендлером
        """
        # Определяем тип события и информацию для логирования
        log_type: str
        log_text: str
        message_obj: Optional[Message]

        log_type, log_text, message_obj = self._determine_event_type(event)

        # Добавляем префикс проекта к типу лога
        prefixed_log_type: str = f"{log_type}"

        # Определяем информацию о пользователе
        user_str: str = self._extract_user_info(event, message_obj)

        # Логируем получение события с префиксом проекта
        loggers.info(
            text=log_text,
            log_type=prefixed_log_type,
            user=user_str
        )

        try:
            # Передаем событие следующему обработчику
            result: Any = await handler(event, data)

            # Логируем успешное выполнение для команд
            if log_type == "CMD":
                loggers.info(
                    text=f"[SUCCESS] команда обработана",
                    log_type=prefixed_log_type,
                    user=user_str
                )

            return result

        except Exception as e:
            # Логируем ошибку при обработке с префиксом проекта
            loggers.error(
                text=f"Ошибка обработки: {str(e)}",
                log_type=prefixed_log_type,
                user=user_str
            )
            raise

    def _determine_event_type(
            self,
            event: TelegramObject
    ) -> Tuple[str, str, Optional[Message]]:
        """
        Определяет тип события и извлекает информацию для логирования.

        Args:
            event: Объект события для анализа

        Returns:
            Кортеж из (тип_лога, текст_лога, объект_сообщения)
        """
        log_type: str = "UPDATE"
        log_text: str = f"Получен апдейт: {type(event).__name__}"
        message_obj: Optional[Message] = None

        # Обработка Update объектов (основной тип в middleware)
        if isinstance(event, Update):
            # Пытаемся найти сообщение в различных полях Update
            message_obj = (
                    event.message or
                    event.edited_message or
                    event.channel_post or
                    event.edited_channel_post
            )

            if message_obj and message_obj.text:
                if self._is_command(message_obj.text):
                    log_type: str = "CMD"
                    log_text: str = f"использовал команду '{message_obj.text}'"
                else:
                    log_type: str = "MSG"
                    log_text: str = f"получено сообщение: {message_obj.text!r}"
            elif message_obj:
                # Не текстовое сообщение (фото, видео и т.д.)
                log_type: str = "MSG"
                log_text: str = f"получено сообщение: '{type_msg(message_obj)}'"
            elif event.callback_query:
                # Обработка callback query
                callback: CallbackQuery = event.callback_query
                log_type: str = "CBD"
                log_text: str = f"получен callback: {callback.data!r}"
                if callback.message:
                    message_obj: Optional[MaybeInaccessibleMessageUnion] = callback.message

        # Прямая обработка Message (если мидлварь зарегистрирован на messages)
        elif isinstance(event, Message):
            message_obj = event
            if event.text and self._is_command(event.text):
                log_type: str = "CMD"
                log_text: str = f"использовал команду '{event.text}'"
            elif event.text:
                log_type: str = "MSG"
                log_text: str = f"получено сообщение: {event.text!r}"
            else:
                log_type: str = "MSG"
                log_text: str = f"получено сообщение типа: {event.content_type}"

        # Прямая обработка CallbackQuery (если мидлварь зарегистрирован на callbacks)
        elif isinstance(event, CallbackQuery):
            log_type: str = "CBD"
            log_text: str = f"получен callback: {event.data!r}"
            if event.message:
                message_obj = event.message

        return log_type, log_text, message_obj

    @staticmethod
    def _extract_user_info(
            event: TelegramObject,
            message: Optional[Message] = None
    ) -> str:
        """
        Извлекает информацию о пользователе из события.

        Args:
            event: Объект события (Update, Message или CallbackQuery)
            message: Объект Message (если уже определен)

        Returns:
            Строка с идентификатором пользователя в формате '@username' или 'id<user_id>'
        """
        user_str: str = "@System"

        # Для CallbackQuery извлекаем пользователя из самого callback'а
        if isinstance(event, CallbackQuery) and hasattr(event, 'from_user') and event.from_user:
            user = event.from_user
            user_str: str = f"@{user.username}" if user.username else f"id{user.id}"

        # Для Message извлекаем пользователя из сообщения
        elif isinstance(event, Message) and hasattr(event, 'from_user') and event.from_user:
            user = event.from_user
            user_str: str = f"@{user.username}" if user.username else f"id{user.id}"

        # Для Update с callback_query
        elif (isinstance(event, Update) and
              event.callback_query and
              hasattr(event.callback_query, 'from_user') and
              event.callback_query.from_user):
            user = event.callback_query.from_user
            user_str: str = f"@{user.username}" if user.username else f"id{user.id}"

        # Для Update с сообщением
        elif (isinstance(event, Update) and
              (event.message or event.edited_message) and
              hasattr(event.message or event.edited_message, 'from_user')):
            msg = event.message or event.edited_message
            if msg and msg.from_user:
                user: Optional[User] = msg.from_user
                user_str: str = f"@{user.username}" if user.username else f"id{user.id}"

        # Если передан message объект
        elif message and hasattr(message, 'from_user') and message.from_user:
            user: Optional[User] = message.from_user
            user_str: str = f"@{user.username}" if user.username else f"id{user.id}"

        return user_str