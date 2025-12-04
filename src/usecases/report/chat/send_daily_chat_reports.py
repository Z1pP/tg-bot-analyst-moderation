import logging

from constants.period import TimePeriod
from dto.report import ChatReportDTO
from models import User
from repositories import ChatRepository, UserRepository
from services.messaging.bot_message_service import BotMessageService
from usecases.report.chat.get_chat_report import GetReportOnSpecificChatUseCase

logger = logging.getLogger(__name__)


class SendDailyChatReportsUseCase:
    """UseCase для автоматической отправки ежедневных отчетов по чатам в архивные чаты."""

    def __init__(
        self,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        bot_message_service: BotMessageService,
        report_usecase: GetReportOnSpecificChatUseCase,
    ):
        self._chat_repository = chat_repository
        self._user_repository = user_repository
        self._bot_message_service = bot_message_service
        self._report_usecase = report_usecase

    async def execute(self, period: str = TimePeriod.TODAY.value) -> None:
        """
        Генерирует и отправляет отчеты по всем чатам с архивными чатами.

        Args:
            period: Период отчета (по умолчанию за сегодня)
        """
        logger.info("Начало генерации ежедневных отчетов по чатам")

        try:
            # Получаем чаты с архивными чатами
            chats_with_archive = await self._chat_repository.get_chats_with_archive()

            logger.info("Найдено %d чатов с архивными чатами", len(chats_with_archive))

            if not chats_with_archive:
                logger.warning("Нет чатов с архивными чатами для отправки отчетов")
                return

            # Вычисляем период отчета
            start_date, end_date = TimePeriod.to_datetime(period)

            processed_count = 0
            skipped_count = 0
            error_count = 0

            # Обрабатываем каждый чат
            for chat in chats_with_archive:
                try:
                    # Получаем админов для чата
                    admins = await self._user_repository.get_admins_for_chat(
                        chat_tg_id=chat.chat_id
                    )

                    if not admins:
                        logger.warning(
                            "Чат '%s' (ID: %s) не имеет админов, пропускаем",
                            chat.title,
                            chat.chat_id,
                        )
                        skipped_count += 1
                        continue

                    # Берем первого админа
                    first_admin: User = admins[0]
                    if not first_admin.tg_id:
                        logger.warning(
                            "Админ для чата '%s' не имеет tg_id, пропускаем",
                            chat.title,
                        )
                        skipped_count += 1
                        continue

                    logger.info(
                        "Генерация отчета для чата '%s' (ID: %d) админом %s",
                        chat.title,
                        chat.id,
                        first_admin.tg_id,
                    )

                    # Создаем DTO для отчета
                    report_dto = ChatReportDTO(
                        chat_id=chat.id,
                        admin_tg_id=first_admin.tg_id,
                        start_date=start_date,
                        end_date=end_date,
                        selected_period=period,
                    )

                    # Генерируем отчет
                    report_parts = await self._report_usecase.execute(report_dto)

                    if not report_parts:
                        logger.warning(
                            "Отчет для чата '%s' пуст, пропускаем отправку",
                            chat.title,
                        )
                        skipped_count += 1
                        continue

                    # Отправляем части отчета в архивный чат
                    for part in report_parts:
                        await self._bot_message_service.send_chat_message(
                            chat_tgid=chat.archive_chat_id,
                            text=part,
                        )

                    processed_count += 1
                    logger.info(
                        "Отчет для чата '%s' успешно отправлен в архивный чат %s",
                        chat.title,
                        chat.archive_chat_id,
                    )

                except Exception as e:
                    error_count += 1
                    logger.error(
                        "Ошибка при обработке чата '%s' (ID: %d): %s",
                        chat.title if chat.title else "Unknown",
                        chat.id,
                        e,
                        exc_info=True,
                    )
                    # Продолжаем обработку других чатов
                    continue

            logger.info(
                "Завершена генерация ежедневных отчетов: обработано %d, пропущено %d, ошибок %d",
                processed_count,
                skipped_count,
                error_count,
            )

        except Exception as e:
            logger.error(
                "Критическая ошибка при генерации ежедневных отчетов: %s",
                e,
                exc_info=True,
            )
            raise
