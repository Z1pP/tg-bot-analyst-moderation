import asyncio
import logging
import sys

from bot import init_bot

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


async def main():
    try:
        bot, dp = await init_bot()
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
