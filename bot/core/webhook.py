from typing import Any

from fastapi import FastAPI, Request
from uvicorn import Config, Server
from aiogram.types import Update

from configs import Webhook
from .bots import dp, bot

# Настройки экспорта
__all__ = ("app", "config", "server",)


# Создаём FastAPI приложение
app: FastAPI = FastAPI()

# Создаём конфиг для uvicorn
config: Config = Config(
    app="bot.core.webhook:app",
    host=Webhook.WEBAPP_HOST,
    port=Webhook.WEBAPP_PORT,
    log_level=Webhook.LOG_LEVEL,  # выводить только предупреждения и ошибки
    access_log=Webhook.ACCES_LOG  # <-- отключает все HTTP-access логи
)

# Создание вебхук-сервера
server: Server = Server(config)


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, Any]:
    """
    Обработчик POST-запроса от Telegram.
    """
    update: Update = Update(**await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}
