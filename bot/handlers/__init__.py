from aiogram import Router
from bot.handlers.commands import router as cmd_routers
from .messages import router as messages_routers

# Настройка экспорта и роутера
__all__ = ("router",)
router: Router = Router(name=__name__)

# Подключение роутеров
router.include_routers(
    cmd_routers,
    messages_routers,

)
