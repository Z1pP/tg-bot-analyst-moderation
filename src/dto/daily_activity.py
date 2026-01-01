from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserDailyActivityDTO(BaseModel):
    user_id: int
    username: str
    message_count: int
    rank: int


class UserReactionActivityDTO(BaseModel):
    user_id: int
    username: str
    reaction_count: int
    rank: int


class PopularReactionDTO(BaseModel):
    emoji: str
    count: int
    rank: int


class ChatDailyStatsDTO(BaseModel):
    chat_id: int
    chat_title: str

    top_users: List[UserDailyActivityDTO]
    top_reactors: List[UserReactionActivityDTO]
    popular_reactions: List[PopularReactionDTO]
    total_messages: int
    total_reactions: int
    active_users_count: int
    start_date: datetime
    end_date: Optional[datetime] = None
    total_users_count: int = 0
