from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MetalRoll(Base):
    __tablename__ = "metal_rolls"
    id = Column(Integer, primary_key=True, index=True)
    length = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    added_date = Column(DateTime, nullable=False)
    removed_date = Column(DateTime, nullable=True)
