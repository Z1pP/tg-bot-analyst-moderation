from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException

from api.dependencies.message import get_save_message_usecase
from dto.message import CreateMessageDTO as CreateMessageSchema
from exceptions.base import BotBaseException
from usecases.message import SaveMessageUseCase

router = APIRouter()


@router.post("/create", status_code=status.HTTP_202_ACCEPTED)
async def create_message(
    message: CreateMessageSchema,
    usecase: SaveMessageUseCase = Depends(get_save_message_usecase),
) -> Response:
    try:
        await usecase.execute(message)
        return Response(status_code=status.HTTP_202_ACCEPTED)
    except BotBaseException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.get_user_message(),
        )
    # Остальные исключения пробрасываем — обработает глобальный handler или FastAPI
