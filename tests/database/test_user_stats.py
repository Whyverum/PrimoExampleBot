from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from database import User, UserMessage, BotDatabase


@pytest.mark.asyncio
class TestUserStatistics:
    """Тесты для статистики пользователей с полной строгой типизацией"""

    async def test_add_user(self, test_db: BotDatabase, test_session: AsyncSession) -> None:
        """
        Тест добавления пользователя.
        Проверяет, что пользователь создаётся с правильными данными и статусом 'active'.
        """
        user_id: int = 111222333

        await test_db.add_user(
            user_id=user_id,
            username="new_user",
            full_name="New User"
        )

        user: User | None = await test_session.get(User, user_id)
        assert user is not None
        assert user.username == "new_user"
        assert user.status.value == "active"

    async def test_add_message_creates_user(
        self, test_db: BotDatabase, test_session: AsyncSession
    ) -> None:
        """
        Тест, что добавление сообщения создаёт пользователя, если его нет.
        Проверяет, что пользователь и сообщение корректно создаются.
        """
        user_id: int = 111222333

        await test_db.add_message(
            user_id=user_id,
            message_text="Тестовое сообщение"
        )

        user: User | None = await test_session.get(User, user_id)
        assert user is not None
        assert user.status.value == "active"

        stmt = select(UserMessage).where(UserMessage.user_id == user_id)
        result = await test_session.execute(stmt)
        messages: Sequence[UserMessage] = result.scalars().all()

        assert len(messages) == 1
        assert messages[0].message_text == "Тестовое сообщение"

    async def test_message_stats_calculation(
        self, test_db: BotDatabase, test_user_with_messages: int
    ) -> None:
        """
        Тест расчёта статистики сообщений пользователя.
        Проверяет корректность статистики по дням, неделям, месяцам и общему количеству сообщений.
        """
        user_id: int = test_user_with_messages

        # Получаем статистику
        day: int
        week: int
        month: int
        total: int
        day, week, month, total = await test_db.get_message_stats(user_id)

        assert total >= 10, f"Ожидается минимум 10 сообщений, получено {total}"
        assert day >= 0
        assert week >= 0
        assert month >= 0
        assert total >= 0
        assert day <= week <= month <= total

    async def test_message_stats_with_dates(
        self, test_db: BotDatabase, test_user: int
    ) -> None:
        """
        Тест статистики с конкретными известными датами сообщений.
        Проверяет подсчёт сообщений за день, неделю, месяц и общее количество.
        """
        user_id: int = test_user
        now: datetime = datetime.now(timezone.utc)

        # Очищаем старые сообщения
        async with test_db.session_factory() as session:
            stmt = select(UserMessage).where(UserMessage.user_id == user_id)
            result = await session.execute(stmt)
            old_messages: Sequence[UserMessage] = result.scalars().all()
            for msg in old_messages:
                await session.delete(msg)
            await session.commit()

        # Создаём сообщения с фиксированными датами
        test_messages: list[tuple[datetime, str]] = [
            (now - timedelta(days=45), "45 дней назад"),
            (now - timedelta(days=30), "30 дней назад"),
            (now - timedelta(days=15), "15 дней назад"),
            (now - timedelta(days=7), "7 дней назад"),
            (now - timedelta(days=3), "3 дня назад"),
            (now - timedelta(hours=6), "6 часов назад"),
            (now, "сейчас")
        ]

        for date, text in test_messages:
            await test_db.add_message(user_id, text, date)

        day: int
        week: int
        month: int
        total: int
        day, week, month, total = await test_db.get_message_stats(user_id)

        assert total == 7, f"Ожидалось 7 сообщений, получено {total}"

        day_start: datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
        expected_day: int = sum(1 for date, _ in test_messages if date >= day_start)
        assert day == expected_day, f"За день: ожидалось {expected_day}, получено {day}"

        monday: datetime = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        expected_week: int = sum(1 for date, _ in test_messages if date >= monday)
        assert week == expected_week, f"За неделю: ожидалось {expected_week}, получено {week}"

        month_start: datetime = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        expected_month: int = sum(1 for date, _ in test_messages if date >= month_start)
        assert month == expected_month, f"За месяц: ожидалось {expected_month}, получено {month}"

    async def test_empty_user_stats(self, test_db: BotDatabase) -> None:
        """
        Тест статистики для пользователя без сообщений.
        Все значения должны быть равны нулю.
        """
        user_id: int = 0o00111222
        await test_db.add_user(user_id, "empty_user", "Empty User")

        day: int
        week: int
        month: int
        total: int
        day, week, month, total = await test_db.get_message_stats(user_id)

        assert day == 0
        assert week == 0
        assert month == 0
        assert total == 0

    async def test_user_management(self, test_db: BotDatabase) -> None:
        """
        Тест управления пользователями.
        Проверяет добавление, назначение админа, бан/разбан и возврат статуса пользователя.
        """
        user_id: int = 555666777

        # Добавление пользователя
        await test_db.add_user(user_id, "managed_user", "Managed User")

        async with test_db.session_factory() as session:
            user: User | None = await session.get(User, user_id)
            assert user is not None
            assert user.status.value == "active"

        # Назначение админом
        await test_db.set_admin(user_id, True)
        async with test_db.session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            assert user.status.value == "admin"

        # Бан пользователя
        await test_db.ban_user(user_id)
        async with test_db.session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            assert user.status.value == "banned"

        # Разбан
        await test_db.unban_user(user_id)
        async with test_db.session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            assert user.status.value == "active"

        # Снятие админки
        await test_db.set_admin(user_id, False)
        async with test_db.session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            assert user.status.value == "active"
