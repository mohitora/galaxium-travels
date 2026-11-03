import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import User, Flight, Booking


class TestFlightsEndpoint:
    """Test /flights endpoint."""

    def test_get_flights_empty(self, client, db_session):
        """Test getting flights when database is empty."""
        response = client.get("/flights")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_flights_with_data(self, client, db_session):
        """Test getting flights with data."""
        db_session.add(Flight(
            origin="Earth",
            destination="Mars",
            departure_time="2099-01-01T09:00:00Z",
            arrival_time="2099-01-01T17:00:00Z",
            price=1000000,
            economy_seats=5,
            flexi_seats=5,
            business_seats=5,
            galaxium_seats=5
        ))
        db_session.commit()

        response = client.get("/flights")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["origin"] == "Earth"
        assert data[0]["destination"] == "Mars"
        assert data[0]["economy_seats"] == 5
        assert data[0]["galaxium_price"] == 6000000


class TestRegisterEndpoint:
    """Test /register endpoint."""

    def test_register_success(self, client, db_session, sample_user_data):
        """Test successful user registration."""
        response = client.post("/register", json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_user_data["name"]
        assert data["email"] == sample_user_data["email"]
        assert "user_id" in data

    def test_register_duplicate_email(self, client, db_session, sample_user_data):
        """Test registration with duplicate email."""
        client.post("/register", json=sample_user_data)
        response = client.post("/register", json=sample_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "EMAIL_EXISTS"


class TestUserEndpoint:
    """Test /user endpoint."""

    def test_get_user_success(self, client, db_session, sample_user_data):
        """Test successful user retrieval."""
        client.post("/register", json=sample_user_data)

        response = client.get(
            "/user",
            params={"name": sample_user_data["name"], "email": sample_user_data["email"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_user_data["name"]

    def test_get_user_not_found(self, client, db_session):
        """Test user retrieval when not found."""
        response = client.get(
            "/user",
            params={"name": "NonExistent", "email": "none@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "USER_NOT_FOUND"


class TestBookEndpoint:
    """Test /book endpoint."""

    def test_book_flight_success(self, client, db_session, sample_user_data):
        """Test successful flight booking."""
        # Register user
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        # Create flight
        db_session.add(Flight(
            origin="Earth",
            destination="Mars",
            departure_time="2099-01-01T09:00:00Z",
            arrival_time="2099-01-01T17:00:00Z",
            price=1000000,
            economy_seats=5,
            flexi_seats=5,
            business_seats=5,
            galaxium_seats=5
        ))
        db_session.commit()
        flight = db_session.query(Flight).first()

        # Book flight
        response = client.post("/book", json={
            "user_id": user_id,
            "name": sample_user_data["name"],
            "flight_id": flight.flight_id,
            "seat_class": "economy"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "booked"
        assert data["seat_class"] == "economy"
        assert data["user_id"] == user_id

    def test_book_flight_not_found(self, client, db_session, sample_user_data):
        """Test booking non-existent flight."""
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        response = client.post("/book", json={
            "user_id": user_id,
            "name": sample_user_data["name"],
            "flight_id": 999,
            "seat_class": "economy"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "FLIGHT_NOT_FOUND"

    def test_book_flight_missing_seat_class(self, client, db_session, sample_user_data):
        """Test booking without seat_class fails request validation."""
        response = client.post("/book", json={
            "user_id": 1,
            "name": sample_user_data["name"],
            "flight_id": 1
        })
        assert response.status_code == 422


class TestBookingsEndpoint:
    """Test /bookings/{user_id} endpoint."""

    def test_get_bookings_success(self, client, db_session, sample_user_data):
        """Test getting user bookings."""
        # Register user
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        # Create flight and booking
        db_session.add(Flight(
            origin="Earth",
            destination="Mars",
            departure_time="2099-01-01T09:00:00Z",
            arrival_time="2099-01-01T17:00:00Z",
            price=1000000,
            economy_seats=5,
            flexi_seats=5,
            business_seats=5,
            galaxium_seats=5
        ))
        db_session.commit()
        flight = db_session.query(Flight).first()

        db_session.add(Booking(
            user_id=user_id,
            flight_id=flight.flight_id,
            status="booked",
            booking_time="2099-01-01T10:00:00Z",
            seat_class="economy"
        ))
        db_session.commit()

        response = client.get(f"/bookings/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "booked"
        assert data[0]["seat_class"] == "economy"

    def test_get_bookings_empty(self, client, db_session):
        """Test getting bookings when user has none."""
        response = client.get("/bookings/999")
        assert response.status_code == 200
        assert response.json() == []


class TestCancelEndpoint:
    """Test /cancel/{booking_id} endpoint."""

    def test_cancel_booking_success(self, client, db_session, sample_user_data):
        """Test successful booking cancellation."""
        # Register user
        user_response = client.post("/register", json=sample_user_data)
        user_id = user_response.json()["user_id"]

        # Create flight and booking
        db_session.add(Flight(
            origin="Earth",
            destination="Mars",
            departure_time="2099-01-01T09:00:00Z",
            arrival_time="2099-01-01T17:00:00Z",
            price=1000000,
            economy_seats=4,
            flexi_seats=5,
            business_seats=5,
            galaxium_seats=5
        ))
        db_session.commit()
        flight = db_session.query(Flight).first()

        db_session.add(Booking(
            user_id=user_id,
            flight_id=flight.flight_id,
            status="booked",
            booking_time="2099-01-01T10:00:00Z",
            seat_class="economy"
        ))
        db_session.commit()
        booking = db_session.query(Booking).first()

        response = client.post(f"/cancel/{booking.booking_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["refund_amount"] == 800000

        db_session.refresh(flight)
        assert flight.economy_seats == 5

    def test_cancel_booking_not_found(self, client, db_session):
        """Test cancelling non-existent booking."""
        response = client.post("/cancel/999")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "BOOKING_NOT_FOUND"

    @pytest.mark.parametrize("seat_class,refund", [
        ("economy", 800),
        ("flexi", 1500),
        ("business", 2250),
        ("galaxium", 6000),
    ])
    def test_cancel_returns_refund_amount(self, client, db_session, make_flight, make_booking, seat_class, refund):
        """Test the cancel response carries the refund for each class."""
        booking = make_booking(make_flight(hours_until_departure=24 * 30, price=1000), seat_class)

        response = client.post(f"/cancel/{booking.booking_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["refund_amount"] == refund

    def test_cancel_inside_cutoff_returns_zero_refund(self, client, db_session, make_flight, make_booking):
        """Test cancelling Economy inside 72h returns refund_amount 0."""
        booking = make_booking(make_flight(hours_until_departure=48, price=1000), "economy")

        response = client.post(f"/cancel/{booking.booking_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["refund_amount"] == 0

    def test_cancel_already_cancelled(self, client, db_session, make_flight, make_booking):
        """Test cancelling twice returns ALREADY_CANCELLED."""
        booking = make_booking(make_flight(), "economy")
        client.post(f"/cancel/{booking.booking_id}")

        response = client.post(f"/cancel/{booking.booking_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "ALREADY_CANCELLED"

    def test_cancel_completed_not_cancellable(self, client, db_session, make_flight, make_booking):
        """Test cancelling a completed booking returns BOOKING_NOT_CANCELLABLE."""
        booking = make_booking(make_flight(), "economy", status="completed")

        response = client.post(f"/cancel/{booking.booking_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "BOOKING_NOT_CANCELLABLE"


class TestRefundPreviewEndpoint:
    """Test /refund-preview/{booking_id} endpoint."""

    @pytest.mark.parametrize("seat_class,class_price,refund,percent", [
        ("economy", 1000, 800, 80),
        ("flexi", 1500, 1500, 100),
        ("business", 3000, 2250, 75),
        ("galaxium", 6000, 6000, 100),
    ])
    def test_preview_success(
        self, client, db_session, make_flight, make_booking, seat_class, class_price, refund, percent
    ):
        """Test the preview body for each class with long notice."""
        flight = make_flight(hours_until_departure=24 * 30, price=1000)
        booking = make_booking(flight, seat_class)

        response = client.get(f"/refund-preview/{booking.booking_id}")

        assert response.status_code == 200
        assert response.json() == {
            "booking_id": booking.booking_id,
            "seat_class": seat_class,
            "class_price": class_price,
            "refund_amount": refund,
            "refund_percent": percent,
            "departure_time": flight.departure_time,
        }

    def test_preview_inside_cutoff_keeps_rule_percent(self, client, db_session, make_flight, make_booking):
        """Test refund_amount is 0 inside the cutoff while refund_percent stays the rule value."""
        booking = make_booking(make_flight(hours_until_departure=48, price=1000), "economy")

        response = client.get(f"/refund-preview/{booking.booking_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["refund_amount"] == 0
        assert data["refund_percent"] == 80

    def test_preview_does_not_cancel(self, client, db_session, make_flight, make_booking):
        """Test the preview leaves the booking and seats untouched."""
        flight = make_flight(hours_until_departure=24 * 30)
        booking = make_booking(flight, "flexi")

        response = client.get(f"/refund-preview/{booking.booking_id}")

        assert response.status_code == 200
        db_session.refresh(booking)
        db_session.refresh(flight)
        assert booking.status == "booked"
        assert booking.refund_amount is None
        assert flight.flexi_seats == 5

    def test_preview_not_found(self, client, db_session):
        """Test the preview of an unknown booking returns HTTP 200 with an error body."""
        response = client.get("/refund-preview/999")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "BOOKING_NOT_FOUND"

    def test_preview_already_cancelled(self, client, db_session, make_flight, make_booking):
        """Test the preview after cancelling returns ALREADY_CANCELLED."""
        booking = make_booking(make_flight(), "economy")
        client.post(f"/cancel/{booking.booking_id}")

        response = client.get(f"/refund-preview/{booking.booking_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "ALREADY_CANCELLED"

    def test_preview_completed_not_cancellable(self, client, db_session, make_flight, make_booking):
        """Test the preview of a completed booking returns BOOKING_NOT_CANCELLABLE."""
        booking = make_booking(make_flight(), "economy", status="completed")

        response = client.get(f"/refund-preview/{booking.booking_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error_code"] == "BOOKING_NOT_CANCELLABLE"

    def test_preview_non_integer_id(self, client, db_session):
        """Test a non-integer booking id fails request validation."""
        response = client.get("/refund-preview/abc")
        assert response.status_code == 422


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client, db_session):
        """Test health check returns OK."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}
