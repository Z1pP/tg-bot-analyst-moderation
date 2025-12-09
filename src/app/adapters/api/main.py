from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.api.dependencies.auth import ServiceAuth
from app.adapters.api.routers.internal import router as internal_router
from app.adapters.api.routers.v1 import router as v1_router


def create_app() -> FastAPI:
    app = FastAPI(title="tg-bot-analyst", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Публичные/клиентские v1 эндпоинты
    app.include_router(router=v1_router, prefix="/api")

    # Служебные internal эндпоинты
    app.include_router(
        router=internal_router,
        prefix="/api",
        dependencies=[Depends(ServiceAuth)],
    )

    return app


app = create_app()
