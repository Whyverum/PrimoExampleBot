from __future__ import annotations

import enum
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List, Protocol, runtime_checkable, Dict, Any, Union

from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum,
    func,
    select,
    and_,
    Integer, case,
)
from sqlalchemy import text as sql_text
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import Select

__all__: Tuple[str, ...] = (
    "UserStatus",
    "User",
    "UserMessage",
    "Role",
    "RoleRegion",
    "RoleMessage",
    "BotDatabase",
    "db"
)


# ======================================================
# База декларативных моделей (SQLAlchemy 2.0 style)
# ======================================================
class Base(DeclarativeBase):
    """Базовый класс декларативных моделей SQLAlchemy."""
    pass


# ======================================================
# Перечисления / константы
# ======================================================
class UserStatus(str, enum.Enum):
    """
    Статус пользователя в системе.

    Значения:
        - ACTIVE — обычный пользователь
        - ADMIN  — администратор
        - BANNED — заблокирован
    """
    ACTIVE = "active"
    ADMIN = "admin"
    BANNED = "banned"


class RoleRegion(str, enum.Enum):
    """
    Регионы персонажей в играх.

    Значения для Genshin Impact:
        - MONDSTADT - Мондштадт
        - LIYUE - Ли Юэ
        - INAZUMA - Инадзума
        - SUMERU - Сумеру
        - FONTAINE - Фонтейн
        - NATLAN - Натлан
        - SNEZHNAYA - Снежная
        - KHAENRIAH - Каэнри'ах
        - GENSHIN_OTHER - Другие (Genshin Impact)

    Значения для Honkai: Star Rail:
        - HSR_STAR - Звездный экспресс
        - HSR_GERTA - Космическая станция Герта
        - HSR_YARILO - Ярило-VI
        - HSR_LOFU - Лофу Сяньчжоу
        - HSR_PENACONY - Пенакония
        - HSR_AMPHOREUS - Амфореус
        - HSR_HUNTER - Охотники за Стеллар
        - HSR_KMM - КММ
        - HSR_EONS - Эоны
        - HSR_FIRE_MANSION - Вечногорящий особняк
        - HSR_LORDS - Лорды Опустошители
        - HSR_OTHER - Прочие (Honkai: Star Rail)
        - HSR_FATE - Фейт
    """
    # Genshin Impact регионы
    MONDSTADT = "Мондштадт"
    LIYUE = "Ли Юэ"
    INAZUMA = "Инадзума"
    SUMERU = "Сумеру"
    FONTAINE = "Фонтейн"
    NATLAN = "Натлан"
    SNEZHNAYA = "Снежная"
    KHAENRIAH = "Каэнри'ах"
    GENSHIN_OTHER = "Другие (Genshin Impact)"

    # Honkai: Star Rail регионы
    HSR_STAR = "Звездный экспресс"
    HSR_GERTA = "Космическая станция Герта"
    HSR_YARILO = "Ярило-VI"
    HSR_LOFU = "Лофу Сяньчжоу"
    HSR_PENACONY = "Пенакония"
    HSR_AMPHOREUS = "Амфореус"
    HSR_HUNTER = "Охотники за Стеллар"
    HSR_KMM = "КММ"
    HSR_EONS = "Эоны"
    HSR_FIRE_MANSION = "Вечногорящий особняк"
    HSR_LORDS = "Лорды Опустошители"
    HSR_OTHER = "Прочие (Honkai: Star Rail)"
    HSR_FATE = "Фейт"


# ======================================================
# Протоколы для минимальной типизации aiogram-сообщений
# (чтобы не тянуть aiogram как зависимость, но иметь строгие типы)
# ======================================================
@runtime_checkable
class SupportsUser(Protocol):
    """Протокол для объекта пользователя с обязательными полями."""
    id: int
    username: Optional[str]
    full_name: Optional[str]


@runtime_checkable
class SupportsAiogramMessage(Protocol):
    """Протокол для объекта сообщения с обязательными полями."""
    from_user: SupportsUser
    text: Optional[str]


