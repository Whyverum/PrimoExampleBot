from aiogram import Router
from .start_cmd import router as start_cmd_router
from .active import router as active_cmd_router

# Настройка экспорта и роутера
__all__ = ("router",)
router: Router = Router(name=__name__)

# Подключение роутеров
router.include_routers(
    start_cmd_router,
    active_cmd_router,
)
