from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery

# Настройка экспорта
__all__ = ("CallbackDataStartsWith",)


class CallbackDataStartsWith(BaseFilter):
    """
    Фильтр для callback_data, начинающихся с префикса.

    Example:
        @router.callback_query(CallbackDataStartsWith("menu:"))
        async def handler(cb: CallbackQuery):
            await cb.answer("Это callback из меню ✅")
    """
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    async def __call__(self, callback: CallbackQuery) -> bool:
        return bool(callback.data and callback.data.startswith(self.prefix))
