import sys
import os
import asyncio
from asyncio import AbstractEventLoop
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Any, Generator

import pytest
import pytest_asyncio

from database import BotDatabase, RoleRegion

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


@pytest.fixture(scope="session")
def event_loop() -> Generator[AbstractEventLoop, Any, None]:
    """
    Создаёт event loop для асинхронных тестов.
    Scope: session, чтобы использовать один loop на всю сессию тестов.
    """
    policy = asyncio.get_event_loop_policy()
    loop: asyncio.AbstractEventLoop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db() -> AsyncGenerator[BotDatabase, None]:
    """
    Создаёт тестовую базу данных в памяти.
    Инициализирует тестовые роли.
    """
    db: BotDatabase = BotDatabase("sqlite+aiosqlite:///:memory:", echo=False)
    await db.init_db()

    # Инициализируем тестовые роли
    test_roles = [
        ("Альбедо", RoleRegion.MONDSTADT),
        ("Нахида", RoleRegion.SUMERU),
        ("Кафка", RoleRegion.HSR_STAR),
        ("Броння", RoleRegion.HSR_STAR),
        ("Чжун Ли", RoleRegion.LIYUE)
    ]
    await db.init_roles(test_roles)

    yield db
    await db.dispose()


@pytest_asyncio.fixture
async def test_session(test_db: BotDatabase) -> AsyncGenerator:
    """
    Создаёт тестовую сессию для работы с БД.
    Scope: function (по умолчанию).
    """
    async with test_db.session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(test_db: BotDatabase) -> int:
    """
    Создаёт тестового пользователя.
    Возвращает user_id.
    """
    user_id: int = 123456789
    await test_db.add_user(
        user_id=user_id,
        username="test_user",
        full_name="Test User"
    )
    return user_id


@pytest_asyncio.fixture
async def test_user_with_messages(test_db: BotDatabase, test_user: int) -> int:
    """
    Создаёт пользователя с тестовыми сообщениями за разные периоды.
    Сообщения распределены по месяцам, неделям и дням.
    """
    now: datetime = datetime.now(timezone.utc)

    # Даты сообщений: > месяца назад, в текущем месяце, в текущей неделе, сегодня
    test_dates: list[datetime] = [
        now - timedelta(days=40),
        now - timedelta(days=35),
        now - timedelta(days=20),
        now - timedelta(days=15),
        now - timedelta(days=8),
        now - timedelta(days=5),
        now - timedelta(days=2),
        now - timedelta(hours=12),
        now - timedelta(hours=1),
        now
    ]

    for i, date in enumerate(test_dates):
        await test_db.add_message(
            user_id=test_user,
            message_text=f"Тестовое сообщение {i + 1}",
            created_at=date
        )

    return test_user
