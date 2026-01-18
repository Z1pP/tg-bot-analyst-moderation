from fastapi import Depends
from punq import Container

from container import container
from usecases.message import SaveMessageUseCase


def get_contaner() -> Container:
    return container


def get_save_message_usecase(
    dc: Container = Depends(get_contaner),
) -> SaveMessageUseCase:
    return dc.resolve(SaveMessageUseCase)
