from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from .database import Base
class Habits(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    frequency = Column(String, nullable= False)
    completed = Column(Boolean, default=False, nullable=False)
    streak_count = Column(Integer, default=0, nullable=False)
    last_completed_date = Column(Date, nullable=True)
    previous_completed_date = Column(Date, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"),nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)