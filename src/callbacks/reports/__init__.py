from aiogram import Router

from .detailed_report import router as detailed_report_router

router = Router(name="reports_callback")

router.include_router(detailed_report_router)
