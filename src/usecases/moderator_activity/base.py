from abc import ABC, abstractmethod
from typing import Optional

from models import ChatMessage, ModeratorActivity, User


class BaseModeratorActivityTrackerUseCase(ABC):
    @abstractmethod
    async def track(
        self,
        user: User,
        message: ChatMessage,
        *args,
        **kwargs,
    ) -> Optional[ModeratorActivity]:
        pass
