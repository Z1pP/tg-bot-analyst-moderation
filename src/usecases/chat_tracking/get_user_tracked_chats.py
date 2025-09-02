import logging

from dto import ChatDTO, UserChatsDTO
from repositories import ChatTrackingRepository
from services.user import UserService

logger = logging.getLogger(__name__)


class GetUserTrackedChatsUseCase:
    def __init__(
        self,
        chat_tracking_repository: ChatTrackingRepository,
        user_service: UserService,
    ):
        self.chat_tracking_repository = chat_tracking_repository
        self.user_service = user_service

    async def execute(self, tg_id: str) -> UserChatsDTO:
        """
        Получает список отслеживаемых чатов пользователя.

        Args:
            tg_id: Telegram ID пользователя

        Returns:
            UserChatsDTO: Данные о чатах пользователя
        """
        try:
            # Получаем пользователя
            user = await self.user_service.get_user(tg_id=tg_id)
            if not user:
                logger.error(f"Пользователь с tg_id={tg_id} не найден")
                return UserChatsDTO(chats=[], user_id=0, total_count=0)

            tracked_chats = await self.chat_tracking_repository.get_all_tracked_chats(
                admin_id=user.id
            )

            # Преобразуем модели в DTO
            chat_dtos = [ChatDTO.from_model(chat) for chat in tracked_chats]

            logger.debug(
                f"Найдено {len(chat_dtos)} отслеживаемых чатов для user_id={user.id}"
            )

            return UserChatsDTO(
                chats=chat_dtos, user_id=user.id, total_count=len(chat_dtos)
            )

        except Exception as e:
            logger.error(f"Ошибка при получении отслеживаемых чатов: {e}")
            raise
