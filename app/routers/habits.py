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

def period_key(d: date, frequency: str):
    """A value that's equal for any two dates falling in the same period for this frequency."""
    if frequency == "weekly":
        iso_year, iso_week, _ = d.isocalendar()
        return (iso_year, iso_week)
    if frequency == "monthly":
        return (d.year, d.month)
    if frequency == "yearly":
        return (d.year,)
    return (d.year, d.month, d.day)  # daily, and fallback

def previous_period_key(d: date, frequency: str):
    """The period_key for whichever period comes immediately before d's period."""
    if frequency == "weekly":
        return period_key(d - timedelta(days=7), frequency)
    if frequency == "monthly":
        last_day_of_prev_month = d.replace(day=1) - timedelta(days=1)
        return period_key(last_day_of_prev_month, frequency)
    if frequency == "yearly":
        return (d.year - 1,)
    return period_key(d - timedelta(days=1), frequency)  # daily, and fallback

def is_done_this_period(habit: models.Habits, today: date) -> bool:
    if habit.last_completed_date is None:
        return False
    return period_key(habit.last_completed_date, habit.frequency) == period_key(today, habit.frequency)

def effective_streak_count(habit: models.Habits, today: date) -> int:
    """The streak as of `today`, without mutating the stored value.

    streak_count only gets reset by the next completion, so a habit left
    untouched keeps reporting its old streak indefinitely. A streak is only
    still "alive" if its last completion falls in the current period (already
    done) or the immediately preceding one (still time to keep it going) —
    anything older means one or more periods were missed, so it reads as 0.
    """
    if habit.last_completed_date is None:
        return 0
    last_key = period_key(habit.last_completed_date, habit.frequency)
    if last_key == period_key(today, habit.frequency) or last_key == previous_period_key(today, habit.frequency):
        return habit.streak_count
    return 0

def to_habit_out(habit: models.Habits) -> schemas.HabitOut:
    """Build the response with `completed` and `streak_count` computed fresh, never trusting stale stored values."""
    today = date.today()
    return schemas.HabitOut(
        id=habit.id,
        name=habit.name,
        frequency=habit.frequency,
        completed=is_done_this_period(habit, today),
        streak_count=effective_streak_count(habit, today),
        last_completed_date=habit.last_completed_date,
    )

@router.post("", response_model=schemas.HabitOut, summary="Create a new habit")
def create_habit(habit: schemas.HabitCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Create a habit owned by the current authenticated user."""
    new_habit = models.Habits(name=habit.name, frequency=habit.frequency, owner_id=current_user.id)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return to_habit_out(new_habit)

@router.get("", response_model=list[schemas.HabitOut], summary="List your habits")
def list_habits(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Return all habits belonging to the current authenticated user."""
    habits = db.query(models.Habits).filter(models.Habits.owner_id == current_user.id).all()
    return [to_habit_out(habit) for habit in habits]

@router.get("/{habit_id}", response_model=schemas.HabitOut, summary="Get a single habit")
def get_habit(habit_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Return one habit by ID, if it belongs to the current user."""
    habit = get_owned_habit_or_404(habit_id, db, current_user)
    return to_habit_out(habit)

@router.patch("/{habit_id}/complete", response_model=schemas.HabitOut, summary="Toggle a habit's completion for the current period and update its streak")
def complete_habit(habit_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Toggle completion for the CURRENT period (day/week/month/year, based on frequency) and keep the streak in sync."""
    habit = get_owned_habit_or_404(habit_id, db, current_user)
    today = date.today()

    if is_done_this_period(habit, today):
        # already done this period -> undo it, restoring whatever completion
        # date this one replaced so a follow-up redo can tell the streak continues
        habit.last_completed_date = habit.previous_completed_date
        habit.previous_completed_date = None
        habit.streak_count = max(habit.streak_count - 1, 0)
    else:
        # not done this period yet -> mark it, and extend the streak only if the
        # previous completion was in the immediately preceding period
        if habit.last_completed_date is not None and period_key(habit.last_completed_date, habit.frequency) == previous_period_key(today, habit.frequency):
            habit.streak_count += 1
        else:
            habit.streak_count = 1
        habit.previous_completed_date = habit.last_completed_date
        habit.last_completed_date = today

    db.commit()
    db.refresh(habit)
    return to_habit_out(habit)

@router.delete("/{habit_id}", summary="Delete a habit")
def delete_habit(habit_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Delete one habit by ID, if it belongs to the current user."""
    habit = get_owned_habit_or_404(habit_id, db, current_user)
    db.delete(habit)
    db.commit()
    return {"message": "Habit successfully deleted"}