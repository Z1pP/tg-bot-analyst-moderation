from abc import ABC, abstractmethod
from dataclasses import dataclass

from constants.enums import SummaryType


@dataclass(frozen=True, slots=True)
class SummaryResult:
    """Result of a summary generation request."""

    status_code: int
    summary: str


class IAIService(ABC):
    """Absrtract class for summarize chat messages"""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    @abstractmethod
    async def summarize_text(
        self,
        text: str,
        msg_count: int,
        summary_type: SummaryType,
        tracked_users: list[str],
    ) -> SummaryResult:
        pass
