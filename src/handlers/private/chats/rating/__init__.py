from aiogram import Router

from .rating import router as rating_router

router = Router(name="chat_rating_router")

router.include_router(rating_router)
