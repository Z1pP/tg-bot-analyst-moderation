import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from services.caching import ICache
from services.caching.redis import RedisCache

logger = logging.getLogger(__name__)

# Лимиты антиспама
WARNING_THRESHOLD = 10  # сообщений за 10 секунд
MUTE_30_SEC_THRESHOLD = 15  # сообщений за 10 секунд
MUTE_10_MIN_THRESHOLD = 20  # сообщений за 10 секунд

WINDOW_SECONDS = 10  # окно времени для подсчета
MUTE_30_SECONDS = 30  # длительность первого мута
MUTE_10_MINUTES = 600  # длительность второго мута


class AdminAntispamMiddleware(BaseMiddleware):
    """
    Middleware для защиты от спама сообщений от администраторов.

    Логика работы:
    - 10 сообщений за 10 секунд → предупреждение
    - 15 сообщений за 10 секунд → мут 30 секунд
    - 20 сообщений за 10 секунд → мут 10 минут
    """

    def __init__(self, cache: ICache):
        self.cache = cache
        # Проверяем, что cache является RedisCache для использования новых методов
        if not isinstance(cache, RedisCache):
            logger.warning(
                "AdminAntispamMiddleware получил cache, который не является RedisCache. "
                "Некоторые функции могут не работать."
            )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обрабатывает входящее сообщение от администратора.

        Args:
            handler: Следующий обработчик в цепочке
            event: Входящее сообщение
            data: Данные контекста

        Returns:
            Результат выполнения обработчика или None, если сообщение заблокировано
        """
        if not isinstance(event, Message) or event.from_user is None:
            return await handler(event, data)

        admin_id = event.from_user.id
        mute_key = f"antispam:mute:{admin_id}"
        count_key = f"antispam:count:{admin_id}"

        # Проверяем, не находится ли админ в муте
        if isinstance(self.cache, RedisCache):
            is_muted = await self.cache.exists(mute_key)
            if is_muted:
                logger.debug(
                    f"Сообщение от админа {admin_id} заблокировано (мут активен)"
                )
                return None  # Игнорируем сообщение
        else:
            # Fallback: проверяем через get
            mute_value: Any = await self.cache.get(mute_key)
            if mute_value is not None:
                logger.debug(
                    f"Сообщение от админа {admin_id} заблокировано (мут активен)"
                )
                return None

        # Инкрементируем счетчик сообщений
        if isinstance(self.cache, RedisCache):
            count = await self.cache.increment(count_key, ttl=WINDOW_SECONDS)
        else:
            # Fallback: используем get/set
            current_count: Any = await self.cache.get(count_key)
            if current_count is None:
                count = 1
                await self.cache.set(count_key, count, ttl=WINDOW_SECONDS)
            else:
                count = int(current_count) + 1
                await self.cache.set(count_key, count, ttl=WINDOW_SECONDS)

        logger.debug(f"Админ {admin_id} отправил сообщение. Счетчик: {count}")

        # Проверяем лимиты и применяем соответствующие действия
        if count >= MUTE_10_MIN_THRESHOLD:
            # Мут на 10 минут
            await self._apply_mute(event, MUTE_10_MINUTES)
            logger.warning(
                f"Админ {admin_id} получил мут на 10 минут ({count} сообщений за {WINDOW_SECONDS} сек)"
            )
            return None  # Игнорируем сообщение
        elif count >= MUTE_30_SEC_THRESHOLD:
            # Мут на 30 секунд
            await self._apply_mute(event, MUTE_30_SECONDS)
            logger.warning(
                f"Админ {admin_id} получил мут на 30 секунд ({count} сообщений за {WINDOW_SECONDS} сек)"
            )
            return None  # Игнорируем сообщение
        elif count >= WARNING_THRESHOLD:
            # Предупреждение
            await self._send_warning(event)
            logger.info(
                f"Админ {admin_id} получил предупреждение ({count} сообщений за {WINDOW_SECONDS} сек)"
            )

        # Пропускаем сообщение дальше по цепочке
        return await handler(event, data)

    async def _apply_mute(self, message: Message, duration_seconds: int) -> None:
        """
        Применяет мут к администратору и отправляет предупреждение.

        Args:
            message: Сообщение от администратора
            duration_seconds: Длительность мута в секундах
        """
        admin_id = message.from_user.id if message.from_user else None
        mute_key = f"antispam:mute:{admin_id}"
        await self.cache.set(mute_key, True, ttl=duration_seconds)
        logger.debug(f"Мут применен к админу {admin_id} на {duration_seconds} секунд")

        # Отправляем предупреждение о муте
        await self._send_mute_warning(message, duration_seconds)

    async def _send_mute_warning(self, message: Message, duration_seconds: int) -> None:
        """
        Отправляет предупреждение администратору о том, что он в муте.

        Args:
            message: Сообщение, на которое нужно ответить
            duration_seconds: Длительность мута в секундах
        """
        admin_id = message.from_user.id if message.from_user else None
        try:
            # Форматируем длительность мута
            if duration_seconds >= 60:
                duration_text = f"{duration_seconds // 60} минут"
            else:
                duration_text = f"{duration_seconds} секунд"

            mute_text = (
                f"🔇 Вы получили мут на {duration_text} из-за слишком частых сообщений.\n"
                f"Ваши сообщения будут игнорироваться до окончания мута."
            )
            await message.reply(mute_text)
        except Exception as e:
            logger.error(
                f"Не удалось отправить предупреждение о муте админу {admin_id}: {e}"
            )

    async def _send_warning(self, message: Message) -> None:
        """
        Отправляет предупреждение администратору.

        Args:
            message: Сообщение, на которое нужно ответить
        """
        admin_id = message.from_user.id if message.from_user else None
        try:
            warning_text = "⚠️ Слишком много сообщений! Пожалуйста, замедлите темп."
            await message.reply(warning_text)
        except Exception as e:
            logger.error(
                f"Не удалось отправить предупреждение админу {admin_id}: {e}"
            )
