from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
from src.config import settings

async_engine = create_async_engine(settings.DB_URL(), echo=True)
AsyncSessionLocal = async_sessionmaker(expire_on_commit=False,
                                       bind=async_engine,
                                       class_=AsyncSession)

class Base(DeclarativeBase):
    pass


async def get_session():
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к базе данных: {str(e)}")