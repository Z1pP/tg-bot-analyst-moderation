from typing import cast

from fastapi import Depends
from punq import Container

from container import container
from usecases.message import SaveMessageUseCase


def get_container() -> Container:
    return container


def get_save_message_usecase(
    dc: Container = Depends(get_container),
) -> SaveMessageUseCase:
    return cast(SaveMessageUseCase, dc.resolve(SaveMessageUseCase))
