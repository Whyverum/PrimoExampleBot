from random import choice

from configs.config import Lists

# Настройки экспорта
__all__ = ("interesting_fact",)


def interesting_fact(mode: str = "факт", lists: list[str] = None) -> str:
    """
    Возвращает случайный факт, анекдот или цитату, в зависимости от режима.

    :param mode: Строка, определяющая тип контента ("факт", "анекдот", "цитата").
    :param lists: Необязательный список строк, из которого можно выбирать вручную.
    :return: Случайный элемент из соответствующего списка.
    """
    if lists is not None:
        return choice(lists)

    mode: str = mode.lower()

    if mode == "анекдот":
        source: list[str] = Lists.jokes
    elif mode == "цитата":
        source: list[str] = Lists.quotes
    else:
        source: list[str] = Lists.facts

    return choice(source)
