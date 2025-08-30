from asyncio import run

from bot import BotInfo, bot, dp, router
from bot.core import server
from bot.middlewares import setup_middlewares
from database import db
from configs import Webhook
from middleware.loggers import setup_logging, loggers


async def main() -> None:
    """
    Входная точка проекта.
    Настройка и запуск бота в режиме webhook или polling.
    """
    try:
        # Логирование
        setup_logging()

        # Cоздание базы данных
        await db.init_db()
        # Проверка соединения
        if not await db.check_connection():
            print("Не удалось подключиться к БД!")
            return
        await db.init_default_roles()

        # Настройка информации о боте
        await BotInfo.setup(bots=bot)

        # Настройка middleware
        setup_middlewares(
            dp=dp,
            bot=bot,
            channel_ids=[]  # пустой список каналов (можно добавить потом)
        )

        # Подключение маршрутов (роутеров)
        dp.include_router(router)

        # Выбор режима работы: webhook или polling
        if Webhook.WEBHOOK:
            loggers.info(f"Запуск бота @{BotInfo.username} в режиме вебхука...\n")
            await server.serve()

        else:
            loggers.info(f"Бот @{BotInfo.username} запущен в режиме polling...\n")
            await dp.start_polling(bot)

    except Exception as e:
        loggers.error(f"🔥 Критическая ошибка при запуске: {e}")
        raise


if __name__ == "__main__":
    run(main())
