"""Утилита извлечения контента шаблона из сообщений (для использования в хендлерах)."""

from typing import Any, Dict, List

from aiogram.types import Message


def extract_media_content_from_messages(messages: List[Message]) -> Dict[str, Any]:
    """
    Извлекает контент из сообщений (в т.ч. медиа-группы) в словарь для сохранения шаблона.
    Не обращается к БД — только парсинг Telegram-типов.
    """
    content: Dict[str, Any] = {
        "text": messages[0].html_text or messages[0].caption or "",
        "media_types": [],
        "media_files": [],
        "media_unique_ids": [],
    }

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
                content["media_files"].append(media.file_id)
                content["media_unique_ids"].append(media.file_unique_id)
                break

    return content
