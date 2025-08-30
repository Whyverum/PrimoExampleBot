from aiogram.types import InlineKeyboardButton

# Настройка экспорта в модули
__all__ = ('pagination_btn',)

def pagination_btn(action: str,
                   page: int = 0,
                   total_posts: int = 0,
                   bt_page: int = 5) -> list[InlineKeyboardButton]:
    """
    Создает кнопки для пагинации.

    :param action: Действие в котором нужна пангинация.
    :param page: Номер начальной страницы, по умолчанию 0.
    :param total_posts: Количество постов.
    :param bt_page: Количество кнопок на одной странице.
    :return: Готовый лист списка инлайн-кнопок.
    """
    navigation_buttons: list[InlineKeyboardButton] = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="←", callback_data=f"{action}_page_{page - 1}"
        ))
    if (page + 1) * bt_page < total_posts:
        navigation_buttons.append(InlineKeyboardButton(
            text="→", callback_data=f"{action}_page_{page + 1}"
        ))
    return navigation_buttons
