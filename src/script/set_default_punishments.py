import asyncio
import logging

from database.session import async_session
from models.punishment_ladder import PunishmentLadder, PunishmentType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def set_default_punishments():
    """
    Создает и сохраняет в базу данных дефолтную (глобальную) лестницу наказаний.
    """
    punishments_data = [
        {
            "step": 1,
            "type": PunishmentType.WARNING,
            "duration": 0,
            "comment": "Предупреждение",
        },
        {
            "step": 2,
            "type": PunishmentType.MUTE,
            "duration": 3600,
            "comment": "Мут на 1 час",
        },
        {
            "step": 3,
            "type": PunishmentType.MUTE,
            "duration": 86400,
            "comment": "Мут на 1 день",
        },
        {
            "step": 4,
            "type": PunishmentType.MUTE,
            "duration": 259200,
            "comment": "Мут на 3 дня",
        },
        {
            "step": 5,
            "type": PunishmentType.MUTE,
            "duration": 604800,
            "comment": "Мут на 1 неделю",
        },
        {
            "step": 6,
            "type": PunishmentType.MUTE,
            "duration": 1209600,
            "comment": "Мут на 2 недели",
        },
        {
            "step": 7,
            "type": PunishmentType.MUTE,
            "duration": 2592000,
            "comment": "Мут на 1 месяц",
        },
        {"step": 8, "type": PunishmentType.BAN, "duration": None, "comment": "Бан"},
    ]

    async with async_session() as session:
        for p_data in punishments_data:
            punishment = PunishmentLadder(
                step=p_data["step"],
                punishment_type=p_data["type"],
                duration_seconds=p_data["duration"],
                chat_id=None,  # chat_id=None означает, что наказание глобальное
            )
            session.add(punishment)
            logger.info(f"Добавлено наказание: {p_data['comment']}")

        await session.commit()
        logger.info("Все дефолтные наказания успешно сохранены.")


if __name__ == "__main__":
    logger.info("Запуск скрипта для установки дефолтных наказаний...")
    asyncio.run(set_default_punishments())
