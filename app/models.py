from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

class Habits(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    frequency = Column(String, nullable= False)
    completed = Column(Boolean, default=False, nullable=False)
