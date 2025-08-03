from dto import MessageReactionDTO
from models import MessageReaction
from repositories import MessageReactionRepository


class SaveMessageReactionUseCase:
    def __init__(self, reaction_repository: MessageReactionRepository):
        self._reaction_repository = reaction_repository

    async def execute(self, reaction_dto: MessageReactionDTO) -> MessageReaction:
        return await self._reaction_repository.add_reaction(dto=reaction_dto)
