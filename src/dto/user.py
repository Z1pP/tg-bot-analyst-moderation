from dataclasses import dataclass


@dataclass
class UserDTO:
    tg_id: str
    username: str
