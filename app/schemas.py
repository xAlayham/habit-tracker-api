from pydantic import BaseModel

class HabitCreate(BaseModel):
    name: str
    frequency: str

class HabitOut(BaseModel):
    id: int
    name: str
    frequency: str
    completed: bool

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True