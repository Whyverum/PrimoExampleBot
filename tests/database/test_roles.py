import pytest
from typing import List, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Role, RoleRegion, BotDatabase


@pytest.mark.asyncio
class TestRoleSystem:
    """Тесты для системы ролей с полной строгой типизацией"""

    async def test_role_creation(self, test_db: BotDatabase, test_session: AsyncSession) -> None:
        """
        Тест создания ролей.
        Проверяет, что тестовые роли существуют в базе.
        """
        stmt = select(Role)
        result = await test_session.execute(stmt)
        roles: List[Role] = result.scalars().all()

        assert len(roles) >= 5
        role_names: List[str] = [role.name for role in roles]
        assert "Альбедо" in role_names
        assert "Нахида" in role_names
        assert "Кафка" in role_names

    async def test_assign_role(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест назначения роли пользователю.
        Проверяет успешное назначение свободной роли и правильное сохранение в БД.
        """
        user_id: int = test_user

        # Освобождаем роль на всякий случай
        await test_db.release_role("Альбедо")

        # Назначаем роль
        success: bool = await test_db.assign_role("Альбедо", user_id)
        assert success, "Не удалось назначить роль"

        # Проверяем, что роль действительно назначена
        stmt = select(Role).where(Role.name == "Альбедо")
        result = await test_session.execute(stmt)
        role: Role = result.scalar_one()

        assert role.occupied_by == user_id

    async def test_assign_occupied_role(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест назначения уже занятой роли.
        Проверяет, что нельзя назначить роль, если она уже занята другим пользователем.
        """
        user_id: int = test_user
        other_user_id: int = 999000111

        await test_db.release_role("Альбедо")
        await test_db.add_user(other_user_id, "other_user", "Other User")

        # Назначаем роль первому пользователю
        success_first: bool = await test_db.assign_role("Альбедо", user_id)
        assert success_first, "Не удалось назначить роль первому пользователю"

        # Пытаемся назначить ту же роль другому пользователю
        success_second: bool = await test_db.assign_role("Альбедо", other_user_id)
        assert not success_second, "Нельзя назначить занятую роль"

    async def test_release_role(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест освобождения роли.
        Проверяет, что роль успешно освобождается.
        """
        user_id: int = test_user

        await test_db.release_role("Нахида")
        success_assign: bool = await test_db.assign_role("Нахида", user_id)
        assert success_assign

        success_release: bool = await test_db.release_role("Нахида")
        assert success_release

        stmt = select(Role).where(Role.name == "Нахида")
        result = await test_session.execute(stmt)
        role: Role = result.scalar_one()
        assert role.occupied_by is None

    async def test_release_unoccupied_role(self, test_db: BotDatabase) -> None:
        """
        Тест освобождения свободной роли.
        Проверяет, что нельзя освободить уже свободную роль.
        """
        await test_db.release_role("Кафка")
        success: bool = await test_db.release_role("Кафка")
        assert not success, "Нельзя освободить свободную роль"

    async def test_get_user_roles(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест получения ролей пользователя.
        Проверяет, что возвращается корректный список назначенных ролей.
        """
        user_id: int = test_user

        await test_db.release_role("Альбедо")
        await test_db.release_role("Нахида")

        success1: bool = await test_db.assign_role("Альбедо", user_id)
        success2: bool = await test_db.assign_role("Нахида", user_id)
        assert success1 and success2

        roles: List[str] = await test_db.get_roles_by_user(user_id)
        assert len(roles) == 2
        assert "Альбедо" in roles
        assert "Нахида" in roles

    async def test_get_available_roles(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест получения доступных ролей.
        Проверяет, что назначенные роли не включены в список свободных.
        """
        user_id: int = test_user

        # Освобождаем все роли
        for role_name in ["Альбедо", "Нахида", "Кафка", "Броння", "Чжун Ли"]:
            await test_db.release_role(role_name)

        # Назначаем одну роль
        success: bool = await test_db.assign_role("Альбедо", user_id)
        assert success

        available_roles: List[Role] = await test_db.get_available_roles()
        role_names: List[str] = [role.name for role in available_roles]

        assert "Альбедо" not in role_names
        assert len(available_roles) > 0

        for role in available_roles:
            assert role.occupied_by is None

    async def test_get_occupied_roles(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест получения занятых ролей.
        Проверяет, что все назначенные роли возвращаются корректно.
        """
        user_id: int = test_user

        await test_db.release_role("Альбедо")
        await test_db.release_role("Нахида")

        success1: bool = await test_db.assign_role("Альбедо", user_id)
        success2: bool = await test_db.assign_role("Нахида", user_id)
        assert success1 and success2

        occupied_roles: List[Role] = await test_db.get_occupied_roles()
        role_names: List[str] = [role.name for role in occupied_roles]

        assert "Альбедо" in role_names
        assert "Нахида" in role_names
        assert len(occupied_roles) >= 2

    async def test_region_filter(
        self, test_db: BotDatabase, test_session: AsyncSession
    ) -> None:
        """
        Тест фильтрации ролей по регионам.
        Проверяет, что метод возвращает роли только указанного региона.
        """
        await test_db.release_role("Альбедо")
        mondstadt_roles: List[Role] = await test_db.get_available_roles(RoleRegion.MONDSTADT)

        assert len(mondstadt_roles) == 1
        assert mondstadt_roles[0].name == "Альбедо"
        assert mondstadt_roles[0].region == RoleRegion.MONDSTADT

    async def test_region_stats(
        self, test_db: BotDatabase, test_session: AsyncSession, test_user: int
    ) -> None:
        """
        Тест статистики по регионам.
        Проверяет, что метод возвращает корректное количество занятых ролей по регионам.
        """
        user_id: int = test_user

        await test_db.release_role("Альбедо")
        await test_db.release_role("Нахида")

        success1: bool = await test_db.assign_role("Альбедо", user_id)
        success2: bool = await test_db.assign_role("Нахида", user_id)
        assert success1 and success2

        stats: Dict[RoleRegion, Dict[str, int]] = await test_db.get_region_stats()

        assert RoleRegion.MONDSTADT in stats
        assert RoleRegion.SUMERU in stats
        assert stats[RoleRegion.MONDSTADT]["occupied"] == 1
        assert stats[RoleRegion.MONDSTADT]["total"] == 1
