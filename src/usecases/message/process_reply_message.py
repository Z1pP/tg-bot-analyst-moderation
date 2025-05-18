from datetime import datetime, time, timedelta

from constants.work_time import TOLERANCE, WORK_END, WORK_START
from dto.message_reply import CreateMessageReplyDTO
from repositories.message_reply_repository import MessageReplyRepository


class ProcessReplyMessageUseCase:
    def __init__(self, msg_reply_repository: MessageReplyRepository):
        self._msg_reply_repository = msg_reply_repository

    async def execute(self, reply_message_dto: CreateMessageReplyDTO):
        """
        Сохраняет связь между reply-сообщением и оригинальным сообщением,
        если сообщения созданы в один день и в рабочее время.
        """
        if self._should_save_reply(reply_message_dto):
            await self._msg_reply_repository.create_reply_message(dto=reply_message_dto)

    def _should_save_reply(self, dto: CreateMessageReplyDTO) -> bool:
        """
        Проверяет, нужно ли сохранять reply-сообщение.

        Условия:
        1. Оригинальное сообщение и ответ должны быть созданы в один день
        2. Время создания должно входить в рабочее время с учетом допустимого отклонения

        Returns:
            bool: True если сообщение нужно сохранить, False в противном случае
        """
        # Проверяем, что сообщения созданы в один день
        if dto.original_message_date.date() != dto.reply_message_date.date():
            return False

        # Проверяем, что оригинальное сообщение создано в рабочее время
        if not self._is_working_time(dto.original_message_date.time()):
            return False

        # Проверяем, что ответ создан в рабочее время
        if not self._is_working_time(dto.reply_message_date.time()):
            return False

        return True

    def _is_working_time(self, current_time: time) -> bool:
        """
        Проверяет, входит ли время в рабочие часы с учетом допустимого отклонения.
        """
        # Вычисляем границы рабочего времени с учетом допуска
        start_with_tolerance = self._adjust_time_with_tolerance(WORK_START, -TOLERANCE)
        end_with_tolerance = self._adjust_time_with_tolerance(WORK_END, TOLERANCE)

        # Проверяем, входит ли время в диапазон
        return start_with_tolerance <= current_time <= end_with_tolerance

    def _adjust_time_with_tolerance(self, base_time: time, delta: timedelta) -> time:
        """
        Корректирует время с учетом допуска.
        """
        # Преобразуем time в datetime для выполнения арифметических операций
        dt = datetime.combine(datetime.today(), base_time)
        # Применяем смещение
        adjusted_dt = dt + delta
        # Возвращаем только компонент времени
        return adjusted_dt.time()
