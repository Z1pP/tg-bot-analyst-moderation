"""Middleware для определения и сохранения языка пользователя"""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from constants.i18n import DEFAULT_LANGUAGE
from container import container
from services.user import UserService

logger = logging.getLogger(__name__)


class LanguageMiddleware(BaseMiddleware):
    """
    Middleware для определения языка пользователя и сохранения его в базе данных.

    Определяет язык из:
    1. Поля language в модели User (если пользователь существует в БД)
    2. language_code из Telegram (если пользователь новый)
    3. DEFAULT_LANGUAGE, если язык не определен
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обрабатывает событие и определяет язык пользователя.

        Args:
            handler: Следующий обработчик в цепочке
            event: Входящее событие (Message или CallbackQuery)
            data: Данные контекста

        Returns:
            Результат выполнения обработчика
        """
        # Получаем пользователя из события
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if not user:
            return await handler(event, data)

        # Определяем язык пользователя
        language = await self._get_user_language(user)

        # Сохраняем язык в контексте для использования в обработчиках
        data["user_language"] = language

        return await handler(event, data)

    async def _get_user_language(self, telegram_user) -> str:
        """
        Получает язык пользователя из базы данных или определяет его из Telegram.

        Args:
            telegram_user: Объект пользователя из Telegram

        Returns:
            Код языка пользователя
        """
        tg_id = str(telegram_user.id)

        try:
            # Получаем пользователя из БД
            db_user = await self.user_service.get_user(tg_id=tg_id)

            if db_user and db_user.language:
                # Используем язык из БД
                return db_user.language

            # Если пользователя нет в БД или у него нет языка, определяем из Telegram
            telegram_language = telegram_user.language_code

            if telegram_language:
                # Нормализуем язык (например, 'en-US' -> 'en')
                language = telegram_language.split("-")[0].lower()

                # Проверяем, поддерживается ли язык (пока только ru и en)
                if language not in ["ru", "en"]:
                    language = DEFAULT_LANGUAGE
            else:
                language = DEFAULT_LANGUAGE

            # Сохраняем язык в БД
            if db_user:
                # Обновляем язык существующего пользователя
                await self._update_user_language(db_user, language)
            else:
                # Создаем пользователя с определенным языком
                try:
                    await self.user_service.create_user(
                        tg_id=tg_id, username=telegram_user.username, language=language
                    )
                except Exception as e:
                    logger.warning(
                        f"Не удалось создать пользователя {tg_id} с языком {language}: {e}"
                    )

            return language

        except Exception as e:
            logger.error(
                f"Ошибка при определении языка пользователя {tg_id}: {e}",
                exc_info=True,
            )
            return DEFAULT_LANGUAGE

    async def _update_user_language(self, user, language: str) -> None:
        """
        Обновляет язык пользователя в базе данных.

        Args:
            user: Объект пользователя из БД
            language: Код языка для сохранения
        """
        try:
            from database.session import DatabaseContextManager
            from repositories import UserRepository

            db_manager: DatabaseContextManager = container.resolve(
                DatabaseContextManager
            )
            user_repo = UserRepository(db_manager)

            await user_repo.update_user_language(user.id, language)
            logger.debug(f"Язык пользователя {user.tg_id} обновлен на {language}")
        except Exception as e:
            logger.error(
                f"Ошибка при обновлении языка пользователя {user.tg_id}: {e}",
                exc_info=True,
            )
