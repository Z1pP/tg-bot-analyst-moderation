"""DTO для уведомлений в архивный чат."""

from pydantic import BaseModel, ConfigDict


class ArchiveMemberNotificationDTO(BaseModel):
    """
    DTO для уведомления в архивный чат о действии с участником
    (новый участник, выход, кик).
    """

    chat_tgid: str
    user_tgid: int
    username: str
    chat_title: str

    model_config = ConfigDict(frozen=True)
