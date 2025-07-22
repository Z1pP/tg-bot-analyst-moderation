import logging
from typing import Any, Dict, Optional

from aiogram.types import Message

from models import MessageTemplate
from repositories import (
    MessageTemplateRepository,
    TemplateMediaRepository,
    UserRepository,
)

logger = logging.getLogger(__name__)


class TemplateContentService:
    """Сервис для работы с контентом шаблонов"""

    def __init__(
        self,
        user_repository: UserRepository,
        template_repository: MessageTemplateRepository,
        media_repository: TemplateMediaRepository,
    ):
        self._user_repository = user_repository
        self._template_repository = template_repository
        self._media_repository = media_repository

    def extract_media_content(self, messages: list[Message]) -> Dict[str, Any]:
        """
        Извлекает контент из сообщений медиа группы
        """
        # Берем первое сообщение для получения текста/подписи
        content = {
            "text": messages[0].html_text or messages[0].caption or "",
            "media_types": [],
            "media_files": [],
            "media_unique_ids": [],
        }

        # Обрабатываем все сообщения для сбора медиа файлов
        for message in messages:
            media_mapping = {
                "photo": (message.photo, lambda x: x[-1]),
                "document": (message.document, lambda x: x),
                "video": (message.video, lambda x: x),
                "animation": (message.animation, lambda x: x),
            }

            for media_type, (media_obj, accessor) in media_mapping.items():
                if media_obj:
                    media = accessor(media_obj)

                    content["media_types"].append(media_type)

                    if media_type in content["media_types"]:
                        content["media_files"].append(media.file_id)
                        content["media_unique_ids"].append(media.file_unique_id)
                    break

        return content

    async def save_template(
        self,
        author_username: str,
        content: Dict[str, Any],
    ) -> Optional[MessageTemplate]:
        """Сохраняет шаблон в базу данных"""
        try:

            user = await self._user_repository.get_user_by_username(
                username=author_username
            )
            if not user:
                raise ValueError("User not found")

            new_template = await self._template_repository.create_template(
                title=content.get("title", "Без названия"),
                content=content.get("text", ""),
                category_id=content.get("category_id"),
                author_id=user.id,
                chat_id=content.get("chat_id"),
            )

            # Сохраняем медиа с привязкой к шаблону
            await self.save_media_files(template_id=new_template.id, content=content)
            return new_template
        except Exception as e:
            logger.error(f"Ошибка сохранения шаблона: {e}", exc_info=True)
            raise

    async def save_media_files(
        self,
        template_id: int,
        content: Dict[str, Any],
    ) -> None:
        """Сохраняет медиа файлы в БД"""
        media_files = content.get("media_files", [])
        media_unique_ids = content.get("media_unique_ids", [])
        media_types = content.get("media_types", [])

        if not media_files or not media_types:
            return

        for position, (file_id, file_unique_id, media_type) in enumerate(
            zip(media_files, media_unique_ids, media_types)
        ):
            try:
                await self._media_repository.create_media(
                    template_id=template_id,
                    media_type=media_type,
                    file_id=file_id,
                    file_unique_id=file_unique_id,
                    position=position,
                )
            except Exception as e:
                logger.error(f"Ошибка сохранения медиа {file_id}: {e}", exc_info=True)
