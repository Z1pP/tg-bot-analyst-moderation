import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import router as v1_router
from container import ContainerSetup
from utils.logger_config import setup_logger

setup_logger(log_level=logging.INFO)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    ContainerSetup.setup()
    logger.info("ContainerSetup setup")
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

    return app


app = create_app()
