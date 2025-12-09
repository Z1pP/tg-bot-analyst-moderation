import asyncio
import logging

from app.adapters.bot.main import start_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    asyncio.run(start_bot())


if __name__ == "__main__":
    main()
