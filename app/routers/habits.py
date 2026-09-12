from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app import schemas
from app import database
from app.auth import get_current_user

router = APIRouter(prefix="/habits", tags=["habits"])

def get_owned_habit_or_404(habit_id: int, db: Session, current_user: models.User) ->  models.Habits:
    habit = db.get(models.Habits, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this habit")
    return habit

@router.post("", response_model=schemas.HabitOut)
def create_habit(habit: schemas.HabitCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    new_habit = models.Habits(name=habit.name, frequency=habit.frequency, owner_id=current_user.id)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit

@router.get("",  response_model=list[schemas.HabitOut])
def list_habits(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Habits).filter(models.Habits.owner_id == current_user.id).all()

@router.get("/{habit_id}",  response_model=schemas.HabitOut)
def get_habit(habit_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return get_owned_habit_or_404(habit_id, db, current_user)

@router.delete("/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    habit = get_owned_habit_or_404(habit_id, db, current_user)
    db.delete(habit)
    db.commit()
    return {"message": "Habit successfully deleted"}