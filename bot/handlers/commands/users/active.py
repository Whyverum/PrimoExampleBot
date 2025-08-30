from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.templates import msg_photo
from bot.core.bots import BotInfo
from configs import COMMANDS
from database import db



# Настройки экспорта и роутера
__all__ = ("router",)


CMD: str = "active".lower()
router: Router = Router(name=f"{CMD}_cmd_router")


@router.callback_query(F.data.lower() == CMD)
@router.message(Command(*COMMANDS[CMD], prefix=BotInfo.prefix, ignore_case=True))
async def active_cmd(message: Message | CallbackQuery, state: FSMContext) -> None:
    """Обработчик команды /active"""
    await state.clear()

    # Получить статистику сообщений пользователя
    day, week, month, total = await db.get_message_stats(message.from_user.id)

    print(f"За день: {day} сообщений")
    print(f"За неделю: {week} сообщений")
    print(f"За месяц: {month} сообщений")
    print(f"Всего: {total} сообщений")

    # Формируем приветственное сообщение
    text: str =f"""
За день: {day} сообщений
За неделю: {week} сообщений
За месяц: {month} сообщений
Всего: {total} сообщений
"""


    # Отправляем сообщение
    await msg_photo(message=message, text=text,)
