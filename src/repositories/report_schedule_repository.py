import logging
from datetime import datetime, time, timedelta, timezone
from typing import List, Optional

import pytz
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.session import DatabaseContextManager
from models import ReportSchedule

logger = logging.getLogger(__name__)


class ReportScheduleRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def get_due_schedules_and_reschedule(self) -> List[ReportSchedule]:
        """
        Находит расписания, готовые к выполнению, блокирует их,
        СРАЗУ обновляет next_run_at на будущее и возвращает список для отправки.
        """
        async with self._db.session() as session:
            try:
                now = datetime.now(timezone.utc)

                # 1. Находим и блокируем записи (SELECT ... FOR UPDATE SKIP LOCKED)
                query = (
                    select(ReportSchedule)
                    .where(
                        ReportSchedule.enabled.is_(True),
                        ReportSchedule.next_run_at.isnot(None),
                        ReportSchedule.next_run_at <= now,
                    )
                    .with_for_update(skip_locked=True)
                )

                result = await session.execute(query)
                schedules = result.scalars().all()

                if not schedules:
                    return []

                logger.info(f"Найдено {len(schedules)} расписаний для обработки.")

                # 2. Обновляем каждое расписание внутри той же транзакции
                results_to_return = []

                for schedule in schedules:
                    # Расчет следующего запуска
                    next_run = self._calculate_next_run(schedule, now)

                    # Обновляем поля
                    schedule.last_run_at = now
                    schedule.next_run_at = next_run

                    # Добавляем в список для возврата (объекты привязаны к сессии,
                    # но мы возьмем нужные данные, пока сессия открыта)
                    results_to_return.append(schedule)

                # 3. Фиксируем изменения (Lock отпускается здесь)
                await session.commit()

                # Обновляем объекты данными из БД (на случай generated values),
                # хотя для отправки ID и chat_id этого обычно не требуется.
                for s in results_to_return:
                    await session.refresh(s)

                return results_to_return

            except Exception as e:
                logger.error(f"Ошибка в шедулере: {e}", exc_info=True)
                await session.rollback()
                return []

    def _calculate_next_run(
        self, schedule: ReportSchedule, now_utc: datetime
    ) -> datetime:
        """
        Чистая функция для расчета следующей даты без обращения к БД.

        Рассчитывает следующее время выполнения на основе текущего времени и
        настроенного времени отправки. Если время еще не прошло сегодня -
        следующее выполнение сегодня, иначе - завтра.

        Гарантирует, что next_run_at будет минимум на 2 минуты в будущем,
        чтобы избежать повторной отправки в следующем тике scheduler (60 сек).
        """
        try:
            schedule_tz = pytz.timezone(schedule.timezone)
            now_in_schedule_tz = now_utc.astimezone(schedule_tz)

            # Рассчитываем время выполнения на сегодня
            today_run_local = schedule_tz.localize(
                datetime.combine(now_in_schedule_tz.date(), schedule.sent_time)
            )

            # Если время еще не прошло сегодня - следующее выполнение сегодня
            if today_run_local > now_in_schedule_tz:
                next_run_local = today_run_local
            else:
                # Время уже прошло - следующее выполнение завтра
                next_run_local = today_run_local + timedelta(days=1)

            # Защита от edge cases: если по какой-то причине next_run_local все еще в прошлом
            # (например, при изменении timezone), сдвигаем дальше
            while next_run_local <= now_in_schedule_tz:
                next_run_local += timedelta(days=1)

            # Конвертируем в UTC для сравнения
            next_run_utc = next_run_local.astimezone(timezone.utc)

            # Гарантируем, что next_run_at будет минимум на 2 минуты в будущем
            # чтобы избежать повторной отправки в следующем тике scheduler (60 сек)
            min_next_run = now_utc + timedelta(minutes=2)
            if next_run_utc <= min_next_run:
                # Если рассчитанное время слишком близко, используем минимальное
                return min_next_run

            return next_run_utc

        except Exception as e:
            logger.error(f"Ошибка расчета времени для {schedule.id}: {e}")
            # Fallback: попробовать через час, чтобы не зациклить
            return now_utc + timedelta(hours=1)

    async def get_schedule(self, chat_id: int) -> Optional[ReportSchedule]:
        """Получает расписание для чата."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(ReportSchedule).where(
                        ReportSchedule.chat_id == chat_id,
                    )
                )
                schedule = result.scalars().first()
                if schedule:
                    logger.info("Получено расписание: chat_id=%s", chat_id)
                return schedule
            except Exception as e:
                logger.error(
                    "Ошибка при получении расписания chat_id=%s: %s",
                    chat_id,
                    e,
                )
                return None

    async def create_schedule(
        self,
        chat_id: int,
        tz_name: str,
        sent_time: time,
        enabled: bool = True,
    ) -> ReportSchedule:
        """Создает новое расписание."""
        async with self._db.session() as session:
            try:
                now_utc = datetime.now(timezone.utc)
                schedule_tz = pytz.timezone(tz_name)
                now_in_schedule_tz = now_utc.astimezone(schedule_tz)

                # Рассчитываем next_run_at
                today_run_local = schedule_tz.localize(
                    datetime.combine(now_in_schedule_tz.date(), sent_time)
                )

                # Если время уже прошло сегодня, следующее выполнение завтра
                if today_run_local <= now_in_schedule_tz:
                    next_run_local = today_run_local + timedelta(days=1)
                else:
                    next_run_local = today_run_local

                # Убеждаемся, что next_run_at в будущем
                while next_run_local <= now_in_schedule_tz:
                    next_run_local += timedelta(days=1)

                next_run_at = next_run_local.astimezone(timezone.utc)

                schedule = ReportSchedule(
                    chat_id=chat_id,
                    timezone=tz_name,
                    sent_time=sent_time,
                    enabled=enabled,
                    next_run_at=next_run_at if enabled else None,
                )

                session.add(schedule)
                await session.commit()
                await session.refresh(schedule)

                logger.info(
                    "Создано расписание: chat_id=%s, time=%s",
                    chat_id,
                    sent_time,
                )
                return schedule
            except IntegrityError as e:
                logger.error(
                    "Ошибка при создании расписания (возможно, уже существует): %s", e
                )
                await session.rollback()
                raise
            except Exception as e:
                logger.error(
                    "Ошибка при создании расписания chat_id=%s: %s",
                    chat_id,
                    e,
                )
                await session.rollback()
                raise

    async def update_schedule(
        self,
        schedule_id: int,
        sent_time: Optional[time] = None,
        enabled: Optional[bool] = None,
        tz_name: Optional[str] = None,
    ) -> Optional[ReportSchedule]:
        """Обновляет расписание."""
        async with self._db.session() as session:
            try:
                schedule = await session.get(ReportSchedule, schedule_id)
                if not schedule:
                    logger.warning("Расписание с id=%s не найдено", schedule_id)
                    return None

                if sent_time is not None:
                    schedule.sent_time = sent_time
                if enabled is not None:
                    schedule.enabled = enabled
                if tz_name is not None:
                    schedule.timezone = tz_name

                # Пересчитываем next_run_at если изменилось время или timezone
                if sent_time is not None or tz_name is not None or enabled is not None:
                    if schedule.enabled:
                        now_utc = datetime.now(timezone.utc)
                        schedule.next_run_at = self._calculate_next_run(
                            schedule, now_utc
                        )
                    else:
                        schedule.next_run_at = None

                await session.commit()
                await session.refresh(schedule)

                logger.info(
                    "Обновлено расписание id=%s: sent_time=%s, enabled=%s",
                    schedule_id,
                    sent_time,
                    enabled,
                )
                return schedule
            except Exception as e:
                logger.error(
                    "Ошибка при обновлении расписания id=%s: %s", schedule_id, e
                )
                await session.rollback()
                raise
