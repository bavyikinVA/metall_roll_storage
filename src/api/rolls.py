from fastapi import HTTPException, APIRouter, Query
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from sqlalchemy import select, and_
from typing import Optional
from src.api.dependencies import SessionDep
from src.database import async_engine, Base
from src.schemas import schemas
from src.api import crud
from src.models.models import MetalRoll


router = APIRouter()


@router.post("/setup/",
             summary="Создание базы данных для рулонов",
             tags=["SETUP"])
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # очищаем бд
        await conn.run_sync(Base.metadata.create_all) # создаем новую


@router.get("/rolls/",
            response_model=list[schemas.MetalRoll],
            summary="Получить все объекты с фильтрацией",
            tags=["GET"])
async def get_rolls(
    session: SessionDep,
    min_length: float = Query(None, description="Минимальная длина рулона"),
    max_length: float = Query(None, description="Максимальная длина рулона"),
    min_weight: float = Query(None, description="Минимальный вес рулона"),
    max_weight: float = Query(None, description="Максимальный вес рулона"),
    start_date: datetime = Query(None, description="Начальная дата добавления"),
    end_date: datetime = Query(None, description="Конечная дата добавления"),
    ):
    if min_length is not None and max_length is not None and min_length > max_length:
        raise HTTPException(
            status_code=400,
            detail="Минимальная длина не может быть больше максимальной",
        )

    if min_weight is not None and max_weight is not None and min_weight > max_weight:
        raise HTTPException(
            status_code=400,
            detail="Минимальный вес не может быть больше максимального",
        )

    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Начальная дата не может быть позже конечной",
        )

    query = select(MetalRoll)

    # добавление фильтров, если они есть
    filters = []
    if min_length is not None:
        filters.append(MetalRoll.length >= min_length)
    if max_length is not None:
        filters.append(MetalRoll.length <= max_length)
    if min_weight is not None:
        filters.append(MetalRoll.weight >= min_weight)
    if max_weight is not None:
        filters.append(MetalRoll.weight <= max_weight)
    if start_date is not None:
        filters.append(MetalRoll.added_date >= start_date)
    if end_date is not None:
        filters.append(MetalRoll.added_date <= end_date)
    else:
        end_date = datetime.now()
        filters.append(MetalRoll.added_date <= end_date)

    # применение фильтров, если они есть
    if filters:
        query = query.where(and_(*filters))

    try:
        result = await session.execute(query)
        rolls = result.scalars().all()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=505,
            detail="Ошибка при выполнении запроса к базе данных",
        )
    # обработка в случае пустого результата
    if not rolls:
        raise HTTPException(
            status_code=404,
            detail="Рулоны по заданным фильтрам не найдены",
        )
    return rolls


@router.get("/rolls/{roll_id}",
         response_model=schemas.MetalRoll,
         summary="Получить конкретный объект",
         tags=["GET"])
async def get_roll(roll_id: int, session: SessionDep) -> schemas.MetalRoll:
    roll = await crud.get_metal_roll(session, roll_id)
    if not roll:
        raise HTTPException(status_code=404, detail="Рулон не найден")
    return roll


@router.post("/rolls/",
          response_model=schemas.MetalRoll,
          summary="Добавить объект",
          tags=["UPDATE"])
async def create_roll(roll: schemas.MetalRoll, session: SessionDep):
    return await crud.create_metal_roll(session, roll)


@router.delete("/rolls/{roll_id}",
            response_model=schemas.MetalRoll,
            summary="Удалить объект по ID",
            tags=["DELETE"])
async def delete_roll(roll_id: int, session : SessionDep) -> schemas.MetalRoll:
    db_roll = await crud.delete_metal_roll(session, roll_id)
    if db_roll is None:
        raise HTTPException(status_code=404, detail="Рулон не найден")
    return db_roll


@router.get("/stats/",
         response_model=schemas.StatisticsResponse,
         summary="Статистика по заданному временному диапазону",
         tags=["GET"])
async def get_stats(session: SessionDep, start_date: datetime,end_date: Optional[datetime]=None):
    if end_date is None:
        end_date = datetime.now()

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Начальная дата не может быть позже конечной")
    try:
        stats = await crud.get_roll_statistics(session, start_date, end_date)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статистики: {str(e)}")
    return stats