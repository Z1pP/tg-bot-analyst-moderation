# import logging
# from typing import Dict, List

# from aiogram import Bot
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.triggers.cron import CronTrigger

# from constants.period import TimePeriod
# from container import container
# from dto.report import AllModeratorReportDTO
# from models import ChatSession
# from repositories import ChatTrackingRepository, UserRepository
# from services.time_service import TimeZoneService
# from services.work_time_service import WorkTimeService
# from usecases.report import GetAllModeratorsReportUseCase

# logger = logging.getLogger(__name__)
# scheduler = AsyncIOScheduler()


# def schedule_daily_report(bot: Bot) -> None:
#     """
#     Запланировать ежедневную отправку отчета в 23:00

#     Args:
#         bot: Экземпляр бота для отправки сообщений
#     """
#     scheduler.add_job(
#         func=send_daily_report,
#         args=[bot],
#         trigger=CronTrigger(
#             hour=23,
#             minute=0,
#             second=0,
#             timezone=TimeZoneService.DEFAULT_TIMEZONE,
#         ),
#         id="daily_report",
#         replace_existing=True,
#     )


# async def send_daily_report(bot: Bot) -> None:
#     """
#     Отправка ежедневного отчета модераторам

#     Args:
#         bot: Экземпляр бота для отправки сообщений
#     """

#     user_repo: UserRepository = container.resolve(UserRepository)
#     chat_repo: ChatTrackingRepository = container.resolve(ChatTrackingRepository)

#     admins = await user_repo.get_all_admins()
#     if not admins:
#         return

#     # Собираем чаты для каждого администратора
#     admin_chats: Dict[str, List[ChatSession]] = {}
#     for admin in admins:
#         chats = await chat_repo.get_admin_target_chats(admin_id=admin.id)
#         if chats:  # Добавляем только если есть чаты
#             admin_chats[admin.username] = chats

#     selected_period = TimePeriod.TODAY.value
#     start_date, end_date = TimePeriod.to_datetime(period=selected_period)

#     # Корректируем даты с учетом рабочего времени
#     adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
#         start_date, end_date
#     )

#     report_dto = AllModeratorReportDTO(
#         start_date=adjusted_start,
#         end_date=adjusted_end,
#         selected_period=selected_period,
#     )

#     usecase: GetAllModeratorsReportUseCase = container.resolve(
#         GetAllModeratorsReportUseCase
#     )
#     report_parts = await usecase.execute(dto=report_dto)

#     for part in report_parts:
#         for username, chats in admin_chats.items():
#             for chat in chats:
#                 try:
#                     await bot.send_message(
#                         chat_id=chat.chat_id,
#                         text=part,
#                     )
#                 except Exception as e:
#                     logger.error(f"Ошибка отправки отчета {username}: {e}")
