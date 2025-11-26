import base64
import hashlib
import hmac
from typing import Optional

from config import settings


class ArchiveBindService:
    """Сервис для генерации и валидации hash для привязки архивных чатов."""

    def __init__(self):
        self.secret_key = settings.BOT_TOKEN

    def generate_bind_hash(self, chat_id: int) -> str:
        """
        Генерирует уникальный hash для привязки архивного чата.

        Формат: ARCHIVE-{base64_urlsafe(chat_id:timestamp)}_{hmac_8_chars}

        Args:
            chat_id: ID рабочего чата из БД

        Returns:
            Hash в формате ARCHIVE-{encoded_data}_{hmac}
        """
        import time

        timestamp = int(time.time())
        message = f"{chat_id}:{timestamp}"

        # Кодируем данные в base64
        encoded_data = base64.urlsafe_b64encode(message.encode()).decode().rstrip("=")

        # Генерируем HMAC для проверки подлинности
        hmac_hash = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()[:8]

        return f"ARCHIVE-{encoded_data}_{hmac_hash}"

    def extract_chat_id(self, bind_hash: str) -> Optional[int]:
        """
        Извлекает и валидирует chat_id из hash.

        Args:
            bind_hash: Hash в формате ARCHIVE-{encoded_data}_{hmac}

        Returns:
            chat_id если hash валиден, иначе None
        """
        try:
            # Убираем префикс ARCHIVE-
            if not bind_hash.startswith("ARCHIVE-"):
                return None

            hash_part = bind_hash[8:]  # Убираем "ARCHIVE-"
            parts = hash_part.split("_", 1)

            if len(parts) != 2:
                return None

            encoded_data, received_hmac = parts

            # Восстанавливаем padding для base64
            padding = 4 - len(encoded_data) % 4
            if padding != 4:
                encoded_data += "=" * padding

            # Декодируем данные
            decoded = base64.urlsafe_b64decode(encoded_data).decode()
            chat_id_str, timestamp_str = decoded.split(":")

            # Проверяем HMAC
            message = f"{chat_id_str}:{timestamp_str}"
            expected_hmac = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256,
            ).hexdigest()[:8]

            if received_hmac != expected_hmac:
                return None

            return int(chat_id_str)

        except (ValueError, IndexError, TypeError):
            return None
