from typing import cast

from fastapi import Depends
from punq import Container

from usecases.message import SaveMessageUseCase

from .container import get_container


def get_save_message_usecase(
    dc: Container = Depends(get_container),
) -> SaveMessageUseCase:
    return cast(SaveMessageUseCase, dc.resolve(SaveMessageUseCase))
