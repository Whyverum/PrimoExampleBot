from pathlib import Path
from urllib.parse import urlparse, ParseResult
from typing import ClassVar, Final, Optional, Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from aiogram.types import ChatAdministratorRights


class Settings(BaseSettings):
    """Улучшенный класс настроек с комплексной валидацией"""

    # Конфигурация загрузки переменных окружения
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        validate_default=True,
    )

    # Режимы и базовые параметры
    PYTHONUNBUFFERED: str = "1"
    LOCALE_PATH: str = "locales"

    DEBUG: bool = False
    OWNER: str = "@verdise"

    # Токены бота
    BOT_TOKEN: Optional[str] = None
    BOT_DEBUG_TOKEN: Optional[str] = None

    # Параметры сообщений
    PARSE_MODE: str = "HTML"
    ENCOD: str = "utf-8"
    TIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    PREFIX: str = "/!.&?"
    BOT_LANGUAGE: str = "Aiogram3"

    # Настройки сообщений
    DISABLE_NOTIFICATION: bool = False
    PROTECT_CONTENT: bool = False
    ALLOW_SENDING_WITHOUT_REPLY: bool = True
    LINK_PREVIEW_IS_DISABLED: bool = False
    LINK_PREVIEW_PREFER_SMALL_MEDIA: bool = False
    LINK_PREVIEW_PREFER_LARGE_MEDIA: bool = True
    LINK_PREVIEW_SHOW_ABOVE_TEXT: bool = True
    SHOW_CAPTION_ABOVE_MEDIA: bool = False

    # Разрешения и логирование
    BOT_EDIT: bool = True
    START_INFO_CONSOLE: bool = True
    START_INFO_TO_FILE: bool = True
    LOG_CONSOLE: bool = True
    LOG_FILE: bool = True
    LOG_DIR: Path = Path('Logs')
    LOG_FILE_INFO: Path = Path('bot_info.log')

    # Вебхук
    WEBHOOK: bool = False
    WEBHOOK_URL: str = "https://bot.primo.dpdns.org/webhook"  # публичный HTTPS url
    WEBAPP_HOST: str = "0.0.0.0"  # адрес, на котором слушает uvicorn внутри контейнера
    WEBAPP_PORT: int = 3131
    LOG_LEVEL: str = "warning"
    ACCES_LOG: bool = False

    # API ключи
    API_KEY: Optional[str] = None
    WEB_API_KEY: Optional[str] = None
    WEATHER_API_KEY: Optional[str] = None

    # Пользовательские данные
    TG_API_UID: int = 0
    TG_API_HASH: Optional[str] = None

    # Идентификаторы
    ADMIN_ID: list[int] = []
    MODERATOR_ID: int = 0
    IMPORTANT_ID: int = 0
    IMPORTANT_GROUP_ID: int = 0
    IMPORTANT_CHANNEL_ID: int = 0
    SUPPORT_CHAT_ID: int = 0

    # Настройки бота
    PROJECT_NAME: str = "PRIMO"
    BOT_NAME: str = "Первозданная Жемчужина"
    BOT_DESCRIPTION: Optional[str] = None
    BOT_SHORT_DESCRIPTION: Optional[str] = None

    # Ролевой проект
    RP_NAME: Optional[str] = "𝘗𝘳𝘪𝘮𝘰 𝘞𝘰𝘳𝘭𝘥"
    INFO_URL: Optional[str] = "https://t.me/PrimoWorldRP"
    FLUD_URL: Optional[str] = "https://t.me/PrimoWorldRP"
    RP_URL: Optional[str] = "https://t.me/PrimoWorldRP"
    LIFE_URL: Optional[str] = "https://t.me/PrimoWorldRP"
    RP_OWNER: Optional[str] = None
    ROLES: list[str] = ["Альбедо", "Чжун Ли", "Кэйа"]

    # Права администратора
    ANONYMOUS: bool = False
    MANAGE_CHAT: bool = True
    CHANGE_INFO: bool = True
    PROMOTE_MEMBERS: bool = True
    RESTRICT_MEMBERS: bool = True
    POST_MESSAGE: bool = True
    MANAGE_TOPICS: bool = True
    INVITE_USER: bool = True
    DELETE_MESSAGES: bool = True
    MANAGE_VIDEO_CHATS: bool = True
    EDIT_MESSAGES: bool = True
    PIN_MESSAGE: bool = True
    POST_STORIES: bool = True
    EDIT_STORIES: bool = True
    DELETE_STORIES: bool = True

    # ================= ВАЛИДАТОРЫ =================

    @field_validator('PYTHONUNBUFFERED')
    def validate_unbuffered(cls, v: str) -> str:
        """Проверка корректности значения буферизации"""
        if v not in ('0', '1'):
            raise ValueError("PYTHONUNBUFFERED должен быть '0' или '1'")
        return v

    @field_validator('PARSE_MODE')
    def validate_parse_mode(cls, v: str) -> str:
        """Проверка допустимого режима разметки"""
        allowed_modes: set[str] = {"HTML", "Markdown", "MarkdownV2"}
        if v not in allowed_modes:
            raise ValueError(f"Недопустимый PARSE_MODE. Допустимые значения: {', '.join(allowed_modes)}")
        return v

    @field_validator('PREFIX')
    def validate_prefix(cls, v: str) -> str:
        """Очистка и проверка префиксов команд"""
        cleaned: str = ''.join(sorted(set(v), key=v.index))  # Удаление дубликатов с сохранением порядка
        if len(cleaned) < 1:
            raise ValueError("PREFIX должен содержать хотя бы один символ")
        return cleaned

    @field_validator('LOG_DIR', 'LOG_FILE_INFO', mode='before')
    def validate_paths(cls, v: Any) -> Path:
        """Преобразование путей в объекты Path"""
        return Path(v) if isinstance(v, str) else v

    @field_validator('TG_API_UID', 'MODERATOR_ID')
    def validate_ids(cls, v: int) -> int:
        """Проверка корректности идентификаторов"""
        if v < 0:
            raise ValueError("ID не может быть отрицательным")
        return v

    @field_validator('WEBHOOK_URL')
    def validate_webhook_url(cls, v: str) -> str:
        """Базовая проверка URL вебхука"""
        parsed: ParseResult  = urlparse(v)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError("Некорректный URL вебхука")
        return v

    @field_validator('BOT_NAME', 'PROJECT_NAME', 'OWNER')
    def validate_non_empty(cls, v: str) -> str:
        """Проверка непустых строк"""
        if not v.strip():
            raise ValueError("Поле не может быть пустым")
        return v

    @model_validator(mode='after')
    def validate_bot_token(cls, setting: "Settings") -> "Settings":
        """Проверка наличия необходимых токенов"""
        if setting.DEBUG and not setting.BOT_DEBUG_TOKEN:
            raise ValueError("Требуется BOT_DEBUG_TOKEN в режиме DEBUG")
        if not setting.DEBUG and not setting.BOT_TOKEN:
            raise ValueError("Требуется BOT_TOKEN для рабочего режима")
        return setting

    @model_validator(mode='after')
    def validate_webhook_config(cls, setting: "Settings") -> "Settings":
        """Проверка конфигурации вебхука"""
        if setting.WEBHOOK and not setting.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL обязателен при включенном WEBHOOK")
        return setting

    @model_validator(mode='after')
    def validate_logging_paths(cls, setting: "Settings") -> "Settings":
        """Создание директорий для логов при необходимости"""
        if setting.LOG_FILE and not setting.LOG_DIR.exists():
            setting.LOG_DIR.mkdir(parents=True, exist_ok=True)
        return setting

    @model_validator(mode='after')
    def set_dynamic_descriptions(cls, setting: "Settings") -> "Settings":
        """Динамическая установка описаний бота"""
        if setting.BOT_DESCRIPTION is None:
            setting.BOT_DESCRIPTION = f"Ваш помощник в удивительные миры! Prod. by:『{setting.OWNER}』"
        if setting.BOT_SHORT_DESCRIPTION is None:
            setting.BOT_SHORT_DESCRIPTION = f"Тех.поддержка: {setting.OWNER}"
        return setting

    # ================= СВОЙСТВА =================

    @property
    def rights(self) -> ChatAdministratorRights:
        """Права администратора бота"""
        return ChatAdministratorRights(
            is_anonymous=self.ANONYMOUS,
            can_manage_chat=self.MANAGE_CHAT,
            can_delete_messages=self.DELETE_MESSAGES,
            can_manage_video_chats=self.MANAGE_VIDEO_CHATS,
            can_restrict_members=self.RESTRICT_MEMBERS,
            can_promote_members=self.PROMOTE_MEMBERS,
            can_change_info=self.CHANGE_INFO,
            can_invite_users=self.INVITE_USER,
            can_post_stories=self.POST_STORIES,
            can_edit_stories=self.EDIT_STORIES,
            can_delete_stories=self.DELETE_STORIES,
            can_post_messages=self.POST_MESSAGE,
            can_edit_messages=self.EDIT_MESSAGES,
            can_pin_messages=self.PIN_MESSAGE,
            can_manage_topics=self.MANAGE_TOPICS,
        )

    @property
    def active_bot_token(self) -> str:
        """Активный токен бота в зависимости от режима"""
        token = self.BOT_DEBUG_TOKEN if self.DEBUG else self.BOT_TOKEN
        if not token:
            raise ValueError("Активный токен бота отсутствует")
        return token

    @property
    def log_dir_absolute(self) -> Path:
        """Абсолютный путь к директории логов"""
        return self.LOG_DIR.absolute()


