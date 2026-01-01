from pydantic import BaseModel, ConfigDict


class UserTrackingDTO(BaseModel):
    admin_username: str
    admin_tgid: str
    user_username: str
    user_tgid: str

    model_config = ConfigDict(frozen=True)


class RemoveUserTrackingDTO(BaseModel):
    admin_username: str
    admin_tgid: str
    user_id: int

    model_config = ConfigDict(frozen=True)