@runtime_checkable
class SupportsAiogramBot(Protocol):
    """Протокол для объекта бота с методом редактирования сообщений."""

    async def edit_message_text(
            self,
            chat_id: Union[int, str],
            message_id: int,
            text: str,
            **kwargs: Any
    ) -> Any:
        ...


# ======================================================
# Модели
# ======================================================
class User(Base):
    """
    Модель пользователя Telegram.

    Таблица:
        users

    Атрибуты:
        id (int) - Telegram ID пользователя (PK)
        username (Optional[str]) - Никнейм (@username)
        full_name (Optional[str]) - Полное имя
        status (UserStatus) - Статус: active/admin/banned
        created_at (datetime) - Дата создания записи (tz-aware)
        updated_at (datetime) - Дата последнего обновления (tz-aware)
        messages (List[UserMessage]) - Связанные сообщения
        roles (List[Role]) - Роли, которые занимает пользователь

    Индексы:
        - ix_users_status
        - ix_users_username

    Пример:
        >> user = User(id=123, username="test", full_name="Test User")
    """

    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Для SQLite используем строковый Enum (native_enum=False)
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, native_enum=False),
        nullable=False,
        default=UserStatus.ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    messages: Mapped[List["UserMessage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    roles: Mapped[List["Role"]] = relationship(
        back_populates="occupied_by_user",
        passive_deletes=True,
    )


class UserMessage(Base):
    """
    Сообщение пользователя.

    Таблица:
        user_messages

    Атрибуты:
        id (int) - ID сообщения (PK)
        user_id (int) - FK -> users.id
        message_text (str) - Текст сообщения
        created_at (datetime) - Метка времени (UTC, tz-aware)

    Индексы:
        - ix_user_messages_user_id_created_at (user_id, created_at)

    Пример:
        >> message = UserMessage(user_id=123, message_text="Hello")
    """

    __tablename__: str = "user_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="messages")


class Role(Base):
    """
    Роль (персонаж).

    Таблица:
        roles

    Атрибуты:
        id (int) - ID роли (PK)
        name (str) - Название роли (уникально)
        region (RoleRegion) - Регион персонажа
        occupied_by (Optional[int]) - Пользователь, который занимает роль (FK -> users.id)
        occupied_by_user (Optional[User]) - Обратная связь на пользователя

    Ограничения:
        - Уникальность name

    Пример:
        >> role = Role(name="Альбедо", region=RoleRegion.MONDSTADT)
    """

    __tablename__: str = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    region: Mapped[RoleRegion] = mapped_column(
        SAEnum(RoleRegion, native_enum=False),
        nullable=False,
        default=RoleRegion.GENSHIN_OTHER,
    )
    occupied_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )
    occupied_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="roles"
    )


class RoleMessage(Base):
    """
    Модель для хранения информации о сообщениях с списками ролей.

    Таблица:
        role_messages

    Атрибуты:
        id (int) - ID записи
        game_type (str) - тип игры ('genshin' или 'hsr')
        channel_id (int) - ID канала
        message_id (int) - ID сообщения
        message_text (str) - исходный текст сообщения

    Пример:
        >> role_msg = RoleMessage(
        >>     game_type="genshin",
        >>     channel_id=-100123456,
        >>     message_id=123,
        >>     message_text="Список персонажей"
        >> )
    """
    __tablename__: str = "role_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_type: Mapped[str] = mapped_column(String, nullable=False)  # 'genshin' или 'hsr'
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)


