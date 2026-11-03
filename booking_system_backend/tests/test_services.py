import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import User, Flight, Booking
from schemas import ErrorResponse, RefundPreviewOut
from services import flight, user, booking

SEAT_CLASSES = ["economy", "flexi", "business", "galaxium"]


def _seats(flight_obj):
    """Return the per-class seat counts of a flight as a dict."""
    return {c: getattr(flight_obj, f"{c}_seats") for c in SEAT_CLASSES}


class TestFlightService:
    """Test flight service functions."""

    def test_list_flights_empty(self, db_session):
        """Test listing flights when database is empty."""
        result = flight.list_flights(db_session)
        assert result == []

    def test_list_flights_with_data(self, db_session):
        """Test listing flights with data in database."""
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

        result = flight.list_flights(db_session)
        assert len(result) == 1
        assert result[0].origin == "Earth"
        assert result[0].destination == "Mars"


class TestUserService:
    """Test user service functions."""

    def test_register_user_success(self, db_session):
        """Test successful user registration."""
        result = user.register_user(db_session, "Test User", "test@example.com")
        assert result.name == "Test User"
        assert result.email == "test@example.com"
        assert result.user_id > 0

    def test_register_user_duplicate_email(self, db_session):
        """Test registration with duplicate email."""
        user.register_user(db_session, "User 1", "test@example.com")
        result = user.register_user(db_session, "User 2", "test@example.com")

        assert isinstance(result, ErrorResponse)
        assert result.error_code == "EMAIL_EXISTS"

    def test_get_user_success(self, db_session):
        """Test successful user retrieval."""
        db_session.add(User(name="Test User", email="test@example.com"))
        db_session.commit()

        result = user.get_user(db_session, "Test User", "test@example.com")
        assert result.name == "Test User"
        assert result.email == "test@example.com"

    def test_get_user_not_found(self, db_session):
        """Test user retrieval when not found."""
        result = user.get_user(db_session, "NonExistent", "none@example.com")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "USER_NOT_FOUND"


