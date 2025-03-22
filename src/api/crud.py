from sqlalchemy.exc import SQLAlchemyError
from src.schemas import schemas
from src.api.dependencies import SessionDep
from sqlalchemy import func, or_, select
from src.models.models import MetalRoll
from datetime import datetime, timedelta
from fastapi import HTTPException, APIRouter

router = APIRouter()


async def create_metal_roll(session: SessionDep, metal_roll: schemas.MetalRoll):
    if metal_roll.length <= 0 or metal_roll.weight <= 0:
        raise HTTPException(status_code=422, detail="Длина и вес должны быть положительными числами")
    db_metal_roll = MetalRoll(
        length=metal_roll.length,
        weight=metal_roll.weight,
        added_date=datetime.now()
    )
    try:
        session.add(db_metal_roll)
        await session.commit()

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Ошибка при сохранении рулона в базу данных",
        )

    return db_metal_roll


async def delete_metal_roll(session: SessionDep, roll_id: int):
    result = await session.execute(
        select(MetalRoll).where(MetalRoll.id == roll_id)
    )
    db_roll = result.scalar_one_or_none()
    if db_roll is None:
        raise HTTPException(status_code=404, detail="Рулон не найден")

    if db_roll.removed_date is not None:
        raise HTTPException(
            status_code=404,
            detail="Рулон уже удален",
        )

    try:
        db_roll.removed_date = datetime.now()
        await session.commit()
        await session.refresh(db_roll)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Ошибка при обновлении рулона в базе данных")

    return db_roll


async def get_metal_roll(session: SessionDep, roll_id: int):
    result = await session.execute(
        select(MetalRoll).where(MetalRoll.id == roll_id)
    )
    db_roll = result.scalar_one_or_none()
    if db_roll is None:
        raise HTTPException(status_code=404, detail="Рулон не найден")
    return db_roll


