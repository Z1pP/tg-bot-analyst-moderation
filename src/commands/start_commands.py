from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeDefault,
)


async def set_bot_commands(bot: Bot) -> None:
    """Устанавливает команды бота."""
    # Удаляем все старые команды
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
    await bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
    await bot.delete_my_commands(scope=BotCommandScopeAllGroupChats())

    # Устанавливаем /start только для приватных чатов
    commands = [BotCommand(command="start", description="Запустить бота")]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())

    await bot.set_my_commands(commands=[], scope=BotCommandScopeAllGroupChats())
