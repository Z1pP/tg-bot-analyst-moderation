"""Use case: получение списка администраторов, у которых есть логи."""

from constants import Dialog
from dto.admin_log import AdminWithLogsDTO
from exceptions import AdminLogsError
from repositories import AdminActionLogRepository


class GetAdminsWithLogsUseCase:
    """Возвращает список администраторов с логами для выбора в меню."""

    def __init__(self, log_repository: AdminActionLogRepository) -> None:
        self._log_repository = log_repository

    async def execute(self) -> list[AdminWithLogsDTO]:
        """Возвращает список администраторов (id, username_display, tg_id)."""
        try:
            raw = await self._log_repository.get_admins_with_logs()
            return [
                AdminWithLogsDTO(
                    id=admin_id,
                    username_display=username_display,
                    tg_id=str(tg_id),
                )
                for admin_id, username_display, tg_id in raw
            ]
        except AdminLogsError:
            raise
        except Exception:
            raise AdminLogsError(message=Dialog.AdminLogs.ERROR_GET_ADMINS)
