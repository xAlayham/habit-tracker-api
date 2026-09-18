from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database import Base, get_db
from app.routers import habits as habits_router

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def auth_headers(client):
    client.post("/users/register", json={"username": "testmember", "password": "testpass123"})

    response = client.post("/users/login", data={"username": "testmember", "password": "testpass123"})
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
def second_user_auth_headers(client):
    client.post("/users/register", json={"username": "testmember2", "password": "testpass123"})

    response = client.post("/users/login", data={"username": "testmember2", "password": "testpass123"})
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
def freeze_date(monkeypatch):
    """Return a function that pins date.today() as seen inside app/routers/habits.py,
    so streak/period logic can be tested across day/week/month/year boundaries
    without waiting for real time to pass."""
    def _freeze(target: date):
        class FrozenDate(date):
            @classmethod
            def today(cls):
                return target
        monkeypatch.setattr(habits_router, "date", FrozenDate)
    return _freeze