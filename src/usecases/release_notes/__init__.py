"""Use cases для релизных заметок (рассылка текста владельцам и админам)."""

from .broadcast_text_to_admins import BroadcastTextToAdminsUseCase

__all__ = [
    "BroadcastTextToAdminsUseCase",
]
