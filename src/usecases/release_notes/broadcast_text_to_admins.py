"""Use case: рассылка произвольного текста владельцам и админам по языку интерфейса."""

from dto.release_note import BroadcastRecipientDTO, BroadcastTextDTO
from repositories import UserRepository


class BroadcastTextToAdminsUseCase:
    """Возвращает список получателей (chat_id, text) для рассылки без сохранения заметки в БД."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, dto: BroadcastTextDTO) -> list[BroadcastRecipientDTO]:
        """Возвращает список (chat_id, text) для пользователей OWNER и ADMIN с заданным языком."""
        language = dto.language.split("-")[0].lower() if dto.language else "ru"
        users = await self._user_repository.get_owners_and_admins(language=language)
        recipients: list[BroadcastRecipientDTO] = []
        for user in users:
            if not user.tg_id:
                continue
            try:
                chat_id = int(user.tg_id)
            except (ValueError, TypeError):
                continue
            recipients.append(BroadcastRecipientDTO(chat_id=chat_id, text=dto.text))
        return recipients