# Инициализация настроек
settings: Settings = Settings()


# Классы для обратной совместимости и удобства использования

class BotSettings:
    """Алиасы для настроек бота."""
    DEBUG: Final[bool] = settings.DEBUG
    OWNER: Final[str] = settings.OWNER
    BOT_TOKEN: Final[str] = settings.active_bot_token
    PARSE_MODE: Final[str] = settings.PARSE_MODE
    ENCOD: Final[str] = settings.ENCOD
    TIME_FORMAT: Final[str] = settings.TIME_FORMAT
    PREFIX: Final[str] = settings.PREFIX
    BOT_LANGUAGE: Final[str] = settings.BOT_LANGUAGE
    DISABLE_NOTIFICATION: Final[bool] = settings.DISABLE_NOTIFICATION
    PROTECT_CONTENT: Final[bool] = settings.PROTECT_CONTENT
    ALLOW_SENDING_WITHOUT_REPLY: Final[bool] = settings.ALLOW_SENDING_WITHOUT_REPLY
    LINK_PREVIEW_IS_DISABLED: Final[bool] = settings.LINK_PREVIEW_IS_DISABLED
    LINK_PREVIEW_PREFER_SMALL_MEDIA: Final[bool] = settings.LINK_PREVIEW_PREFER_SMALL_MEDIA
    LINK_PREVIEW_PREFER_LARGE_MEDIA: Final[bool] = settings.LINK_PREVIEW_PREFER_LARGE_MEDIA
    LINK_PREVIEW_SHOW_ABOVE_TEXT: Final[bool] = settings.LINK_PREVIEW_SHOW_ABOVE_TEXT
    SHOW_CAPTION_ABOVE_MEDIA: Final[bool] = settings.SHOW_CAPTION_ABOVE_MEDIA


