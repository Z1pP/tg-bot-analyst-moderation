import asyncio
import time
from pathlib import Path

import aiohttp
import jwt
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message
from aiohttp import ClientTimeout

from app.adapters.bot.config import bot_config


def _build_service_token() -> str:
    private_key = Path(bot_config.SERVICE_BOT_PRIVATE_KEY_PATH).read_text()
    payload = {
        "iss": "bot",
        "aud": bot_config.SERVICE_JWT_AUDIENCE,
        "role": "bot",
        "exp": int(time.time()) + bot_config.SERVICE_JWT_TTL_SECONDS,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


async def call_backend_bot_info() -> dict:
    token = _build_service_token()
    url = bot_config.BACKEND_URL.rstrip("/") + "/api/v1/bot"
    headers = {"Authorization": f"Bearer {token}"}
    timeout = ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()


router = Router(name="bot-router")


@router.message(Command("backend"))
async def backend_handler(message: Message):
    """
    Дёргаем backend `/api/v1/bot` через сервисный JWT.
    """
    try:
        resp = await call_backend_bot_info()
        await message.answer(f"Backend ok: {resp.get('message', 'ok')}")
    except Exception as e:
        await message.answer(f"Backend error: {e}")


async def start_bot() -> None:
    bot = Bot(token=bot_config.BOT_TOKEN)
    storage = RedisStorage.from_url(bot_config.REDIS_URL)
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
