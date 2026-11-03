from models import Base, User, Flight, Booking
from db import engine, SessionLocal
from schemas import calculate_refund
from datetime import datetime, timedelta, timezone
import random

SEAT_CLASSES = ["economy", "flexi", "business", "galaxium"]

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Clear existing data
    db.query(Booking).delete()
    db.query(User).delete()
    db.query(Flight).delete()
    db.commit()
    # Add demo users
    users = [
        User(name="Alice", email="alice@example.com"),
        User(name="Bob", email="bob@example.com"),
        User(name="Charlie", email="charlie@galaxium.com"),
        User(name="Diana", email="diana@moonmail.com"),
        User(name="Eve", email="eve@marsmail.com"),
        User(name="Frank", email="frank@venusmail.com"),
        User(name="Grace", email="grace@jupiter.com"),
        User(name="Heidi", email="heidi@europa.com"),
        User(name="Ivan", email="ivan@asteroidbelt.com"),
        User(name="Judy", email="judy@pluto.com"),
    ]
    db.add_all(users)
    db.commit()
    # Add demo flights — each flight has 4 seat class inventories
    # economy_seats / flexi_seats / business_seats / galaxium_seats
    flights = [
        Flight(origin="Earth",   destination="Mars",   departure_time="2099-01-01T09:00:00Z", arrival_time="2099-01-01T17:00:00Z", price=1000000, economy_seats=10, flexi_seats=8, business_seats=4, galaxium_seats=2),
        Flight(origin="Earth",   destination="Moon",   departure_time="2099-01-02T10:00:00Z", arrival_time="2099-01-02T14:00:00Z", price=500000,  economy_seats=12, flexi_seats=8, business_seats=4, galaxium_seats=2),
        Flight(origin="Mars",    destination="Earth",  departure_time="2099-01-03T12:00:00Z", arrival_time="2099-01-03T20:00:00Z", price=950000,  economy_seats=10, flexi_seats=6, business_seats=4, galaxium_seats=2),
        Flight(origin="Venus",   destination="Earth",  departure_time="2099-01-04T08:00:00Z", arrival_time="2099-01-04T18:00:00Z", price=1200000, economy_seats=8,  flexi_seats=6, business_seats=3, galaxium_seats=1),
        Flight(origin="Jupiter", destination="Europa", departure_time="2099-01-05T15:00:00Z", arrival_time="2099-01-05T19:00:00Z", price=2000000, economy_seats=6,  flexi_seats=4, business_seats=2, galaxium_seats=1),
        Flight(origin="Earth",   destination="Venus",  departure_time="2099-01-06T07:00:00Z", arrival_time="2099-01-06T15:00:00Z", price=1100000, economy_seats=10, flexi_seats=8, business_seats=4, galaxium_seats=2),
        Flight(origin="Moon",    destination="Mars",   departure_time="2099-01-07T11:00:00Z", arrival_time="2099-01-07T19:00:00Z", price=800000,  economy_seats=12, flexi_seats=8, business_seats=4, galaxium_seats=2),
        Flight(origin="Mars",    destination="Jupiter",departure_time="2099-01-08T13:00:00Z", arrival_time="2099-01-08T23:00:00Z", price=2500000, economy_seats=8,  flexi_seats=6, business_seats=3, galaxium_seats=1),
        Flight(origin="Europa",  destination="Earth",  departure_time="2099-01-09T09:00:00Z", arrival_time="2099-01-09T21:00:00Z", price=3000000, economy_seats=6,  flexi_seats=4, business_seats=2, galaxium_seats=1),
        Flight(origin="Earth",   destination="Pluto",  departure_time="2099-01-10T06:00:00Z", arrival_time="2099-01-11T06:00:00Z", price=5000000, economy_seats=4,  flexi_seats=3, business_seats=2, galaxium_seats=1),
    ]
    db.add_all(flights)
    db.commit()
    # Add demo bookings
    user_ids = [user.user_id for user in db.query(User).all()]
    flights_by_id = {flight.flight_id: flight for flight in db.query(Flight).all()}
    flight_ids = list(flights_by_id)
    statuses = ["booked", "cancelled", "completed"]
    bookings = []
    now = datetime.utcnow()
    now_utc = datetime.now(timezone.utc)
    for i in range(20):
        user_id = random.choice(user_ids)
        flight_id = random.choice(flight_ids)
        status = random.choice(statuses)
        seat_class = random.choice(SEAT_CLASSES)
        booking_time = (now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))).isoformat() + "Z"
        refund_amount = None
        if status == "cancelled":
            flight = flights_by_id[flight_id]
            refund_amount = calculate_refund(seat_class, flight.price, flight.departure_time, now_utc)
        bookings.append(Booking(user_id=user_id, flight_id=flight_id, status=status, booking_time=booking_time, seat_class=seat_class, refund_amount=refund_amount))
    db.add_all(bookings)
    db.commit()
    db.close()
    print("Database seeded with elaborate demo data!")

if __name__ == "__main__":
    seed()
