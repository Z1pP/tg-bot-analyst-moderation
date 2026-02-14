"""Use cases для просмотра логов администраторов."""

from usecases.admin_logs.get_admin_logs_page import GetAdminLogsPageUseCase
from usecases.admin_logs.get_admins_with_logs import GetAdminsWithLogsUseCase

__all__ = [
    "GetAdminLogsPageUseCase",
    "GetAdminsWithLogsUseCase",
]
