from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
from models import User, Flight, Booking
from schemas import (
    BookingOut,
    ErrorResponse,
    RefundPreviewOut,
    REFUND_RULES,
    SEAT_CLASS_MULTIPLIERS,
    calculate_refund,
)


def _seat_attr(seat_class: str) -> str:
    """Return the Flight attribute name for the given seat class."""
    return f"{seat_class}_seats"


def _compute_refund(flight: Flight, seat_class: str, now: Optional[datetime] = None) -> int:
    """Calculate the refund amount for a booking given its flight and seat class."""
    if now is None:
        now = datetime.now(timezone.utc)
    return calculate_refund(
        seat_class=seat_class,
        base_price=flight.price,
        departure_time=flight.departure_time,
        now=now,
    )


def book_flight(db: Session, user_id: int, name: str, flight_id: int, seat_class: str) -> BookingOut | ErrorResponse:
    """Book a seat of a specific class on a flight for a user."""

    # Validate seat class
    if seat_class not in SEAT_CLASS_MULTIPLIERS:
        return ErrorResponse(
            error="Invalid seat class",
            error_code="INVALID_SEAT_CLASS",
            details=f"'{seat_class}' is not a valid seat class. Valid options are: {', '.join(SEAT_CLASS_MULTIPLIERS)}."
        )

    # Check flight exists
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    if not flight:
        return ErrorResponse(
            error="Flight not found",
            error_code="FLIGHT_NOT_FOUND",
            details=f"The specified flight_id {flight_id} does not exist in our system. Please check the flight_id or use list_flights to see available flights."
        )

    # Check seats available for the requested class
    seats_remaining = getattr(flight, _seat_attr(seat_class))
    if seats_remaining < 1:
        return ErrorResponse(
            error="No seats available",
            error_code="NO_SEATS_AVAILABLE",
            details=f"The {seat_class} class on this flight is fully booked. Please choose a different class or flight."
        )

    # Check user exists and name matches
    user = db.query(User).filter(User.user_id == user_id, User.name == name).first()
    if not user:
        existing_user = db.query(User).filter(User.user_id == user_id).first()
        if existing_user:
            return ErrorResponse(
                error="Name mismatch",
                error_code="NAME_MISMATCH",
                details=f"User ID {user_id} exists but the name '{name}' does not match the registered name '{existing_user.name}'. Please verify the user's name or use the correct name for this user ID."
            )
        else:
            return ErrorResponse(
                error="User not found",
                error_code="USER_NOT_FOUND",
                details=f"User with ID {user_id} is not registered in our system. The user might need to register first, or you may need to check if the user_id is correct."
            )

    # Decrement seat count for the chosen class
    setattr(flight, _seat_attr(seat_class), seats_remaining - 1)

    new_booking = Booking(
        user_id=user_id,
        flight_id=flight_id,
        status="booked",
        booking_time=datetime.utcnow().isoformat(),
        seat_class=seat_class,
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return BookingOut.model_validate(new_booking)


def get_refund_preview(db: Session, booking_id: int) -> RefundPreviewOut | ErrorResponse:
    """Preview the refund amount and policy details for cancelling a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        return ErrorResponse(
            error="Booking not found",
            error_code="BOOKING_NOT_FOUND",
            details=f"Booking with ID {booking_id} not found. The booking may have been deleted or the booking_id may be incorrect. Please verify the booking_id or check if the booking exists."
        )

    if booking.status == "cancelled":
        return ErrorResponse(
            error="Booking already cancelled",
            error_code="ALREADY_CANCELLED",
            details=f"Booking {booking_id} is already cancelled and cannot be previewed for refund."
        )

    if booking.status != "booked":
        return ErrorResponse(
            error="Booking not cancellable",
            error_code="BOOKING_NOT_CANCELLABLE",
            details=f"Booking {booking_id} has status '{booking.status}' and cannot be cancelled or previewed for refund."
        )

    flight = db.query(Flight).filter(Flight.flight_id == booking.flight_id).first()
    if not flight:
        return ErrorResponse(
            error="Flight not found",
            error_code="FLIGHT_NOT_FOUND",
            details=f"The flight associated with booking {booking_id} does not exist in our system."
        )

    seat_class = booking.seat_class
    class_price = round(flight.price * SEAT_CLASS_MULTIPLIERS[seat_class])
    refund_amount = _compute_refund(flight, seat_class)
    refund_percent = REFUND_RULES[seat_class]["refund_percent"]

    return RefundPreviewOut(
        booking_id=booking.booking_id,
        seat_class=seat_class,
        class_price=class_price,
        refund_amount=refund_amount,
        refund_percent=refund_percent,
        departure_time=flight.departure_time,
    )


def cancel_booking(db: Session, booking_id: int) -> BookingOut | ErrorResponse:
    """Cancel an existing booking by its booking_id."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        return ErrorResponse(
            error="Booking not found",
            error_code="BOOKING_NOT_FOUND",
            details=f"Booking with ID {booking_id} not found. The booking may have been deleted or the booking_id may be incorrect. Please verify the booking_id or check if the booking exists."
        )

    if booking.status == "cancelled":
        return ErrorResponse(
            error="Booking already cancelled",
            error_code="ALREADY_CANCELLED",
            details=f"Booking {booking_id} is already cancelled and cannot be cancelled again. The booking status is currently '{booking.status}'. If you need to make changes, please contact support."
        )

    if booking.status != "booked":
        return ErrorResponse(
            error="Booking not cancellable",
            error_code="BOOKING_NOT_CANCELLABLE",
            details=f"Booking {booking_id} has status '{booking.status}' and cannot be cancelled."
        )

    # Restore seat to the correct class and compute refund
    flight = db.query(Flight).filter(Flight.flight_id == booking.flight_id).first()
    refund_amount = 0
    if flight:
        attr = _seat_attr(booking.seat_class)
        setattr(flight, attr, getattr(flight, attr) + 1)
        refund_amount = _compute_refund(flight, booking.seat_class)

    booking.refund_amount = refund_amount
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return BookingOut.model_validate(booking)


def get_bookings(db: Session, user_id: int) -> list[BookingOut]:
    """Retrieve all bookings for a specific user."""
    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
    return [BookingOut.model_validate(b) for b in bookings]