class TestBookingService:
    """Test booking service functions."""

    def test_book_flight_success(self, db_session):
        """Test successful flight booking."""
        db_session.add(User(name="Test User", email="test@example.com"))
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

        user_obj = db_session.query(User).first()
        flight_obj = db_session.query(Flight).first()

        result = booking.book_flight(db_session, user_obj.user_id, "Test User", flight_obj.flight_id, "economy")
        assert result.status == "booked"
        assert result.seat_class == "economy"
        assert result.user_id == user_obj.user_id
        assert result.flight_id == flight_obj.flight_id

        # Verify only the economy seat was decremented
        db_session.refresh(flight_obj)
        assert _seats(flight_obj) == {"economy": 4, "flexi": 5, "business": 5, "galaxium": 5}

    def test_book_flight_not_found(self, db_session):
        """Test booking non-existent flight."""
        db_session.add(User(name="Test User", email="test@example.com"))
        db_session.commit()
        user_obj = db_session.query(User).first()

        result = booking.book_flight(db_session, user_obj.user_id, "Test User", 999, "economy")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "FLIGHT_NOT_FOUND"

    def test_book_flight_no_seats(self, db_session):
        """Test booking when no seats available in the chosen class."""
        db_session.add(User(name="Test User", email="test@example.com"))
        db_session.add(Flight(
            origin="Earth",
            destination="Mars",
            departure_time="2099-01-01T09:00:00Z",
            arrival_time="2099-01-01T17:00:00Z",
            price=1000000,
            economy_seats=0,
            flexi_seats=5,
            business_seats=5,
            galaxium_seats=5
        ))
        db_session.commit()

        user_obj = db_session.query(User).first()
        flight_obj = db_session.query(Flight).first()

        result = booking.book_flight(db_session, user_obj.user_id, "Test User", flight_obj.flight_id, "economy")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "NO_SEATS_AVAILABLE"

    def test_book_flight_user_not_found(self, db_session):
        """Test booking with non-existent user."""
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
        flight_obj = db_session.query(Flight).first()

        result = booking.book_flight(db_session, 999, "Fake User", flight_obj.flight_id, "economy")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "USER_NOT_FOUND"

    def test_book_flight_name_mismatch(self, db_session):
        """Test booking with wrong name for user ID."""
        db_session.add(User(name="Real Name", email="test@example.com"))
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

        user_obj = db_session.query(User).first()
        flight_obj = db_session.query(Flight).first()

        result = booking.book_flight(db_session, user_obj.user_id, "Wrong Name", flight_obj.flight_id, "economy")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "NAME_MISMATCH"

    def test_book_flight_invalid_seat_class(self, db_session):
        """Test booking with an unknown seat class."""
        db_session.add(User(name="Test User", email="test@example.com"))
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

        user_obj = db_session.query(User).first()
        flight_obj = db_session.query(Flight).first()

        result = booking.book_flight(db_session, user_obj.user_id, "Test User", flight_obj.flight_id, "first")
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "INVALID_SEAT_CLASS"

    def test_cancel_booking_success(self, db_session):
        """Test successful booking cancellation."""
        db_session.add(User(name="Test User", email="test@example.com"))
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

        user_obj = db_session.query(User).first()
        flight_obj = db_session.query(Flight).first()

        db_session.add(Booking(
            user_id=user_obj.user_id,
            flight_id=flight_obj.flight_id,
            status="booked",
            booking_time="2099-01-01T10:00:00Z",
            seat_class="economy"
        ))
        db_session.commit()

        booking_obj = db_session.query(Booking).first()
        result = booking.cancel_booking(db_session, booking_obj.booking_id)

        assert result.status == "cancelled"

        # Verify seat was restored
        db_session.refresh(flight_obj)
        assert flight_obj.economy_seats == 5

    def test_cancel_booking_not_found(self, db_session):
        """Test cancelling non-existent booking."""
        result = booking.cancel_booking(db_session, 999)
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "BOOKING_NOT_FOUND"

    def test_cancel_booking_already_cancelled(self, db_session):
        """Test cancelling already cancelled booking."""
        db_session.add(User(name="Test User", email="test@example.com"))
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

        user_obj = db_session.query(User).first()
        flight_obj = db_session.query(Flight).first()

        db_session.add(Booking(
            user_id=user_obj.user_id,
            flight_id=flight_obj.flight_id,
            status="cancelled",
            booking_time="2099-01-01T10:00:00Z",
            seat_class="economy"
        ))
        db_session.commit()

        booking_obj = db_session.query(Booking).first()
        result = booking.cancel_booking(db_session, booking_obj.booking_id)

        assert isinstance(result, ErrorResponse)
        assert result.error_code == "ALREADY_CANCELLED"

    def test_get_bookings_success(self, db_session):
        """Test getting user bookings."""
        db_session.add(User(name="Test User", email="test@example.com"))
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

        user_obj = db_session.query(User).first()
        flight_obj = db_session.query(Flight).first()

        db_session.add(Booking(
            user_id=user_obj.user_id,
            flight_id=flight_obj.flight_id,
            status="booked",
            booking_time="2099-01-01T10:00:00Z",
            seat_class="economy"
        ))
        db_session.commit()

        result = booking.get_bookings(db_session, user_obj.user_id)
        assert len(result) == 1
        assert result[0].status == "booked"

    def test_get_bookings_empty(self, db_session):
        """Test getting bookings when user has none."""
        result = booking.get_bookings(db_session, 999)
        assert result == []


