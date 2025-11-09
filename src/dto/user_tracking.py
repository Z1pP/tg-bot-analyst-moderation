from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserTrackingDTO:
    admin_username: str
    admin_tgid: str
    user_username: str
    user_tgid: str


@dataclass(frozen=True, slots=True)
class RemoveUserTrackingDTO:
    admin_username: str
    admin_tgid: str
    user_id: int
