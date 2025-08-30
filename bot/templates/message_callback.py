from typing import Union

from aiogram.types import FSInputFile, CallbackQuery, Message, ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Настройка экспорта
__all__ = ('msg', 'msg_photo')


async def msg(message: Message | CallbackQuery,
              text: str = "Сообщение отправлено!",
              markup: Union[InlineKeyboardBuilder, ReplyKeyboardBuilder, None] = None) -> None:
    """
    Шаблон для ответа на сообщение текстом.
    :param message: Объект сообщения или callback-запроса.
    :param text: Текст отправного сообщения от бота.
    :param markup: Кнопки сообщения (инлайн или реплай).
    """

    # Преобразуем клавиатуру
    reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None
    if markup:
        if isinstance(markup, InlineKeyboardBuilder):
            reply_markup: InlineKeyboardMarkup = markup.as_markup()
        elif isinstance(markup, ReplyKeyboardBuilder):
            reply_markup: ReplyKeyboardMarkup = markup.as_markup(resize_keyboard=True)

    # Обработчик ответа на сообщение
    if isinstance(message, Message):
        await message.reply(
            text=text,
            reply_markup=reply_markup
        )
    # Обработчик ответа на callback
    else:
        await message.message.reply(
            text=text,
            reply_markup=reply_markup
        )


async def msg_photo(
    message: Message | CallbackQuery,
    text: str = "Сообщение отправлено!",
    file: str = "assets/default.jpg",
    markup: Union[InlineKeyboardBuilder, ReplyKeyboardBuilder, None] = None) -> None:
    """
    Шаблон для ответа на сообщение фотографией.
    :param message: Объект сообщения или callback-запроса.
    :param file: Путь к фотографии для ответа.
    :param text: Подпись к фото.
    :param markup: Кнопки сообщения (инлайн или реплай).
    """

    # Преобразуем клавиатуру
    reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None
    if markup:
        if isinstance(markup, InlineKeyboardBuilder):
            reply_markup = markup.as_markup()
        elif isinstance(markup, ReplyKeyboardBuilder):
            reply_markup = markup.as_markup(resize_keyboard=True)

    # Обработчик ответа на сообщение
    if isinstance(message, Message):
        await message.reply_photo(
            photo=FSInputFile(file),
            caption=text,
            reply_markup=reply_markup
        )

    # Обработчик ответа на callback
    else:
        await message.message.reply_photo(
            photo=FSInputFile(file),
            caption=text,
            reply_markup=reply_markup
        )
