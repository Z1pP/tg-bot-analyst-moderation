from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException

from api.dependencies.message import get_save_message_usecase
from dto.message import CreateMessageDTO
from usecases.message import SaveMessageUseCase

router = APIRouter()


@router.post("/create", status_code=status.HTTP_202_ACCEPTED)
async def create_message(
    message: CreateMessageDTO,
    usecase: SaveMessageUseCase = Depends(get_save_message_usecase),
) -> Response:
    try:
        await usecase.execute(message)
        return Response(status_code=status.HTTP_202_ACCEPTED)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
            headers={"X-Error": "Internal Server Error"},
        )
