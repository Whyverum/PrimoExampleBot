from datetime import datetime, timezone
from typing import List

import pytest
from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserMessage, BotDatabase


@pytest.mark.asyncio
class TestMessageManagement:
    """Тесты для управления сообщениями с полной строгой типизацией"""

    async def test_message_creation(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест создания сообщения.
        Проверяет, что сообщение успешно сохраняется в базе и содержит правильные данные.
        """
        user_id: int = test_user
        test_text: str = "Тестовое сообщение для проверки"

        await test_db.add_message(user_id, test_text)

        stmt = select(UserMessage).where(UserMessage.user_id == user_id)
        result = await test_session.execute(stmt)
        messages: Sequence[UserMessage] = result.scalars().all()

        assert len(messages) == 1
        assert messages[0].message_text == test_text
        assert messages[0].user_id == user_id
        assert messages[0].created_at is not None

    async def test_message_with_custom_date(
        self, test_db: BotDatabase, test_session: AsyncSession
    ) -> None:
        """
        Тест добавления сообщения с кастомной датой.
        Проверяет, что дата создания сохраняется корректно.
        """
        user_id: int = 999888777
        custom_date: datetime = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)

        await test_db.add_user(user_id, "test_user", "Test User")
        await test_db.add_message(
            user_id=user_id,
            message_text="Сообщение с кастомной датой",
            created_at=custom_date
        )

        stmt = select(UserMessage).where(UserMessage.user_id == user_id)
        result = await test_session.execute(stmt)
        messages: Sequence[UserMessage] = result.scalars().all()

        assert len(messages) == 1
        db_date: datetime = messages[0].created_at
        if db_date.tzinfo is not None:
            db_date = db_date.replace(tzinfo=None)
        expected_date: datetime = custom_date.replace(tzinfo=None)
        assert db_date == expected_date

    async def test_multiple_messages(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест добавления нескольких сообщений.
        Проверяет, что все сообщения корректно сохраняются в базе.
        """
        user_id: int = test_user

        # Удаляем старые сообщения
        async with test_db.session_factory() as session:
            stmt = select(UserMessage).where(UserMessage.user_id == user_id)
            result = await session.execute(stmt)
            old_messages: Sequence[UserMessage] = result.scalars().all()
            for msg in old_messages:
                await session.delete(msg)
            await session.commit()

        # Добавляем несколько сообщений
        for i in range(5):
            await test_db.add_message(
                user_id=user_id,
                message_text=f"Сообщение {i + 1}"
            )

        stmt = select(UserMessage).where(UserMessage.user_id == user_id)
        result = await test_session.execute(stmt)
        messages: Sequence[UserMessage] = result.scalars().all()

        assert len(messages) == 5

    async def test_message_ordering(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест проверки порядка сообщений по дате создания.
        Сообщения должны возвращаться в порядке возрастания даты.
        """
        user_id: int = test_user

        # Очищаем старые сообщения
        async with test_db.session_factory() as session:
            stmt = select(UserMessage).where(UserMessage.user_id == user_id)
            result = await session.execute(stmt)
            old_messages: Sequence[UserMessage] = result.scalars().all()
            for msg in old_messages:
                await session.delete(msg)
            await session.commit()

        texts: List[str] = ["Сообщение 1", "Сообщение 2", "Сообщение 3"]

        for text in texts:
            await test_db.add_message(user_id, text)

        stmt = select(UserMessage).where(UserMessage.user_id == user_id).order_by(UserMessage.created_at.asc())
        result = await test_session.execute(stmt)
        messages: Sequence[UserMessage] = result.scalars().all()

        assert len(messages) == 3
        assert messages[0].message_text == "Сообщение 1"
        assert messages[1].message_text == "Сообщение 2"
        assert messages[2].message_text == "Сообщение 3"
