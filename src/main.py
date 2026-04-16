import argparse
import asyncio
import logging
import os
import sys

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot import configure_dispatcher
from commands.start_commands import set_bot_commands
from config import settings
from container import ContainerSetup
from database.session import engine
from scheduler import broker
from utils.logger_config import setup_logger

setup_logger(log_level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_UPDATES = [
    "message",
    "edited_message",
    "callback_query",
    "inline_query",
    "chat_member",
    "message_reaction",
]


async def init_bot() -> tuple[Bot, Dispatcher]:
    """Инициализирует контейнер зависимостей и возвращает экземпляры бота и диспетчера."""
    logger.info("Инициализация контейнера...")
    ContainerSetup.setup()
    logger.info("Настройка и запуск бота...")
    return await configure_dispatcher()


async def setup_webhook_and_commands(bot: Bot, webhook_url: str) -> None:
    """Настраивает вебхук и команды перед стартом веб-сервера."""
    await broker.startup()
    logger.info("TaskIQ broker запущен")

    url = f"{webhook_url}/webhook"
    logger.info("🚀 Устанавливаем webhook: %s", url)
    await bot.set_webhook(url, allowed_updates=ALLOWED_UPDATES)
    await set_bot_commands(bot)


async def root(request: web.Request) -> web.Response:
    """Проверка работоспособности aiohttp сервера."""
    return web.json_response({"status": "ok", "message": "Webhook server is running"})


async def health(request: web.Request) -> web.Response:
    """Возвращает статус здоровья бота и конфигурацию."""
    return web.json_response(
        {
            "status": "healthy",
            "webhook_configured": request.app.get("webhook_url") is not None,
            "bot_initialized": request.app.get("bot") is not None,
        }
    )


async def webhook_info(request: web.Request) -> web.Response:
    """Возвращает информацию о текущем webhook от Telegram API."""
    bot: Bot | None = request.app.get("bot")
    if bot:
        info = await bot.get_webhook_info()
        return web.json_response(
            {
                "url": info.url,
                "has_custom_certificate": info.has_custom_certificate,
                "pending_update_count": info.pending_update_count,
                "last_error_date": info.last_error_date,
                "last_error_message": info.last_error_message,
            }
        )
    return web.json_response({"error": "Bot not initialized"}, status=503)


def build_web_app(bot: Bot, dp: Dispatcher, webhook_url: str) -> web.Application:
    """Создает aiohttp приложение для webhook, изолируя зависимости внутри app."""
    app = web.Application()

    app["bot"] = bot
    app["webhook_url"] = webhook_url

    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    app.router.add_get("/webhook-info", webhook_info)

    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    return app


async def run_fastapi() -> None:
    """Запускает FastAPI (Mini App API) через uvicorn."""
    from api.main import create_app as create_fastapi_app

    api_port = int(settings.API_PORT)
    fastapi_app = create_fastapi_app()

    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=api_port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info("FastAPI server starting on port %d", api_port)

    await server.serve()


async def run_webhook(bot: Bot, dp: Dispatcher, webhook_url: str) -> None:
    """Запускает aiohttp (webhook) в фоне и FastAPI (Mini App) как блокирующий процесс."""
    logger.info("Запуск в режиме webhook...")

    await setup_webhook_and_commands(bot, webhook_url)

    app = build_web_app(bot, dp, webhook_url)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logger.info("Webhook server started on port %s", port)

    try:
        await run_fastapi()
    finally:
        logger.info("Остановка Webhook сервера aiohttp...")
        await runner.cleanup()


async def run_polling(bot: Bot, dp: Dispatcher):
    """Запускает бота в режиме long polling."""
    await broker.startup()
    logger.info("TaskIQ broker запущен")

    logger.info("Удаляем webhook...")
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Настраиваем команды...")
    await set_bot_commands(bot)

    logger.info("Запуск polling...")
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


async def shutdown(bot: Bot, dp: Dispatcher) -> None:
    """Идемпотентная функция для безопасного закрытия ресурсов."""
    logger.info("Начало процесса Graceful Shutdown...")

    if bot and bot.session:
        logger.info("Закрытие сессии бота...")
        await bot.session.close()

    try:
        logger.info("Остановка TaskIQ broker...")
        await broker.shutdown()
    except Exception as e:
        logger.warning("Ошибка при остановке брокера: %s", e)

    if dp and getattr(dp, "storage", None):
        logger.info("Закрытие хранилища FSM...")
        await dp.storage.close()

    try:
        logger.info("Закрытие пула соединений с БД...")
        await engine.dispose()
    except Exception as e:
        logger.warning("Ошибка при закрытии БД: %s", e)

    logger.info("Бот успешно остановлен.")


async def main():
    """Точка входа."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--webhook-url", type=str, default=None)
    args = parser.parse_args()

    webhook_url = args.webhook_url or settings.USE_WEBHOOK

    bot, dp = await init_bot()

    try:
        if webhook_url:
            await run_webhook(bot, dp, webhook_url)
        else:
            await run_polling(bot, dp)
    except Exception as e:
        logger.error("Критическая ошибка: %s", str(e), exc_info=True)
        sys.exit(1)
    finally:
        await shutdown(bot, dp)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
