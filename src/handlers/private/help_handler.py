from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList

router = Router(name=__name__)


@router.message(Command(CommandList.HELP.name.lower()))
async def help_handler(message: Message) -> None:
    help_text = """
    <b>📚 Справочник по командам бота</b>

    <code>✨ Основные команды:</code>
    <b>/start</b> - Запуск бота и главное меню
    <b>/help</b> - Показать эту справку

    <code>👥 Управление модераторами:</code>
    <b>/add_moderator @username</b> - Добавить модератора
    <b>/remove_moderator @username</b> - Удалить модератора

    <code>📊 Отчеты по активности:</code>
    <b>/report_daily 21.04-25.04 @username</b> - Сообщения за период
    <b>/report_avg 6h</b> - Средняя активность (3h/6h/12h/1d)
    <b>/report_response_time @username</b> - Время ответа
    <b>/report_inactive @username</b> - Периоды неактивности

    <code>💾 Экспорт данных:</code>
    <b>/export_start csv</b> - Выгрузить данные (csv/json)

    <code>─────────────────────</code>
    <i>Примеры:</i> 
    • <code>/report_avg 12h</code> - статистика за 12 часов
    • <code>/report_daily 01.05-07.05</code> - недельный отчет
    """

    await message.answer(text=help_text, parse_mode="HTML")
