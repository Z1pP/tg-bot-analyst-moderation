from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserDailyActivityDTO:
    user_id: int
    username: str
    message_count: int
    rank: int


@dataclass
class UserReactionActivityDTO:
    user_id: int
    username: str
    reaction_count: int
    rank: int


@dataclass
class PopularReactionDTO:
    emoji: str
    count: int
    rank: int


@dataclass
class ChatDailyStatsDTO:
    chat_id: int
    chat_title: str
    date: datetime
    top_users: list[UserDailyActivityDTO]
    top_reactors: list[UserReactionActivityDTO]
    popular_reactions: list[PopularReactionDTO]
    total_messages: int
    total_reactions: int
    active_users_count: int
