from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserTrackingDTO(BaseModel):
    admin_username: Optional[str]
    admin_tgid: str
    user_username: Optional[str] = None
    user_tgid: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class RemoveUserTrackingDTO(BaseModel):
    admin_username: Optional[str]
    admin_tgid: str
    user_id: int

    model_config = ConfigDict(frozen=True)
