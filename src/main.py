import logging

from aiogram import Bot, Dispatcher

from config import settings

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    dp.run_polling(bot)