async def get_roll_statistics(session: SessionDep, start_date: datetime, end_date: datetime | None):
    # Количество добавленных рулонов
    added_count_result = await session.execute(
        select(func.count(MetalRoll.id)).filter(
            MetalRoll.added_date >= start_date,
            MetalRoll.added_date <= end_date,
        )
    )
    added_count = added_count_result.scalar()

    # Количество удалённых рулонов
    removed_count_result = await session.execute(
        select(func.count(MetalRoll.id)).filter(
            MetalRoll.removed_date >= start_date,
            MetalRoll.removed_date <= end_date,
        )
    )
    removed_count = removed_count_result.scalar()

    # Средняя длина и вес рулонов, находившихся на складе в этот период
    avg_length_result = await session.execute(
        select(func.avg(MetalRoll.length)).filter(
            MetalRoll.added_date <= end_date,
            or_(
                MetalRoll.removed_date.is_(None),
                MetalRoll.removed_date >= start_date,
            ),
        )
    )
    avg_length = avg_length_result.scalar()

    avg_weight_result = await session.execute(
        select(func.avg(MetalRoll.weight)).filter(
            MetalRoll.added_date <= end_date,
            or_(
                MetalRoll.removed_date.is_(None),
                MetalRoll.removed_date >= start_date,
            ),
        )
    )
    avg_weight = avg_weight_result.scalar()

    # Максимальная и минимальная длина и вес рулонов
    async def get_min_max(session_: SessionDep, model, field, start_date_: datetime|None, end_date_: datetime|None):
        query = await session_.execute(
            select(
                func.min(field).label("min_value"),
                func.max(field).label("max_value")
            ).filter(
                model.added_date <= end_date_,
                or_(
                    model.removed_date.is_(None),
                    model.removed_date >= start_date_,
                )
            )
        )
        result = query.first()
        return result.min_value, result.max_value

    min_length, max_length = await get_min_max(session, MetalRoll, MetalRoll.length, start_date, end_date)
    min_weight, max_weight = await get_min_max(session, MetalRoll, MetalRoll.weight, start_date, end_date)

    # Суммарный вес рулонов на складе за период
    total_weight_result = await session.execute(
        select(func.sum(MetalRoll.weight)).filter(
            MetalRoll.added_date <= end_date,
            or_(
                MetalRoll.removed_date.is_(None),
                MetalRoll.removed_date >= start_date,
            ),
        )
    )
    total_weight = total_weight_result.scalar()

    # Максимальный и минимальный промежуток между добавлением и удалением
    time_diff = func.julianday(MetalRoll.removed_date) - func.julianday(MetalRoll.added_date)

    # Запрос для максимального промежутка времени
    max_time_diff_days_result = await session.execute(
        select(func.max(time_diff)).filter(
            MetalRoll.removed_date.isnot(None),
            MetalRoll.added_date >= start_date,
            MetalRoll.added_date <= end_date,
        )
    )
    max_time_diff_days = max_time_diff_days_result.scalar()

    # Запрос для минимального промежутка времени
    min_time_diff_days_result = await session.execute(
        select(func.min(time_diff)).filter(
            MetalRoll.removed_date.isnot(None),  
            MetalRoll.added_date >= start_date,
            MetalRoll.added_date <= end_date,
        )
    )
    min_time_diff_days = min_time_diff_days_result.scalar()

    # Преобразуем дни в читаемый формат
    max_time_diff = days_to_readable(max_time_diff_days) if max_time_diff_days is not None else "Нет данных"
    min_time_diff = days_to_readable(min_time_diff_days) if min_time_diff_days is not None else "Нет данных"

    # Дни с минимальным и максимальным количеством рулонов
    roll_count_by_day_result = await session.execute(
        select(
            func.date(MetalRoll.added_date).label("day"),
            func.count(MetalRoll.id).label("roll_count")
        ).filter(
            MetalRoll.added_date >= start_date,
            MetalRoll.added_date <= end_date,
        ).group_by(
            func.date(MetalRoll.added_date)
        )
    )
    roll_count_by_day = roll_count_by_day_result.all()

    if roll_count_by_day:
        min_roll_count_day = min(roll_count_by_day, key=lambda x: x.roll_count).day
        max_roll_count_day = max(roll_count_by_day, key=lambda x: x.roll_count).day
    else:
        min_roll_count_day = "Нет данных"
        max_roll_count_day = "Нет данных"

    # Дни с минимальным и максимальным суммарным весом рулонов
    weight_by_day_result = await session.execute(
        select(
            func.date(MetalRoll.added_date).label("day"),
            func.sum(MetalRoll.weight).label("total_weight")
        ).filter(
            MetalRoll.added_date >= start_date,
            MetalRoll.added_date <= end_date,
        ).group_by(
            func.date(MetalRoll.added_date)
        )
    )
    weight_by_day = weight_by_day_result.all()

    if weight_by_day:
        min_weight_day = min(weight_by_day, key=lambda x: x.total_weight).day
        max_weight_day = max(weight_by_day, key=lambda x: x.total_weight).day
    else:
        min_weight_day = "Нет данных"
        max_weight_day = "Нет данных"

    return {
        "added_count": added_count,
        "removed_count": removed_count,
        "avg_length": avg_length,
        "avg_weight": avg_weight,
        "max_length": max_length,
        "min_length": min_length,
        "max_weight": max_weight,
        "min_weight": min_weight,
        "total_weight": total_weight,
        "max_time_diff": max_time_diff,
        "min_time_diff": min_time_diff,
        "min_roll_count_day": min_roll_count_day,
        "max_roll_count_day": max_roll_count_day,
        "min_weight_day": min_weight_day,
        "max_weight_day": max_weight_day,
    }


def days_to_readable(days: float) -> str:
    if days is None:
        return "Нет данных"

    delta = timedelta(days=days)

    # извлекаем дни, часы, минуты и секунды
    total_seconds = int(delta.total_seconds())
    days = total_seconds // (24 * 3600)
    remaining_seconds = total_seconds % (24 * 3600)
    hours = remaining_seconds // 3600
    remaining_seconds %= 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    return f"{days} дней, {hours} часов, {minutes} минут, {seconds} секунд"
