from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app.database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

#DELETE /habits/{habit_id} — deletes the matching habit (with a 404 if it doesn't exist), returns some confirmation.
def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

@app.post("/habits")
def create_habit(name:str, frequency:str, db: Session = Depends(get_db)):
    new_habit = models.Habits(name=name, frequency=frequency)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit

@app.get("/habits")
def list_habits(db: Session = Depends(get_db)):
    return db.query(models.Habits).all()

@app.get("/habits/{habit_id}")
def get_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.get(models.Habits, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit

@app.delete("/habits/{habit_id}")
def deelte_habit(habit_id: int, db: Session = Depends(get_db)):
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