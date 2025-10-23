from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AdminPanelBanDTO:
    """DTO для блокировки пользователя через админ-панель."""

    user_tgid: str
    user_username: str
    admin_tgid: str
    admin_username: str
    chat_tgid: str
    chat_title: str
    reason: str
