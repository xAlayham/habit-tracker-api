from fastapi import FastAPI
from app import models
from app.database import engine
from app.routers import users, habits

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

app.include_router(users.router)
app.include_router(habits.router)

@app.get("/")
def get_api_info():
    return {
        "name": "Habit_API",
        "version": "1.0.0",
    }