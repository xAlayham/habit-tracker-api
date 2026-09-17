from pydantic import BaseModel, ConfigDict
from enum import Enum
from datetime import date


class FrequencyEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class HabitCreate(BaseModel):
    name: str
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
    username: str
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str