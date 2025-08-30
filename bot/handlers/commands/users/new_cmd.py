import re
from typing import Optional, Dict, Tuple

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from bot.core.bots import BotInfo
from bot.keyboards.inline.decision import decision_keyboard
from bot.states.new_states import NewStates
from bot.templates import msg
from middleware.loggers import log
from configs import COMMANDS, ImportantID, RpValue

# Глобальная мапа для хранения связей пользователь-топик
user_topic_map: Dict[Tuple[int, str], int] = {}

__all__ = ("router",)
CMD: str = "new"
router: Router = Router(name=f"{CMD}_cmd_router")
TOPIC_TYPE: str = "anketa"

TEXTS: Dict[str, Dict[str, str]] = {
    "anketa": {
        "accept": f"<b>🎉 Ваша анкета принята!</b>\n\nДобро пожаловать в проект!\n\nФлуд: {RpValue.FLUD_URL}\nРолевая: {RpValue.RP_URL}",
        "reject": "<b>❌ Ваша анкета отклонена.</b>\n\nВы можете попробовать позже."
    }
}


async def validate_russian_text(text: str) -> bool:
    """Проверяет текст на соответствие русским буквам, пробелам и дефисам."""
    return bool(re.fullmatch(r"[А-Яа-яЁё\s\-]+", text))


# ===================== Команда /new =====================
@router.callback_query(F.data == CMD)
@router.message(Command(*COMMANDS[CMD], prefix=BotInfo.prefix, ignore_case=True))
@log(level='INFO', log_type=CMD.upper(), text=f"использовал команду /{CMD}")
async def new_cmd(message: Message | CallbackQuery, state: FSMContext) -> None:
    """
    Начало анкеты /new.
    Отправляет пользователю сообщение с просьбой указать желаемую роль.
    """
    await state.clear()
    await state.set_state(NewStates.role)

    ikb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    ikb.row(InlineKeyboardButton(text="Отмена↩️", callback_data='start'))

    text: str = _(
        "Пожалуйста, отправьте желаемую роль:\n"
        "(только русские буквы, пробелы или дефисы)"
    )

    await msg(message=message, text=text, markup=ikb)


# ===================== Обработка роли =====================
@router.message(NewStates.role)
async def process_role(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод роли и запрашивает сортол."""
    if not await validate_russian_text(message.text):
        await message.reply("Ошибка: роль должна содержать только русские буквы, пробелы или дефисы.")
        return

    await state.update_data(role=message.text.strip().title())
    await state.set_state(NewStates.sorol)

    ikb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    ikb.row(InlineKeyboardButton(text="Отмена↩️", callback_data='start'))

    await message.reply(
        text="Теперь укажите желаемый сортол:\n(только русские буквы, пробелы или дефисы)",
        reply_markup=ikb.as_markup()
    )


# ===================== Обработка сортола =====================
@router.message(NewStates.sorol)
async def process_sortol(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод сортола и запрашивает кодовую фразу."""
    if not await validate_russian_text(message.text):
        await message.reply("Ошибка: сорол должен содержать только русские буквы, пробелы или дефисы.")
        return

    await state.update_data(sortol=message.text.strip().title())
    await state.set_state(NewStates.code_phrase)

    ikb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    ikb.row(InlineKeyboardButton(text="Отмена↩️", callback_data='start'))

    await message.reply(
        text="Теперь введите кодовую фразу из правил:",
        reply_markup=ikb.as_markup()
    )


# ===================== Обработка кодовой фразы =====================
@router.message(NewStates.code_phrase)
async def process_code_phrase(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод кодовой фразы и показывает предпросмотр анкеты."""
    code_phrase = message.text.strip()
    if not code_phrase:
        await message.reply("Кодовая фраза не может быть пустой.")
        return

    await state.update_data(code_phrase=code_phrase)
    data: Dict[str, str] = await state.get_data()

    ikb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    ikb.row(
        InlineKeyboardButton(text="Отправить!", callback_data="submit_new"),
        InlineKeyboardButton(text="Отмена↩️", callback_data="start")
    )

    text: str = (
        f"<b>Проверьте данные анкеты:</b>\n\n"
        f"• Роль: {data['role']}\n"
        f"• Сортол: {data['sortol']}\n"
        f"• Кодовая фраза: {data['code_phrase']}"
    )

    await message.reply(text, reply_markup=ikb.as_markup())


# ===================== Отправка анкеты в поддержку =====================
@router.callback_query(F.data == "submit_new")
async def submit_new_cmd(callback: CallbackQuery, state: FSMContext) -> None:
    """Отправляет анкету в топик форума поддержки и создает запись в мапе."""
    data: Dict[str, str] = await state.get_data()
    user = callback.from_user

    # Создаем топик в форуме
    topic = await callback.bot.create_forum_topic(
        chat_id=ImportantID.SUPPORT_CHAT_ID,
        name=f"Анкета от {user.full_name}"
    )
    thread_id: int = topic.message_thread_id

    # Сохраняем связь пользователь-топик
    user_topic_map[(user.id, TOPIC_TYPE)] = thread_id

    # Формируем текст анкеты
    text: str = (
        f'<b><a href="tg://user?id={user.id}">Анкета</a></b>\n\n'
        f"• Роль: {data['role']}\n"
        f"• Сортол: {data['sortol']}\n"
        f"• Кодовая фраза: {data['code_phrase']}"
    )

    # Отправляем в топик с кнопками принятия/отклонения
    await callback.bot.send_message(
        chat_id=ImportantID.SUPPORT_CHAT_ID,
        message_thread_id=thread_id,
        text=text,
        parse_mode="HTML",
        reply_markup=decision_keyboard(thread_id=thread_id, kind=TOPIC_TYPE)
    )

    await callback.message.edit_text("✅ Ваша анкета успешно отправлена на рассмотрение!")
    await state.clear()


# ===================== Обработка решения админов =====================
@router.callback_query(F.data.regexp(r"^([a-z_]+):(accept|reject):(\d+)$"))
async def process_decision_callback(callback: CallbackQuery) -> None:
    """Обрабатывает решение администраторов и отправляет результат пользователю."""
    kind, action, thread_id_str = callback.data.split(":")
    thread_id = int(thread_id_str)

    # Ищем пользователя по thread_id в мапе
    user_id = None
    for (uid, k), tid in user_topic_map.items():
        if k == kind and tid == thread_id:
            user_id = uid
            break

    if not user_id:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    text_to_send: Optional[str] = TEXTS.get(kind, {}).get(action)
    if not text_to_send:
        await callback.answer("Некорректные данные.", show_alert=True)
        return

    await callback.bot.send_message(chat_id=user_id, text=text_to_send, parse_mode="HTML")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Ответ отправлен пользователю.")


# ===================== Пересылка ответов админов пользователю =====================
@router.message(F.is_topic_message, F.reply_to_message, ~F.from_user.is_bot)
async def forward_reply_to_user(message: Message) -> None:
    """Пересылает ответы администраторов из топика пользователю."""
    thread_id = message.message_thread_id
    if not thread_id:
        return

    # Ищем пользователя по thread_id
    user_id = None
    for (uid, _), tid in user_topic_map.items():
        if tid == thread_id:
            user_id = uid
            break

    if not user_id:
        return

    reply_text: str = f"<b>Ответ администратора:</b>\n{message.html_text}"
    try:
        await message.bot.send_message(chat_id=user_id, text=reply_text, parse_mode="HTML")
    except Exception as e:
        await message.reply(f"⚠️ Не удалось отправить сообщение пользователю: {e}")