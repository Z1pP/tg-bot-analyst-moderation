from abc import ABC, abstractmethod


class IAIService(ABC):
    """Absrtract class for summarize chat messages"""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    @abstractmethod
    async def summarize_text(self, text: str, msg_count: int) -> str:
        pass
