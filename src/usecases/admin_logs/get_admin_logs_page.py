"""Use case: получение страницы логов администраторов с форматированием."""

from constants import Dialog
from dto.admin_log import AdminLogPageResultDTO, GetAdminLogsPageDTO
from exceptions import AdminLogsError
from keyboards.inline.admin_logs import format_action_type
from repositories import AdminActionLogRepository
from services.time_service import TimeZoneService


class GetAdminLogsPageUseCase:
    """Возвращает страницу логов с готовыми строками для отображения."""

    def __init__(self, log_repository: AdminActionLogRepository) -> None:
        self._log_repository = log_repository

    async def execute(self, dto: GetAdminLogsPageDTO) -> AdminLogPageResultDTO:
        """Загружает страницу логов, форматирует и возвращает DTO."""
        try:
            return await self._execute(dto)
        except AdminLogsError:
            raise
        except Exception:
            raise AdminLogsError(message=Dialog.AdminLogs.ERROR_GET_LOGS)

    async def _execute(self, dto: GetAdminLogsPageDTO) -> AdminLogPageResultDTO:
        """Внутренняя реализация без обработки исключений."""
        if dto.admin_id is None:
            logs, total_count = await self._log_repository.get_logs_paginated(
                page=dto.page, limit=dto.limit
            )
            header_text = Dialog.AdminLogs.ALL_ADMINS_LOGS
        else:
            logs, total_count = await self._log_repository.get_logs_by_admin(
                admin_id=dto.admin_id,
                page=dto.page,
                limit=dto.limit,
            )
            if logs:
                admin_username = (
                    logs[0].admin.username
                    if logs[0].admin.username
                    else f"ID:{logs[0].admin.tg_id}"
                )
                header_text = Dialog.AdminLogs.ADMIN_LOGS_FORMAT.format(
                    username=admin_username
                )
            else:
                header_text = Dialog.AdminLogs.ADMIN_LOGS_FORMAT.format(
                    username="неизвестен"
                )

        entry_lines: list[str] = []
        for log in logs:
            admin_username = (
                log.admin.username if log.admin.username else f"ID:{log.admin.tg_id}"
            )
            action_name = format_action_type(log.action_type)
            local_time = TimeZoneService.convert_to_local_time(log.created_at)
            time_str = local_time.strftime("%d.%m.%Y %H:%M")
            entry_lines.append(
                f"• {action_name}\n  Админ: @{admin_username}\n  Дата: {time_str}"
            )
            if log.details:
                entry_lines.append(f"  {log.details}")
            entry_lines.append("")

        return AdminLogPageResultDTO(
            header_text=header_text,
            entry_lines=entry_lines,
            total_count=total_count,
        )
