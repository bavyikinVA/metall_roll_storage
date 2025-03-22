from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class MetalRollBase(BaseModel):
    length: float = Field(ge=0, description="Длина должна быть положительным числом")
    weight: float = Field(ge=0, description="Вес должен быть положительным числом")

class MetalRoll(MetalRollBase):
    id: int = Field(ge=0)
    added_date: datetime
    removed_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class StatisticsResponse(BaseModel):
    added_count: int
    removed_count: int
    avg_length: Optional[float]
    avg_weight: Optional[float]
    max_length: Optional[float]
    min_length: Optional[float]
    max_weight: Optional[float]
    min_weight: Optional[float]
    total_weight: Optional[float]
    max_time_diff: Optional[str]
    min_time_diff: Optional[str]
    min_roll_count_day: Optional[str]
    max_roll_count_day: Optional[str]
    min_weight_day: Optional[str]
    max_weight_day: Optional[str]