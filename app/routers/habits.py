from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app import schemas
from app import database
from app.auth import get_current_user

router = APIRouter(prefix="/habits", tags=["habits"])

def get_owned_habit_or_404(habit_id: int, db: Session, current_user: models.User) -> models.Habits:
    habit = db.get(models.Habits, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this habit")
    return habit

@router.post("", response_model=schemas.HabitOut, summary="Create a new habit")
def create_habit(habit: schemas.HabitCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Create a habit owned by the current authenticated user."""
    new_habit = models.Habits(name=habit.name, frequency=habit.frequency, owner_id=current_user.id)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit

@router.get("", response_model=list[schemas.HabitOut], summary="List your habits")
def list_habits(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Return all habits belonging to the current authenticated user."""
    return db.query(models.Habits).filter(models.Habits.owner_id == current_user.id).all()

@router.get("/{habit_id}", response_model=schemas.HabitOut, summary="Get a single habit")
def get_habit(habit_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Return one habit by ID, if it belongs to the current user."""
    return get_owned_habit_or_404(habit_id, db, current_user)

@router.patch("/{habit_id}/complete", response_model=schemas.HabitOut, summary="Toggle a habit's completion and update its streak")
def complete_habit(habit_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Toggle completion for a habit. Marking it complete updates the streak; un-marking leaves the streak untouched."""
    habit = get_owned_habit_or_404(habit_id, db, current_user)
    today = date.today()

    if habit.completed:
        habit.completed = False
    else:
        habit.completed = True
        if habit.last_completed_date == today:
            pass
        elif habit.last_completed_date == today - timedelta(days=1):
            habit.streak_count += 1
        else:
            habit.streak_count = 1
        habit.last_completed_date = today

    db.commit()
    db.refresh(habit)
    return habit

@router.delete("/{habit_id}", summary="Delete a habit")
def delete_habit(habit_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Delete one habit by ID, if it belongs to the current user."""
    habit = get_owned_habit_or_404(habit_id, db, current_user)
    db.delete(habit)
    db.commit()
    return {"message": "Habit successfully deleted"}