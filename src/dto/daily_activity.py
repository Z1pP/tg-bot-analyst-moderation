from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserDailyActivityDTO:
    user_id: int
    username: str
    message_count: int
    rank: int


@dataclass
class ChatDailyStatsDTO:
    chat_id: int
    chat_title: str
    date: datetime
    top_users: list[UserDailyActivityDTO]
    total_messages: int
    active_users_count: int