import pytest
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Base, User, Flight, Booking
from db import SessionLocal

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    """Create a test client with a fresh database."""
    # Import server module and patch SessionLocal
    import server
    import db as db_module

    # Patch SessionLocal to use test session factory
    def get_test_session():
        return db_session

    monkeypatch.setattr(db_module, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(server, "SessionLocal", lambda: db_session)

    # Don't run seed during tests
    monkeypatch.setattr(server, "seed", lambda: None)

    # Override get_db dependency to use test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    server.app.dependency_overrides[db_module.get_db] = override_get_db

    with TestClient(server.app) as test_client:
        yield test_client

    server.app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_flight_data():
    """Sample flight data for testing."""
    return {
        "origin": "Earth",
        "destination": "Mars",
        "departure_time": "2099-01-01T09:00:00Z",
        "arrival_time": "2099-01-01T17:00:00Z",
        "price": 1000000,
        "economy_seats": 5,
        "flexi_seats": 5,
        "business_seats": 5,
        "galaxium_seats": 5,
    }


@pytest.fixture
def sample_booking_data():
    """Sample booking data for testing."""
    return {
        "user_id": 1,
        "name": "Test User",
        "flight_id": 1,
        "seat_class": "economy",
    }


def iso_utc(dt: datetime) -> str:
    """Format an aware datetime as an ISO string with a Z suffix."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def make_flight(db_session):
    """Return a factory that adds a flight departing `hours_until_departure` from now."""
    def _make(hours_until_departure: float = 24 * 365, price: int = 1000, **seats):
        departure = datetime.now(timezone.utc) + timedelta(hours=hours_until_departure)
        flight = Flight(
            origin="Earth",
            destination="Mars",
            departure_time=iso_utc(departure),
            arrival_time=iso_utc(departure + timedelta(hours=8)),
            price=price,
            economy_seats=seats.get("economy_seats", 5),
            flexi_seats=seats.get("flexi_seats", 5),
            business_seats=seats.get("business_seats", 5),
            galaxium_seats=seats.get("galaxium_seats", 5),
        )
        db_session.add(flight)
        db_session.commit()
        return flight
    return _make


@pytest.fixture
def make_booking(db_session):
    """Return a factory that adds a user and a booking for the given flight and class."""
    def _make(flight, seat_class: str = "economy", status: str = "booked"):
        user = User(name="Test User", email=f"user{db_session.query(User).count()}@example.com")
        db_session.add(user)
        db_session.commit()
        booking = Booking(
            user_id=user.user_id,
            flight_id=flight.flight_id,
            status=status,
            booking_time=iso_utc(datetime.now(timezone.utc)),
            seat_class=seat_class,
        )
        db_session.add(booking)
        db_session.commit()
        return booking
    return _make