class Permission:
    """Алиасы для разрешений."""
    BOT_EDIT: Final[bool] = settings.BOT_EDIT
    START_INFO_CONSOLE: Final[bool] = settings.START_INFO_CONSOLE
    START_INFO_TO_FILE: Final[bool] = settings.START_INFO_TO_FILE


class LogConfig:
    """Алиасы для конфигурации логов."""
    CONSOLE: Final[bool] = settings.LOG_CONSOLE
    FILE: Final[bool] = settings.LOG_FILE
    DIR: Final[Path] = settings.LOG_DIR
    FILE_INFO: Final[Path] = settings.LOG_FILE_INFO
    ROTATION: ClassVar[str] = '100 MB'
    RETENTION: ClassVar[str] = '7 days'


class Webhook:
    """Алиасы для вебхука."""
    WEBHOOK: Final[bool] = settings.WEBHOOK
    WEBHOOK_URL: Final[str] = settings.WEBHOOK_URL
    WEBAPP_HOST: Final[str] = settings.WEBAPP_HOST
    WEBAPP_PORT: Final[int] = settings.WEBAPP_PORT
    LOG_LEVEL: Final[str] = settings.LOG_LEVEL
    ACCES_LOG: Final[bool] = settings.ACCES_LOG



class APISettings:
    """Алиасы для API."""
    API_KEY: Final[Optional[str]] = settings.API_KEY
    WEB_API_KEY: Final[Optional[str]] = settings.WEB_API_KEY
    WEATHER_API_KEY: Final[Optional[str]] = settings.WEATHER_API_KEY


