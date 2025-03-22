from fastapi import APIRouter

from src.api.rolls import router as rolls_router

main_router = APIRouter()

main_router.include_router(rolls_router)