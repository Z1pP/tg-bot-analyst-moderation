import argparse
import asyncio
import logging
import os
import sys

from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot import configure_dispatcher
from commands.start_commands import set_bot_commands
from config import settings
from container import ContainerSetup
from database.session import engine
from utils.logger_config import setup_logger

setup_logger(log_level=logging.INFO)

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--webhook-url", type=str, default=None)
args = parser.parse_args()

bot = None
dp = None


ALLOWED_UPDATES = [
    "message",
    "edited_message",
    "callback_query",
    "inline_query",
    "chat_member",
    "message_reaction",
]


async def init_bot() -> None:
    """Инициализирует контейнер зависимостей и настраивает бота."""
    global bot, dp
    logger.info("Инициализация контейнера...")
    ContainerSetup.setup()
    logger.info("Настройка и запуск бота...")
    bot, dp = await configure_dispatcher()


async def on_startup(app: web.Application) -> None:
    """Устанавливает webhook и команды при старте сервера."""
    if args.webhook_url:
        url = f"{args.webhook_url}/webhook"
        logger.info("🚀 Устанавливаем webhook: %s", url)
        await bot.set_webhook(url, allowed_updates=ALLOWED_UPDATES)
        await set_bot_commands(bot)


async def on_shutdown(app: web.Application) -> None:
    """Освобождает ресурсы при остановке сервера."""
    await shutdown(bot, dp)


async def root(request: web.Request) -> web.Response:
    """Проверка работоспособности бота."""
    return web.json_response({"status": "ok", "message": "Bot is running"})


async def health(request: web.Request) -> web.Response:
    """Возвращает статус здоровья бота и конфигурацию."""
    return web.json_response(
        {
            "status": "healthy",
            "webhook_configured": args.webhook_url is not None,
            "bot_initialized": bot is not None,
        }
    )


async def webhook_info(request: web.Request) -> web.Response:
    """Возвращает информацию о текущем webhook."""
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


def build_web_app() -> web.Application:
    """Создает aiohttp приложение для webhook."""
    app = web.Application()
    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    app.router.add_get("/webhook-info", webhook_info)

    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


async def run_webhook() -> None:
    """Запускает бота в режиме webhook через aiohttp."""
    logger.info("Запуск в режиме webhook...")
    await init_bot()
    app = build_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    await site.start()
    logger.info("Webhook server started")
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


async def run_polling():
    """Запускает бота в режиме long polling."""

    await init_bot()

    logger.info("Удаляем webhook...")
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Настраиваем команды...")
    await set_bot_commands(bot)

    logger.info("Запуск polling...")

    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


async def shutdown(bot, dp) -> None:
    """
    Функция для корректного завершения всех ресурсов.
    """
    logger.info("Начало процесса Graceful Shutdown...")

    if dp and dp.is_polling():
        logger.info("Остановка polling...")
        dp.stop_polling()

    if bot and hasattr(bot, "session") and not bot.session.closed:
        logger.info("Закрытие сессии бота...")
        await bot.session.close()

    logger.info("Закрытие соединений с БД...")
    await engine.dispose()

    if dp and dp.storage:
        logger.info("Закрытие хранилища FSM...")
        await dp.storage.close()

    logger.info("Бот успешно остановлен.")


async def main():
    """Точка входа: выбирает режим запуска (webhook/polling)."""
    webhook_url = args.webhook_url or settings.USE_WEBHOOK
    try:
        if webhook_url:
            await run_webhook()
        else:
            await run_polling()
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
        sys.exit(0)
