"""Use cases для проверки прав бота в чате."""

from .get_bot_permissions_in_chat import (
    GetBotPermissionsInChatUseCase,
    GetBotPermissionsResult,
)

__all__ = ["GetBotPermissionsInChatUseCase", "GetBotPermissionsResult"]