class UserIn:
    """Алиасы для пользовательских данных."""
    TG_API_UID: Final[int] = settings.TG_API_UID
    TG_API_HASH: Final[Optional[str]] = settings.TG_API_HASH


class ImportantID:
    """Алиасы для важных ID."""
    ADMIN_ID: Final[list[int]] = settings.ADMIN_ID
    MODERATOR_ID: Final[int] = settings.MODERATOR_ID
    IMPORTANT_ID: Final[int] = settings.IMPORTANT_ID
    IMPORTANT_GROUP_ID: Final[int] = settings.IMPORTANT_GROUP_ID
    IMPORTANT_CHANNEL_ID: Final[int] = settings.IMPORTANT_CHANNEL_ID
    SUPPORT_CHAT_ID: Final[int] = settings.SUPPORT_CHAT_ID


class BotEdit:
    """Алиасы для настроек редактирования бота."""
    ALLOW_PERMISSION: Final[bool] = settings.BOT_EDIT
    PROJECT_NAME: Final[str] = settings.PROJECT_NAME
    NAME: Final[str] = settings.BOT_NAME
    DESCRIPTION: Final[str] = settings.BOT_DESCRIPTION
    SHORT_DESCRIPTION: Final[str] = settings.BOT_SHORT_DESCRIPTION
    ANONYMOUS: Final[bool] = settings.ANONYMOUS
    MANAGE_CHAT: Final[bool] = settings.MANAGE_CHAT
    CHANGE_INFO: Final[bool] = settings.CHANGE_INFO
    PROMOTE_MEMBERS: Final[bool] = settings.PROMOTE_MEMBERS
    RESTRICT_MEMBERS: Final[bool] = settings.RESTRICT_MEMBERS
    POST_MESSAGE: Final[bool] = settings.POST_MESSAGE
    MANAGE_TOPICS: Final[bool] = settings.MANAGE_TOPICS
    INVITE_USER: Final[bool] = settings.INVITE_USER
    DELETE_MESSAGES: Final[bool] = settings.DELETE_MESSAGES
    MANAGE_VIDEO_CHATS: Final[bool] = settings.MANAGE_VIDEO_CHATS
    EDIT_MESSAGES: Final[bool] = settings.EDIT_MESSAGES
    PIN_MESSAGE: Final[bool] = settings.PIN_MESSAGE
    POST_STORIES: Final[bool] = settings.POST_STORIES
    EDIT_STORIES: Final[bool] = settings.EDIT_STORIES
    DELETE_STORIES: Final[bool] = settings.DELETE_STORIES
    RIGHTS: Final[ChatAdministratorRights] = settings.rights


class RpValue:
    """Переменные связанные с ролевым проектом."""
    RP_NAME: Final[str] = settings.RP_NAME
    INFO_URL: str = settings.INFO_URL
    FLUD_URL: str = settings.FLUD_URL
    RP_URL: str = settings.RP_URL
    LIFE_URL: str = settings.LIFE_URL
    RP_OWNER: str = settings.RP_OWNER
    ROLES: list[str] = settings.ROLES


class Project:
    POSTS_DIR: ClassVar[Path] = Path('posts')


class Lists:
   """Интересные списки фактов, цитат и анекдотов."""
   facts: list[str] = [
       "Python был создан Гвидо ван Россумом в 1991 году.",
       "Имена Python и Monty Python связаны — язык назван в честь шоу.",
       "Python — язык с динамической типизацией.",
       "В Python всё является объектом, даже функции и типы данных.",
       "Списки в Python — это изменяемые коллекции, в отличие от кортежей.",
       "Python поддерживает парадигмы ООП, функционального и императивного программирования.",
       "Zen of Python можно увидеть, набрав `import this` в интерпретаторе.",
   ]
   jokes: list[str] = [
       "1",
       "2",
       "3",
       "4",
   ]
   quotes: list[str] = [
       "5",
       "6",
       "7",
       "8",
   ]



# Экспорт совместимых компонентов
__all__ = (
    "BotSettings",
    "LogConfig",
    "Webhook",
    "APISettings",
    "UserIn",
    "ImportantID",
    "Permission",
    "BotEdit",
    "Project",
    "RpValue",
    'settings',
    'Lists',
)