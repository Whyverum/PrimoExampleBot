from aiogram import Router
from .default import router as default_message_router

# Настройка экспорта и роутера
__all__ = ('router',)
router: Router = Router(name=__name__)

# Подготовка роутера команд
#router.include_routers(
#)

# Подключение стандартного роутера
router.include_router(default_message_router)
