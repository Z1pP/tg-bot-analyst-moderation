from dataclasses import dataclass
from typing import Optional


@dataclass
class UserData:
    username: Optional[str] = None
    tg_id: Optional[str] = None


def parse_data_from_text(text: str) -> Optional[UserData]:
    """
    Функция для парсинга введенной информации о пользователе
    """
    if text.startswith("@"):
        username = text[1:]
        return UserData(username=username)

    if text.isdigit():
        tg_id = text
        return UserData(tg_id=tg_id)

    return None
