import argparse
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from aiogram.types import Update
from fastapi import FastAPI, Request

from bot import configure_dispatcher
from container import ContainerSetup
from utils.logger_config import setup_logger

setup_logger(log_level=logging.INFO)

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--webhook-url", type=str, default=None)
args = parser.parse_args()

bot = None
dp = None


async def init_bot():
    """Инициализирует контейнер зависимостей и настраивает бота."""
    global bot, dp
    logger.info("Инициализация контейнера...")
    ContainerSetup.setup()
    logger.info("Настройка и запуск бота...")
    bot, dp = await configure_dispatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управляет жизненным циклом FastAPI: инициализация и очистка ресурсов."""
    await init_bot()

    if args.webhook_url:
        url = f"{args.webhook_url}/webhook"
        logger.info("🚀 Устанавливаем webhook: %s", url)
        await bot.set_webhook(url)

    yield

    if bot and hasattr(bot, "session"):
        await bot.session.close()
        logger.info("Сессия бота закрыта")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    """Проверка работоспособности бота."""
    return {"status": "ok", "message": "Bot is running"}


@app.get("/health")
async def health():
    """Возвращает статус здоровья бота и конфигурацию."""
    return {
        "status": "healthy",
        "webhook_configured": args.webhook_url is not None,
        "bot_initialized": bot is not None,
    }


@app.get("/webhook-info")
async def webhook_info():
    """Возвращает информацию о текущем webhook."""
    if bot:
        info = await bot.get_webhook_info()
        return {
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message,
        }
    return {"error": "Bot not initialized"}


@app.post("/webhook")
async def webhook(request: Request):
    """Обрабатывает входящие обновления от Telegram."""
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


async def run_webhook():
    """Запускает бота в режиме webhook через FastAPI."""
    logger.info("Запуск в режиме webhook...")
    config = uvicorn.Config(
        app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)), log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_polling():
    """Запускает бота в режиме long polling."""
    await init_bot()
    logger.info("Удаляем webhook...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Запуск polling...")
    await dp.start_polling(bot)


async def main():
    """Точка входа: выбирает режим запуска (webhook/polling)."""
    try:
        # if args.webhook_url:
        #     await run_webhook()
        # else:
        await run_polling()
    except Exception as e:
        logger.error("Критическая ошибка: %s", str(e), exc_info=True)
        sys.exit(1)
    finally:
        if bot and hasattr(bot, "session"):
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
        sys.exit(0)
