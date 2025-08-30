from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from bot.templates import msg_photo
from bot.utils.interesting_facts import interesting_fact
from bot.core.bots import BotInfo
from configs import COMMANDS, RpValue

# Настройки экспорта и роутера
__all__ = ("router",)
CMD: str = "settings".lower()
router: Router = Router(name=f"{CMD}_cmd_router")


@router.callback_query(F.data.lower() == CMD)
@router.message(Command(*COMMANDS[CMD], prefix=BotInfo.prefix, ignore_case=True))
async def start_cmd(message: Message | CallbackQuery, state: FSMContext) -> None:
    """Обработчик команды /start"""
    await state.clear()

    # Создание инлайн-клавиатуры
    ikb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    ikb.row(InlineKeyboardButton(text="Инфо-канал🗂", url=RpValue.INFO_URL))
    ikb.row(InlineKeyboardButton(text="Вступление🚀", callback_data='new'),
            InlineKeyboardButton(text="Анкета📖", callback_data='anketa'))
    ikb.row(InlineKeyboardButton(text="Связь с администрацией🌐", callback_data='admin'))

    # Формируем приветственное сообщение
    text: str = _(
        """Добро пожаловать, <a href="{url}">{name}</a>!

Я ваш искусственный помощник по ролевой - <b>{rp_name}</b>! 
Моя цель — помочь вам сориентироваться и сделать ваше вступление куда проще! 
Надеюсь, я смогу вам помочь! Пожалуйста, выберите нужную функцию на клавиатуре!

Интересный факт:
<blockquote>{fact}</blockquote>
"""
    ).format(
        url=message.from_user.url if message.from_user else "",
        name=message.from_user.first_name if message.from_user else "пользователь",
        rp_name=RpValue.RP_NAME,
        fact=interesting_fact(),
    )

    # Отправляем сообщение
    await msg_photo(message=message, text=text, file=f'assets/{CMD}.jpg', markup=ikb)
