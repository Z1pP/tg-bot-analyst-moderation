from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

from constants import CommandList


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command=comm.name.lower(), description=comm.value)
        for comm in CommandList
    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
