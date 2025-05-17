from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList
from utils.send_message import send_html_message

router = Router(name=__name__)


@router.message(Command(CommandList.START.name.lower()))
async def start_handler(message: Message) -> None:
    username = message.from_user.full_name
    welcome_text = f"""
    <b>Привет, {username}!</b> ✨
    <i>Рад видеть тебя здесь!</i>

    Я бот, который поможет тебе:

    <b>📊 Мониторинг активности</b>
    <code>• Анализ сообщений в чатах</code>
    <code>• Топ активных пользователей</code>

    <b>📈 Статистика</b>
    <code>• Отчеты за любой период</code>
    <code>• Графики активности</code>

    <b>⏱ Управление процессами</b>
    <code>• Контроль рабочих задач</code>
    <code>• Напоминания и уведомления</code>

    <u>Давай начнем!</u> Просто напиши <b>/help</b> чтобы увидеть все возможности.
    """

    await send_html_message(message=message, text=welcome_text)
