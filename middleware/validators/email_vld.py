from typing import Optional

from email_validator import validate_email, EmailNotValidError, ValidatedEmail

# Настройка экспорта из этого модуля
__all__ = ("valid_email",)


def valid_email(e_mail: str) -> Optional[str]:
    """
    Валидация почты через библиотеку.

    :param e_mail: Получаемая почта.
    :return: Нормализированная почта.
    """
    try:
        # Провека почты на валидность
        email: ValidatedEmail = validate_email(e_mail)

    except EmailNotValidError:
        return None

    # Возвращение строки с нормализированной почтой
    return email.normalized