class TestRefundPreviewService:
    """Test booking.get_refund_preview."""

    @pytest.mark.parametrize("seat_class,class_price,refund,percent", [
        ("economy", 1000, 800, 80),
        ("flexi", 1500, 1500, 100),
        ("business", 3000, 2250, 75),
        ("galaxium", 6000, 6000, 100),
    ])
    def test_preview_long_notice_all_classes(
        self, db_session, make_flight, make_booking, seat_class, class_price, refund, percent
    ):
        """Test the preview with long notice returns the full class refund."""
        flight_obj = make_flight(hours_until_departure=24 * 30, price=1000)
        booking_obj = make_booking(flight_obj, seat_class)

        result = booking.get_refund_preview(db_session, booking_obj.booking_id)

        assert isinstance(result, RefundPreviewOut)
        assert result.booking_id == booking_obj.booking_id
        assert result.seat_class == seat_class
        assert result.class_price == class_price
        assert result.refund_amount == refund
        assert result.refund_percent == percent
        assert result.departure_time == flight_obj.departure_time

    def test_preview_economy_inside_cutoff_is_zero(self, db_session, make_flight, make_booking):
        """Test Economy inside 72h gives 0 refund but still reports the rule percentage."""
        booking_obj = make_booking(make_flight(hours_until_departure=48, price=1000), "economy")

        result = booking.get_refund_preview(db_session, booking_obj.booking_id)

        assert result.refund_amount == 0
        assert result.refund_percent == 80
        assert result.class_price == 1000

    def test_preview_flexi_inside_cutoff_is_zero(self, db_session, make_flight, make_booking):
        """Test Flexi inside 24h gives 0 refund but still reports the rule percentage."""
        booking_obj = make_booking(make_flight(hours_until_departure=10, price=1000), "flexi")

        result = booking.get_refund_preview(db_session, booking_obj.booking_id)

        assert result.refund_amount == 0
        assert result.refund_percent == 100

    def test_preview_business_and_galaxium_close_to_departure(self, db_session, make_flight, make_booking):
        """Test Business and Galaxium still refund an hour before departure."""
        flight_obj = make_flight(hours_until_departure=1, price=1000)
        business = make_booking(flight_obj, "business")
        galaxium = make_booking(flight_obj, "galaxium")

        assert booking.get_refund_preview(db_session, business.booking_id).refund_amount == 2250
        assert booking.get_refund_preview(db_session, galaxium.booking_id).refund_amount == 6000

    def test_preview_after_departure_is_zero(self, db_session, make_flight, make_booking):
        """Test a preview after departure gives 0 refund with the rule percentage."""
        booking_obj = make_booking(make_flight(hours_until_departure=-5, price=1000), "galaxium")

        result = booking.get_refund_preview(db_session, booking_obj.booking_id)

        assert result.refund_amount == 0
        assert result.refund_percent == 100

    def test_preview_does_not_change_data(self, db_session, make_flight, make_booking):
        """Test the preview leaves booking status, refund and seats unchanged."""
        flight_obj = make_flight(hours_until_departure=24 * 30)
        booking_obj = make_booking(flight_obj, "business")
        seats_before = _seats(flight_obj)

        booking.get_refund_preview(db_session, booking_obj.booking_id)

        db_session.refresh(flight_obj)
        db_session.refresh(booking_obj)
        assert booking_obj.status == "booked"
        assert booking_obj.refund_amount is None
        assert _seats(flight_obj) == seats_before

    def test_preview_booking_not_found(self, db_session):
        """Test the preview of an unknown booking."""
        result = booking.get_refund_preview(db_session, 999)
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "BOOKING_NOT_FOUND"

    def test_preview_already_cancelled(self, db_session, make_flight, make_booking):
        """Test the preview of a cancelled booking."""
        booking_obj = make_booking(make_flight(), "economy", status="cancelled")
        result = booking.get_refund_preview(db_session, booking_obj.booking_id)
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "ALREADY_CANCELLED"

    def test_preview_completed_not_cancellable(self, db_session, make_flight, make_booking):
        """Test the preview of a completed booking."""
        booking_obj = make_booking(make_flight(), "economy", status="completed")
        result = booking.get_refund_preview(db_session, booking_obj.booking_id)
        assert isinstance(result, ErrorResponse)
        assert result.error_code == "BOOKING_NOT_CANCELLABLE"

    def test_preview_flight_not_found(self, db_session, make_flight, make_booking):
        """Test the preview when the booking's flight no longer exists."""
        flight_obj = make_flight()
        booking_obj = make_booking(flight_obj, "economy")
        db_session.delete(flight_obj)
        db_session.commit()

        result = booking.get_refund_preview(db_session, booking_obj.booking_id)

        assert isinstance(result, ErrorResponse)
        assert result.error_code == "FLIGHT_NOT_FOUND"


