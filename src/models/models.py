from sqlalchemy import DateTime, Column, Integer, Float
from src.database import Base

class MetalRoll(Base):
    __tablename__ = "metal_rolls"

    id = Column(Integer, primary_key=True)
    length = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    added_date = Column(DateTime, nullable=False)
    removed_date = Column(DateTime, nullable=False)
