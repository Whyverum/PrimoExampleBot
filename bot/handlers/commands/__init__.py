from aiogram import Router
from .admins import router as admin_cmd_router
from .users import router as users_cmd_router

# Настройка экспорта и роутера
__all__ = ("router",)
router: Router = Router(name=__name__)

# Подключение роутеров
router.include_routers(
    admin_cmd_router,
    users_cmd_router,
)
