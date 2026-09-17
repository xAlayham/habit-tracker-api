from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from datetime import date


class FrequencyEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    frequency: FrequencyEnum

class HabitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    frequency: FrequencyEnum
    completed: bool
    streak_count: int
    last_completed_date: date | None = None

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=100)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str