# ======================================================
# Утилиты для расчёта периодов (день/неделя/месяц)
# ======================================================
def _start_of_day(dt: datetime) -> datetime:
    """
    Начало дня для tz-aware datetime.

    Args:
        dt: текущая дата/время (tz-aware)

    Returns:
        datetime: 00:00:00 того же дня.

    Пример:
        >> now = datetime.now(timezone.utc)
        >> start = _start_of_day(now)
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_week_monday(dt: datetime) -> datetime:
    """
    Начало недели (понедельник 00:00:00) для tz-aware datetime.

    Args:
        dt: текущая дата/время (tz-aware)

    Returns:
        datetime: понедельник 00:00:00 текущей недели.

    Пример:
        >> now = datetime.now(timezone.utc)
        >> start = _start_of_week_monday(now)
    """
    monday: datetime = dt - timedelta(days=dt.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_month(dt: datetime) -> datetime:
    """
    Начало месяца (первое число 00:00:00) для tz-aware datetime.

    Args:
        dt: текущая дата/время (tz-aware)

    Returns:
        datetime: первое число 00:00:00 текущего месяца.

    Пример:
        >> now = datetime.now(timezone.utc)
        >> start = _start_of_month(now)
    """
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


# ======================================================
# Класс управления базой данных
# ======================================================
class BotDatabase:
    """
    Асинхронный менеджер базы данных для Telegram-бота (SQLite + SQLAlchemy 2.x).

    Возможности:
        - Автосоздание базы и всех таблиц.
        - Учёт пользователей (регистрация, бан, разбан, список ID).
        - Учёт сообщений (логирование, статистика за день/неделю/месяц/всё время).
        - Система ролей (создание, назначение, освобождение, статус).
        - Управление сообщениями с ролями в Telegram.

    Замечания:
        - Все временные метки сохраняются в UTC (tz-aware).
        - Неделя считается с понедельника по воскресенье.

    Пример:
        >> db = BotDatabase()                               # doctest: +SKIP
        >> await db.init_db()                               # doctest: +SKIP
        >> await db.add_user(1001, "user1", "User One")     # doctest: +SKIP
        >> await db.add_message(1001, "Привет")             # doctest: +SKIP
        >> await db.init_roles([                            # doctest: +SKIP
        >>     ("Альбедо", RoleRegion.MONDSTADT),           # doctest: +SKIP
        >>     ("Чжун Ли", RoleRegion.LIYUE)                # doctest: +SKIP
        >> ])                                               # doctest: +SKIP
        >> await db.assign_role("Альбедо", 1001)            # doctest: +SKIP
        >> ids = await db.get_user_ids()                    # doctest: +SKIP
        >> stats = await db.get_message_stats(1001)         # doctest: +SKIP
    """

    DEFAULT_DB_URL: str = "sqlite+aiosqlite:///./bot.db"

    def __init__(self, db_url: Optional[str] = None, echo: bool = False) -> None:
        """
        Инициализация менеджера БД.

        Args:
            db_url: строка подключения к базе (по умолчанию создаётся ./bot.db).
            echo:   логирование SQL (для отладки).

        Raises:
            ValueError: если db_url пустая строка.

        Пример:
            >> db = BotDatabase()  # Создаст базу в файле ./bot.db
            >> db = BotDatabase("sqlite+aiosqlite:///./test.db", echo=True)  # Создаст test.db с логированием SQL
        """
        if db_url is not None and not db_url.strip():
            raise ValueError("db_url не может быть пустой строкой")

        url: str = db_url or self.DEFAULT_DB_URL
        self.engine: AsyncEngine = create_async_engine(url, echo=echo, future=True)
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine, expire_on_commit=False, class_=AsyncSession
        )

    # ----------------------- Инициализация схемы -----------------------
    async def init_db(self) -> None:
        """
        Создаёт все таблицы в базе данных.

        Пример:
            >> await db.init_db()
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        """
        Корректно закрывает соединения с БД.

        Пример:
            >> await db.dispose()
        """
        await self.engine.dispose()

    # ----------------------- Пользователи -----------------------
    async def add_user(
            self,
            user_id: int,
            username: Optional[str] = None,
            full_name: Optional[str] = None,
            is_admin: bool = False,
    ) -> None:
        """
        Регистрирует пользователя (idempotent): если запись уже есть — ничего не делает.

        Args:
            user_id: Telegram ID пользователя.
            username: никнейм (@username).
            full_name: полное имя.
            is_admin: установить статус ADMIN при создании.

        Пример:
            >> await db.add_user(42, username="neo", full_name="Thomas Anderson", is_admin=True)
        """
        async with self.session_factory() as session:
            existing: Optional[User] = await session.get(User, user_id)
            if existing is not None:
                return

            status: UserStatus = UserStatus.ADMIN if is_admin else UserStatus.ACTIVE
            new_user: User = User(
                id=user_id,
                username=username,
                full_name=full_name,
                status=status,
            )
            session.add(new_user)
            await session.commit()

    async def ensure_user_from_message(self, message: SupportsAiogramMessage) -> None:
        """
        Гарантирует наличие пользователя в БД на основе aiogram-сообщения.

        Args:
            message: объект, совместимый с aiogram.types.Message (имеет from_user с полями id/username/full_name).

        Пример:
            >> # в хендлере aiogram:
            >> await db.ensure_user_from_message(message)
        """
        # Строгая проверка протокола:
        if not isinstance(message, SupportsAiogramMessage):
            raise TypeError("message не соответствует протоколу SupportsAiogramMessage")

        from_user: SupportsUser = message.from_user
        if not isinstance(from_user, SupportsUser):
            raise TypeError("message.from_user не соответствует протоколу SupportsUser")

        await self.add_user(
            user_id=from_user.id,
            username=from_user.username,
            full_name=from_user.full_name,
        )

    async def set_admin(self, user_id: int, make_admin: bool = True) -> None:
        """
        Повышает/понижает пользователя до/с администратора.

        Args:
            user_id: Telegram ID.
            make_admin: True — сделать админом, False — вернуть в ACTIVE.

        Пример:
            >> await db.set_admin(42, make_admin=True)   # Сделать админом
            >> await db.set_admin(42, make_admin=False)  # Убрать админа
        """
        async with self.session_factory() as session:
            user: Optional[User] = await session.get(User, user_id)
            if user is None:
                return
            user.status = UserStatus.ADMIN if make_admin else UserStatus.ACTIVE
            await session.commit()  # Убедитесь, что этот вызов есть!

    async def ban_user(self, user_id: int) -> None:
        """
        Банит пользователя (status=BANNED).

        Args:
            user_id: Telegram ID.

        Пример:
            >> await db.ban_user(1001)
        """
        async with self.session_factory() as session:
            user: Optional[User] = await session.get(User, user_id)
            if user is None:
                return
            user.status = UserStatus.BANNED
            await session.commit()

    async def unban_user(self, user_id: int) -> None:
        """
        Разбанивает пользователя (возвращает в ACTIVE, если был BANNED).

        Args:
            user_id: Telegram ID.

        Пример:
            >> await db.unban_user(1001)
        """
        async with self.session_factory() as session:
            user: Optional[User] = await session.get(User, user_id)
            if user is None:
                return
            if user.status == UserStatus.BANNED:
                user.status = UserStatus.ACTIVE
                await session.commit()

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Возвращает пользователя по ID.

        Args:
            user_id: Telegram ID.

        Returns:
            Optional[User]: объект или None.

        Пример:
            >> user = await db.get_user(1001)
            >> if user:
            >>     print(user.username)
        """
        async with self.session_factory() as session:
            return await session.get(User, user_id)

    async def get_all_users(self, include_banned: bool = False) -> List[User]:
        """
        Возвращает список пользователей.

        Args:
            include_banned: включать ли забаненных (по умолчанию False).

        Returns:
            List[User]: список пользователей.

        Пример:
            >> users = await db.get_all_users()
            >> for user in users:
            >>     print(f"{user.id}: {user.username}")
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[User]] = select(User)
            if not include_banned:
                stmt = stmt.where(User.status != UserStatus.BANNED)
            res: Result[Tuple[User]] = await session.execute(stmt)
            return list(res.scalars().all())

    async def get_user_ids(
            self,
            only_active: bool = True,
            include_admins: bool = True,
            order_asc: bool = True,
    ) -> List[int]:
        """
        Возвращает список ID пользователей (для рассылок и т.п.).

        Args:
            only_active: Исключать ли забаненных (True по умолчанию).
            include_admins: Включать ли администраторов.
            order_asc: Сортировать по возрастанию (иначе по убыванию).

        Returns:
            List[int]: список Telegram ID.

        Пример:
            >> active_user_ids = await db.get_user_ids(only_active=True, include_admins=False)
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[int]] = select(User.id)
            if only_active:
                stmt = stmt.where(User.status != UserStatus.BANNED)
            if not include_admins:
                stmt = stmt.where(User.status != UserStatus.ADMIN)
            stmt = stmt.order_by(User.id.asc() if order_asc else User.id.desc())

            res: Result[Tuple[int]] = await session.execute(stmt)
            ids: List[int] = list(res.scalars().all())
            return ids

    # ----------------------- Сообщения / статистика -----------------------
    async def add_message(
            self,
            user_id: int,
            message_text: str,
            created_at: Optional[datetime] = None,
    ) -> None:
        async with self.session_factory() as session:
            # Сначала пытаемся найти пользователя
            user: Optional[User] = await session.get(User, user_id)

            # Если пользователя нет, создаем его
            if user is None:
                user = User(id=user_id, status=UserStatus.ACTIVE)
                session.add(user)
                await session.flush()

            # Используем переданную дату или текущее время
            if created_at is not None:
                # Убедимся, что дата имеет временную зону
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                ts = created_at
            else:
                ts = datetime.now(timezone.utc)

            record: UserMessage = UserMessage(user_id=user_id, message_text=message_text, created_at=ts)
            session.add(record)
            await session.commit()

    async def check_connection(self) -> bool:
        """Проверяет соединение с базой данных"""
        try:
            async with self.session_factory() as session:
                await session.execute(sql_text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            return False

    async def add_message_from_message(self, message: SupportsAiogramMessage) -> None:
        """
        Логирует сообщение напрямую из aiogram (минимальный контракт через Protocol).

        Args:
            message: объект, совместимый с aiogram.types.Message.

        Пример:
            >> await db.add_message_from_message(message)
        """
        if not isinstance(message, SupportsAiogramMessage):
            raise TypeError("message не соответствует протоколу SupportsAiogramMessage")
        from_user: SupportsUser = message.from_user
        if not isinstance(from_user, SupportsUser):
            raise TypeError("message.from_user не соответствует протоколу SupportsUser")

        await self.add_message(
            user_id=from_user.id,
            message_text=message.text or "",
        )

    async def get_message_stats(self, user_id: int) -> Tuple[int, int, int, int]:
        """
        Возвращает статистику сообщений пользователя:
        (за текущий день, за текущую неделю [Пн-Вс], за текущий месяц, за всё время).

        Все границы считаются по UTC и округляются к началу периода.

        Args:
            user_id: Telegram ID.

        Returns:
            Tuple[int, int, int, int]: (day, week, month, total)

        Пример:
            >> day, week, month, total = await db.get_message_stats(1001)
            >> print(f"За день: {day}, за неделю: {week}, за месяц: {month}, всего: {total}")
        """
        async with self.session_factory() as session:
            now: datetime = datetime.now(timezone.utc)
            day_start: datetime = _start_of_day(now)
            week_start: datetime = _start_of_week_monday(now)
            month_start: datetime = _start_of_month(now)
            epoch_start: datetime = datetime(1970, 1, 1, tzinfo=timezone.utc)

            async def _count_from(since: datetime) -> int:
                stmt: Select[Tuple[int]] = select(func.count()).where(
                    and_(UserMessage.user_id == user_id, UserMessage.created_at >= since)
                )
                res: Result[Tuple[int]] = await session.execute(stmt)
                return int(res.scalar() or 0)

            day_count: int = await _count_from(day_start)
            week_count: int = await _count_from(week_start)
            month_count: int = await _count_from(month_start)
            total_count: int = await _count_from(epoch_start)

            return day_count, week_count, month_count, total_count

    # ----------------------- Роли -----------------------
    async def init_roles(self, roles: List[Tuple[str, RoleRegion]]) -> None:
        """
        Создаёт роли персонажей. Если таблицы нет — создаёт таблицы.

        Args:
            roles: список кортежей (имя_роли, регион)

        Пример:
            >> roles = [
            >>     ("Альбедо", RoleRegion.MONDSTADT),
            >>     ("Чжун Ли", RoleRegion.LIYUE),
            >>     ("Вельт", RoleRegion.HSR_STAR)
            >> ]
            >> await db.init_roles(roles)
        """
        # создаём таблицы перед вставкой ролей
        await self.init_db()

        async with self.session_factory() as session:
            for name, region in roles:
                stmt = select(Role).where(Role.name == name)
                res = await session.execute(stmt)
                role = res.scalar_one_or_none()
                if not role:
                    session.add(Role(name=name, region=region))
            await session.commit()

    async def assign_role(self, role_name: str, user_id: int, bot: Optional[SupportsAiogramBot] = None) -> bool:
        """
        Назначает пользователя на роль, если она свободна.

        Args:
            role_name: название роли (уникальное).
            user_id: Telegram ID пользователя.
            bot: экземпляр бота для обновления сообщения (опционально).

        Returns:
            bool: True — если назначение выполнено, False — если такой роли нет или роль уже занята.

        Пример:
            >> success = await db.assign_role("Альбедо", 1001, bot)
            >> if success:
            >>     print("Роль назначена")
        """
        async with self.session_factory() as session:
            role_stmt: Select[Tuple[Role]] = select(Role).where(Role.name == role_name)
            role_res: Result[Tuple[Role]] = await session.execute(role_stmt)
            role: Optional[Role] = role_res.scalar_one_or_none()
            if role is None or role.occupied_by is not None:
                return False

            user: Optional[User] = await session.get(User, user_id)
            if user is None or user.status == UserStatus.BANNED:
                return False

            role.occupied_by = user_id
            await session.commit()

            # Обновляем сообщение с ролями если передан бот
            if bot:
                # Определяем игру по региону
                game_type: str = "hsr" if role.region.name.startswith("HSR_") else "genshin"
                await self.update_role_message(game_type, bot)

            return True

    async def release_role(self, role_name: str, bot: Optional[SupportsAiogramBot] = None) -> bool:
        """
        Освобождает роль (устанавливает occupied_by = NULL).

        Args:
            role_name: название роли.
            bot: экземпляр бота для обновления сообщения (опционально).

        Returns:
            bool: True если роль была освобождена, False если роль не найдена или уже свободна.

        Пример:
            >> success = await db.release_role("Альбедо", bot)
            >> if success:
            >>     print("Роль освобождена")
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[Role]] = select(Role).where(Role.name == role_name)
            res: Result[Tuple[Role]] = await session.execute(stmt)
            role: Optional[Role] = res.scalar_one_or_none()

            if role is None or role.occupied_by is None:
                return False

            role.occupied_by = None
            await session.commit()

            # Обновляем сообщение с ролями если передан бот
            if bot:
                # Определяем игру по региону
                game_type: str = "hsr" if role.region.name.startswith("HSR_") else "genshin"
                await self.update_role_message(game_type, bot)

            return True

    async def get_role_status(self) -> List[Tuple[str, Optional[int]]]:
        """
        Возвращает текущий статус всех ролей.

        Returns:
            List[Tuple[str, Optional[int]]]: пары (role_name, user_id | None)

        Пример:
            >> roles = await db.get_role_status()
            >> for name, user_id in roles:
            >>     status = "занята" if user_id else "свободна"
            >>     print(f"{name}: {status}")
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[Role]] = select(Role).order_by(Role.name.asc())
            res: Result[Tuple[Role]] = await session.execute(stmt)
            roles: List[Role] = list(res.scalars().all())
            return [(r.name, r.occupied_by) for r in roles]

    async def get_roles_by_user(self, user_id: int) -> List[str]:
        """
        Возвращает список имён ролей, занятых указанным пользователем.

        Args:
            user_id: Telegram ID.

        Returns:
            List[str]: имена ролей.

        Пример:
            >> roles = await db.get_roles_by_user(1001)
            >> print(f"Пользователь занимает роли: {', '.join(roles)}")
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[str]] = select(Role.name).where(Role.occupied_by == user_id)
            res: Result[Tuple[str]] = await session.execute(stmt)
            names: List[str] = list(res.scalars().all())
            return names

    async def release_roles_by_user(self, user_id: int, bot: Optional[SupportsAiogramBot] = None) -> int:
        """
        Освобождает все роли, занятые указанным пользователем.

        Args:
            user_id: Telegram ID.
            bot: экземпляр бота для обновления сообщения (опционально).

        Returns:
            int: количество освобождённых ролей.

        Пример:
            >> count = await db.release_roles_by_user(1001, bot)
            >> print(f"Освобождено {count} ролей")
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[Role]] = select(Role).where(Role.occupied_by == user_id)
            res: Result[Tuple[Role]] = await session.execute(stmt)
            roles: List[Role] = list(res.scalars().all())

            for r in roles:
                r.occupied_by = None

            if roles:
                await session.commit()

                # Обновляем сообщения с ролями если передан бот
                if bot:
                    # Обновляем оба типа сообщений, так как пользователь мог занимать роли в обеих играх
                    await self.update_role_message("genshin", bot)
                    await self.update_role_message("hsr", bot)

            return len(roles)

    async def get_available_roles(self, region: Optional[RoleRegion] = None) -> List[Role]:
        """
        Возвращает список свободных ролей.

        Args:
            region: фильтр по региону (опционально).

        Returns:
            List[Role]: список свободных ролей.

        Пример:
            >> free_roles = await db.get_available_roles(RoleRegion.MONDSTADT)
            >> for role in free_roles:
            >>     print(role.name)
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[Role]] = select(Role).where(Role.occupied_by.is_(None))
            if region:
                stmt = stmt.where(Role.region == region)
            stmt = stmt.order_by(Role.name.asc())

            res: Result[Tuple[Role]] = await session.execute(stmt)
            return list(res.scalars().all())

    async def get_occupied_roles(self, region: Optional[RoleRegion] = None) -> List[Role]:
        """
        Возвращает список занятых ролей.

        Args:
            region: фильтр по региону (опционально).

        Returns:
            List[Role]: список занятых ролей.

        Пример:
            >> occupied_roles = await db.get_occupied_roles(RoleRegion.MONDSTADT)
            >> for role in occupied_roles:
            >>     print(f"{role.name} занята пользователем {role.occupied_by}")
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[Role]] = select(Role).where(Role.occupied_by.is_not(None))
            if region:
                stmt = stmt.where(Role.region == region)
            stmt = stmt.order_by(Role.name.asc())

            res: Result[Tuple[Role]] = await session.execute(stmt)
            return list(res.scalars().all())

    async def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """
        Возвращает роль по имени.

        Args:
            role_name: название роли.

        Returns:
            Optional[Role]: объект роли или None если не найдена.

        Пример:
            >> role = await db.get_role_by_name("Альбедо")
            >> if role:
            >>     print(f"Регион: {role.region}, занята: {role.occupied_by is not None}")
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[Role]] = select(Role).where(Role.name == role_name)
            res: Result[Tuple[Role]] = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def get_roles_by_region(self, region: RoleRegion) -> List[Role]:
        """
        Возвращает все роли в указанном регионе.

        Args:
            region: регион для фильтрации.

        Returns:
            List[Role]: список ролей в регионе.

        Пример:
            >> mondstadt_roles = await db.get_roles_by_region(RoleRegion.MONDSTADT)
            >> for role in mondstadt_roles:
            >>     status = "занята" if role.occupied_by else "свободна"
            >>     print(f"{role.name}: {status}")
        """
        async with self.session_factory() as session:
            stmt: Select[Tuple[Role]] = select(Role).where(Role.region == region).order_by(Role.name.asc())
            res: Result[Tuple[Role]] = await session.execute(stmt)
            return list(res.scalars().all())

    async def get_region_stats(self) -> Dict[RoleRegion, Dict[str, int]]:
        """
        Возвращает статистику по регионам: количество свободных и занятых ролей.
        """
        async with self.session_factory() as session:
            # Используем агрегатные функции для подсчета статистики
            stmt = select(
                Role.region,
                func.count().label("total"),
                func.sum(case((Role.occupied_by.is_not(None), 1), else_=0)).label("occupied"),
                func.sum(case((Role.occupied_by.is_(None), 1), else_=0)).label("free")
            ).group_by(Role.region).order_by(Role.region.asc())

            res = await session.execute(stmt)
            results = res.all()

            stats: Dict[RoleRegion, Dict[str, int]] = {}
            for region, total, occupied, free in results:
                stats[region] = {
                    "total": total,
                    "occupied": occupied,
                    "free": free
                }

            return stats

    # ----------------------- Управление сообщениями с ролями -----------------------
    async def save_role_message(
            self,
            game_type: str,
            channel_id: int,
            message_id: int,
            message_text: str
    ) -> None:
        """
        Сохраняет информацию о сообщении со списком ролей.

        Args:
            game_type: 'genshin' или 'hsr'
            channel_id: ID канала
            message_id: ID сообщения
            message_text: исходный текст сообщения

        Пример:
            >> await db.save_role_message(
            >>     game_type="genshin",
            >>     channel_id=-100123456,
            >>     message_id=123,
            >>     message_text="Список персонажей Genshin Impact"
            >> )
        """
        async with self.session_factory() as session:
            # Удаляем старую запись если есть
            stmt = select(RoleMessage).where(RoleMessage.game_type == game_type)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                await session.delete(existing)

            # Создаем новую запись
            new_message = RoleMessage(
                game_type=game_type,
                channel_id=channel_id,
                message_id=message_id,
                message_text=message_text
            )
            session.add(new_message)
            await session.commit()

    async def update_role_message(self, game_type: str, bot: SupportsAiogramBot) -> bool:
        """
        Обновляет сообщение со списком ролей в Telegram.

        Args:
            game_type: 'genshin' или 'hsr'
            bot: экземпляр aiogram Bot

        Returns:
            bool: True если сообщение обновлено, False если сообщение не найдено

        Пример:
            >> success = await db.update_role_message("genshin", bot)
            >> if success:
            >>     print("Сообщение обновлено")
        """
        async with self.session_factory() as session:
            # Получаем информацию о сообщении
            stmt = select(RoleMessage).where(RoleMessage.game_type == game_type)
            result = await session.execute(stmt)
            role_message = result.scalar_one_or_none()

            if not role_message:
                return False

            # Получаем статус всех ролей
            roles_status = await self.get_role_status()
            role_status_dict = {name: user_id for name, user_id in roles_status}

            # Обновляем текст сообщения
            lines = role_message.message_text.split('\n')
            updated_lines = []

            for line in lines:
                # Пропускаем заголовки и пустые строки
                if not line.strip() or any(marker in line for marker in ['ᵎ', 'СПИСОК', 'Если персонажа']):
                    updated_lines.append(line)
                    continue

                # Проверяем, есть ли роль в этом сообщении
                role_name = line.strip().replace('✅', '').replace('🕒', '').strip()

                if role_name in role_status_dict:
                    if role_status_dict[role_name] is not None:
                        # Роль занята - добавляем галочку
                        updated_line = f"{role_name} ✅"
                    else:
                        # Роль свободна - оставляем как есть
                        updated_line = role_name
                else:
                    # Роль не найдена в базе - оставляем как есть
                    updated_line = line

                updated_lines.append(updated_line)

            updated_text = '\n'.join(updated_lines)

            # Обновляем сообщение в Telegram
            try:
                await bot.edit_message_text(
                    chat_id=role_message.channel_id,
                    message_id=role_message.message_id,
                    text=updated_text
                )
                return True
            except Exception as e:
                print(f"Ошибка при обновлении сообщения: {e}")
                return False

    async def init_default_roles(self) -> None:
        """
        Инициализирует стандартные списки ролей для Genshin Impact и Honkai: Star Rail.

        Пример:
            >> await db.init_default_roles()
        """
        # Роли для Genshin Impact с регионами
        from configs import all_roles
        await self.init_roles(all_roles)


# Глобальный экземпляр базы данных
db: BotDatabase = BotDatabase()
