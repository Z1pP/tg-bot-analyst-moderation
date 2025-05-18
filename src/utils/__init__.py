import re

from aiogram import Bot

from repositories.user_repository import UserRepository


async def save_all_administators_in_db(chat_id: str, bot: Bot) -> bool:
    admins = await bot.get_chat_administrators(chat_id=chat_id)

    service = UserRepository()

    await service.save_all(admins[1])


async def match_username(text: str) -> str:
    match = re.match(r"^@?(\w+)$", text)

    if match:
        return match.group(1)
    return None