class TestCancelRefundService:
    """Test refund behaviour of booking.cancel_booking."""

    @pytest.mark.parametrize("seat_class,refund", [
        ("economy", 800),
        ("flexi", 1500),
        ("business", 2250),
        ("galaxium", 6000),
    ])
    def test_cancel_stores_refund_and_restores_one_seat(
        self, db_session, make_flight, make_booking, seat_class, refund
    ):
        """Test cancel stores the refund and restores exactly one seat in the booked class."""
        flight_obj = make_flight(hours_until_departure=24 * 30, price=1000)
        booking_obj = make_booking(flight_obj, seat_class)
        seats_before = _seats(flight_obj)

        result = booking.cancel_booking(db_session, booking_obj.booking_id)

        assert result.status == "cancelled"
        assert result.refund_amount == refund
        db_session.refresh(booking_obj)
        db_session.refresh(flight_obj)
        assert booking_obj.refund_amount == refund
        expected = dict(seats_before)
        expected[seat_class] += 1
        assert _seats(flight_obj) == expected

    def test_cancel_inside_cutoff_stores_zero_and_restores_seat(self, db_session, make_flight, make_booking):
        """Test cancelling Economy inside 72h stores 0 and still restores the seat."""
        flight_obj = make_flight(hours_until_departure=48, price=1000)
        booking_obj = make_booking(flight_obj, "economy")

        result = booking.cancel_booking(db_session, booking_obj.booking_id)

        assert result.refund_amount == 0
        db_session.refresh(flight_obj)
        assert flight_obj.economy_seats == 6

    def test_cancel_after_departure_stores_zero(self, db_session, make_flight, make_booking):
        """Test cancelling after departure stores a 0 refund."""
        booking_obj = make_booking(make_flight(hours_until_departure=-5, price=1000), "business")
        result = booking.cancel_booking(db_session, booking_obj.booking_id)
        assert result.status == "cancelled"
        assert result.refund_amount == 0

    def test_cancel_completed_not_cancellable(self, db_session, make_flight, make_booking):
        """Test cancelling a completed booking is rejected and leaves seats unchanged."""
        flight_obj = make_flight()
        booking_obj = make_booking(flight_obj, "economy", status="completed")
        seats_before = _seats(flight_obj)

        result = booking.cancel_booking(db_session, booking_obj.booking_id)

        assert isinstance(result, ErrorResponse)
        assert result.error_code == "BOOKING_NOT_CANCELLABLE"
        db_session.refresh(flight_obj)
        db_session.refresh(booking_obj)
        assert _seats(flight_obj) == seats_before
        assert booking_obj.status == "completed"
        assert booking_obj.refund_amount is None

    def test_cancel_already_cancelled_does_not_restore_seat(self, db_session, make_flight, make_booking):
        """Test a second cancel is rejected and does not restore another seat."""
        flight_obj = make_flight()
        booking_obj = make_booking(flight_obj, "flexi")
        booking.cancel_booking(db_session, booking_obj.booking_id)
        db_session.refresh(flight_obj)
        seats_after_first = _seats(flight_obj)

        result = booking.cancel_booking(db_session, booking_obj.booking_id)

        assert isinstance(result, ErrorResponse)
        assert result.error_code == "ALREADY_CANCELLED"
        db_session.refresh(flight_obj)
        assert _seats(flight_obj) == seats_after_first
