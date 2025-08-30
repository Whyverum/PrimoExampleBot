from aiogram import Router
from .settings_cmd import router as settings_cmd_router

# Настройка экспорта и роутера
__all__ = ("router",)
router: Router = Router(name=__name__)

# Подключение роутеров
router.include_routers(
    settings_cmd_router,
)
