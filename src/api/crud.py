from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import models, schemas
from datetime import datetime, timedelta
from fastapi import HTTPException


def create_metal_roll(db: Session, metal_roll: schemas.MetalRoll):
    if metal_roll.length <= 0 or metal_roll.weight <= 0:
        raise HTTPException(status_code=422, detail="Длина и вес должны быть положительными числами")
    db_metal_roll = models.MetalRoll(
        length=metal_roll.length,
        weight=metal_roll.weight,
        added_date=datetime.now()
    )
    db.add(db_metal_roll)
    db.commit()
    db.refresh(db_metal_roll)
    return db_metal_roll


def delete_metal_roll(db: Session, roll_id: int):
    db_metal_roll = db.query(models.MetalRoll).filter(models.MetalRoll.id == roll_id).first()
    if not db_metal_roll:
        raise HTTPException(status_code=404, detail="Рулон не найден")
    db_metal_roll.removed_date = datetime.now()
    db.commit()
    db.refresh(db_metal_roll)
    return db_metal_roll


def get_metal_rolls(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.MetalRoll).offset(skip).limit(limit).all()


def get_metal_roll(db: Session, roll_id: int):
    metal_roll = db.query(models.MetalRoll).filter(models.MetalRoll.id == roll_id).first()
    return metal_roll


def get_roll_statistics(db: Session, start_date: datetime, end_date: datetime):
    # количество добавленных рулонов
    added_count = db.query(models.MetalRoll).filter(
        models.MetalRoll.added_date >= start_date,
        models.MetalRoll.added_date <= end_date,
    ).count()

    # количество удалённых рулонов
    removed_count = db.query(models.MetalRoll).filter(
        models.MetalRoll.removed_date >= start_date,
        models.MetalRoll.removed_date <= end_date,
    ).count()

    # средняя длина и вес рулонов, находившихся на складе в этот период
    avg_length = db.query(func.avg(models.MetalRoll.length)).filter(
        models.MetalRoll.added_date <= end_date,
        or_(
            models.MetalRoll.removed_date.is_(None),
            models.MetalRoll.removed_date >= start_date,
        ),
    ).scalar()

    avg_weight = db.query(func.avg(models.MetalRoll.weight)).filter(
        models.MetalRoll.added_date <= end_date,
        or_(
            models.MetalRoll.removed_date.is_(None),
            models.MetalRoll.removed_date >= start_date,
        ),
    ).scalar()

    # максимальная и минимальная длина и вес рулонов
    def get_min_max(db_: Session, model, field, start_date_: datetime, end_date_: datetime):

        query = db_.query(
            func.min(field).label("min_value"),
            func.max(field).label("max_value")
        ).filter(
            model.added_date <= end_date_,
            or_(
                model.removed_date.is_(None),
                model.removed_date >= start_date_,
            )
        ).first()

        return query.min_value, query.max_value

    min_length, max_length = get_min_max(db, models.MetalRoll, models.MetalRoll.length, start_date, end_date)
    min_weight, max_weight = get_min_max(db, models.MetalRoll, models.MetalRoll.weight, start_date, end_date)

    # суммарный вес рулонов на складе за период
    total_weight = db.query(func.sum(models.MetalRoll.weight)).filter(
        models.MetalRoll.added_date <= end_date,
        or_(
            models.MetalRoll.removed_date.is_(None),
            models.MetalRoll.removed_date >= start_date,
        ),
    ).scalar()

    # максимальный промежуток между добавлением и удалением
    time_diff = func.julianday(models.MetalRoll.removed_date) - func.julianday(models.MetalRoll.added_date)
    max_time_diff_days = db.query(func.max(time_diff)).filter(
        models.MetalRoll.removed_date.isnot(None),
        models.MetalRoll.added_date >= start_date,
        models.MetalRoll.added_date <= end_date,
    ).scalar()
    # минимальный промежуток между добавлением и удалением
    min_time_diff_days = db.query(func.min(time_diff)).filter(
        models.MetalRoll.removed_date.isnot(None),
        models.MetalRoll.added_date >= start_date,
        models.MetalRoll.added_date <= end_date,
    ).scalar()

    max_time_diff = days_to_readable(max_time_diff_days)
    min_time_diff = days_to_readable(min_time_diff_days)

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