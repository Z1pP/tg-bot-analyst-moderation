from fastapi import APIRouter

from config import settings

router = APIRouter()


@router.get("/")
async def health_check() -> dict[str, str]:
    return {"status v1": "ok"}


@router.get("/config")
async def get_public_config() -> dict[str, str]:
    """Публичный эндпоинт для получения конфигурации фронтенда (API URL)."""
    return {"api_url": settings.PUBLIC_URL}
