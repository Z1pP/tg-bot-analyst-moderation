"""Use case: получение сырой страницы логов администраторов для API."""

from dto.admin_log import AdminLogItemDTO, AdminLogsPageResultDTO, GetAdminLogsPageDTO
from repositories import AdminActionLogRepository


class GetModerationLogsUseCase:
    """Возвращает страницу логов администраторов в виде DTO для Mini App."""

    def __init__(self, log_repository: AdminActionLogRepository) -> None:
        self._log_repository = log_repository

    async def execute(self, dto: GetAdminLogsPageDTO) -> AdminLogsPageResultDTO:
        """Загружает страницу логов и преобразует записи в DTO."""
        logs, total = await self._log_repository.get_logs_paginated(
            page=dto.page,
            limit=dto.limit,
        )
        items = [
            AdminLogItemDTO(
                id=log.id,
                action_type=log.action_type,
                details=log.details,
                admin_username=log.admin.username if log.admin else None,
                admin_tg_id=log.admin.tg_id if log.admin else None,
                created_at=log.created_at,
            )
            for log in logs
        ]
        return AdminLogsPageResultDTO(
            items=items,
            total=total,
            page=dto.page,
            limit=dto.limit,
        )