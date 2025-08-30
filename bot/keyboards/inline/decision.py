from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def decision_keyboard(thread_id: int, kind: str) -> InlineKeyboardMarkup:
    """
    Получение клавиатуры Принятия\Отклонить.

    :param thread_id: Айди действия.
    :param kind: Вид для клавиатуры.
    :return: Инлайн-клавиатуру (Принять, Отклонить).
    """
    ikb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    ikb.row(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"{kind}:accept:{thread_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"{kind}:reject:{thread_id}")
    )
    return ikb.as_markup()
