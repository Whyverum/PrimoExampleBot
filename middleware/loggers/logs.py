from sys import stderr
from pathlib import Path
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Callable, Optional, TypeVar, cast, Final

from loguru import logger
from aiogram.types import Message, User

from configs.config import BotEdit, LogConfig

# Экспортируемые объекты
__all__ = ('Logger', 'setup_logging', 'loggers', 'log',)

# Универсальный тип для функций
F: TypeVar = TypeVar('F', bound=Callable[..., Any])


class Logger:
    """
    Кастомный логгер с поддержкой декораторов и прямого вызова.

    Attributes:
        system_name: Имя системы для логирования
        _log_format: Формат логов
    """
    _log_format: Final[str] = (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> <red>|</red> '
        '<blue>{extra[system]}-{extra[log_type]}</blue> <red>| '
        '{extra[user]} |</red> <level>{message}</level>'
    )

    def __init__(self, system_name: str = BotEdit.PROJECT_NAME) -> None:
        """
        Инициализация логгера.

        :param system_name: Имя системы для логирования
        """
        self.system_name = system_name
        self._setup_done = False

    def setup(self, start: bool = True) -> None:
        """
        Настройка обработчиков Loguru: консоль и файлы.

        :param start: Если True, сразу логирует запуск проекта
        """
        if self._setup_done:
            return

        # Полная очистка настроек
        logger.remove()

        # Создание директории для файловых логов
        log_dir: Path = Path(getattr(LogConfig, 'DIR', 'logs'))
        log_dir.mkdir(parents=True, exist_ok=True)

        # Консольный лог
        if getattr(LogConfig, 'CONSOLE', False):
            logger.add(
                sink=stderr,
                format=self._log_format,
                colorize=True,
                level='DEBUG',
                filter=lambda rec: rec['extra'].get('log_type') != 'DEBUG'
            )

        # Файловые логи
        if getattr(LogConfig, 'FILE', False):
            # Общий лог
            logger.add(
                sink=log_dir / 'bot.log',
                rotation=getattr(LogConfig, 'ROTATION', '100 MB'),
                retention=getattr(LogConfig, 'RETENTION', '7 days'),
                format=self._log_format,
                level='DEBUG',
                enqueue=True,
                backtrace=True,
                diagnose=True
            )
            # Раздельные логи по уровням
            for level_name in ['INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL']:
                logger.add(
                    sink=log_dir / f'{level_name.lower()}.log',
                    rotation='10 MB',
                    retention='7 days',
                    format=self._log_format,
                    level=level_name,
                    filter=lambda rec, lvl=level_name: rec['level'].name == lvl,
                    enqueue=True
                )

        self._setup_done = True

        # Логируем старт
        if start:
            self.log_entry(
                level='INFO',
                text='Запуск проекта...',
                log_type='START'
            )

    @staticmethod
    def format_user(message: Optional[Message] = None) -> str:
        """
        Форматирует имя пользователя из объекта Message.

        :param message: Объект aiogram.types.Message
        :return: Строка '@username' или 'id<user_id>'
        """
        if message is None or message.from_user is None:
            return '@System'
        user: User = message.from_user
        return f"@{user.username}" if user.username else f"id{user.id}"

    def log_entry(
            self,
            level: str,
            text: str,
            log_type: str,
            user: Optional[str] = None,
            message: Optional[Message] = None
    ) -> None:
        """
        Основной метод для записи логов.

        :param level: Уровень логирования (например, 'INFO')
        :param text: Сообщение для логирования
        :param log_type: Кастомный тип лога (например, 'HANDLER')
        :param user: Явно указанный пользователь
        :param message: Объект Message для извлечения юзера
        """
        actual_user: str = user or self.format_user(message)
        logger.bind(
            system=self.system_name,
            user=actual_user,
            log_type=log_type
        ).log(level, text)

    def log(
            self,
            level: str = 'INFO',
            log_type: str = '',
            text: Optional[str] = None
    ) -> Callable[[F], F]:
        """
        Декоратор для логирования функций.

        :param level: Уровень логирования
        :param log_type: Категория лога
        :param text: Кастомный текст сообщения
        :return: Декорированную функцию
        """

        def decorator(func: F) -> F:
            is_coroutine = iscoroutinefunction(func)
            action_text = text or f'Вызов {func.__name__}'

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                message = self._find_message(args)
                self.log_entry(level, f"[START] {action_text}", log_type, message=message)
                try:
                    result = func(*args, **kwargs)
                    self.log_entry(level, f"[SUCCESS] {action_text}", log_type, message=message)
                    return result
                except Exception as e:
                    self.log_entry(
                        'ERROR',
                        f"[ERROR] {action_text} | Exception: {e!r}",
                        log_type,
                        message=message
                    )
                    raise

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                message = self._find_message(args)
                self.log_entry(level, f"[START] {action_text}", log_type, message=message)
                try:
                    result = await func(*args, **kwargs)
                    self.log_entry(level, f"[SUCCESS] {action_text}", log_type, message=message)
                    return result
                except Exception as e:
                    self.log_entry(
                        'ERROR',
                        f"[ERROR] {action_text} | Exception: {e!r}",
                        log_type,
                        message=message
                    )
                    raise

            return cast(F, async_wrapper if is_coroutine else sync_wrapper)

        return decorator

    @staticmethod
    def _find_message(args: tuple[Any, ...]) -> Optional[Message]:
        """
        Ищет объект Message в аргументах функции.

        :param args: Аргументы функции
        :return: Найденный Message или None
        """
        return next((arg for arg in args if isinstance(arg, Message)), None)

    # Методы для прямого вызова
    def debug(self, text: str, log_type: str = 'BOT', user: Optional[str] = None,
              message: Optional[Message] = None) -> None:
        self.log_entry('DEBUG', text, log_type, user, message)

    def info(self, text: str, log_type: str = 'BOT', user: Optional[str] = None,
             message: Optional[Message] = None) -> None:
        self.log_entry('INFO', text, log_type, user, message)

    def warning(self, text: str, log_type: str = 'BOT', user: Optional[str] = None,
                message: Optional[Message] = None) -> None:
        self.log_entry('WARNING', text, log_type, user, message)

    def error(self, text: str, log_type: str = 'BOT', user: Optional[str] = None,
              message: Optional[Message] = None) -> None:
        self.log_entry('ERROR', text, log_type, user, message)

    def critical(self, text: str, log_type: str = 'BOT', user: Optional[str] = None,
                 message: Optional[Message] = None) -> None:
        self.log_entry('CRITICAL', text, log_type, user, message)


# Создаем глобальный экземпляр логгера
loggers: Logger = Logger()

# Экспортируемые функции для обратной совместимости
setup_logging = loggers.setup
log = loggers.log
