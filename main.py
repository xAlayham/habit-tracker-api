from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app.database import engine
from app import schemas
from app import database
from app.routers import users

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

app.include_router(users.router)

@app.post("/habits", response_model=schemas.HabitOut)
def create_habit(habit: schemas.HabitCreate, db: Session = Depends(database.get_db)):
    new_habit = models.Habits(name=habit.name, frequency=habit.frequency)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit

@app.get("/habits",  response_model=list[schemas.HabitOut])
def list_habits(db: Session = Depends(database.get_db)):
    return db.query(models.Habits).all()

@app.get("/habits/{habit_id}",  response_model=schemas.HabitOut)
def get_habit(habit_id: int, db: Session = Depends(database.get_db)):
    habit = db.get(models.Habits, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit

@app.delete("/habits/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(database.get_db)):
    habit = db.get(models.Habits, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    db.delete(habit)
    db.commit()
    return {"deleted": habit_id}

@app.get("/")
def get_api_info():
    return {
        "name": "Habit_API",
        "version": "1.0.0",
    }