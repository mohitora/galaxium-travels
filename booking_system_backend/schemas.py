from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional, Literal

# Seat class multipliers — single source of truth for the backend
SEAT_CLASS_MULTIPLIERS: dict[str, float] = {
    "economy": 1.0,
    "flexi": 1.5,
    "business": 3.0,
    "galaxium": 6.0,
}

# Refund rules per seat class — single source of truth for cancellations.
# refund_percent: share of the class price refunded.
# cutoff_hours: refund only if cancelled MORE than this many hours before departure;
# None means any time before departure.
REFUND_RULES: dict[str, dict[str, Optional[int]]] = {
    "economy": {"refund_percent": 80, "cutoff_hours": 72},
    "flexi": {"refund_percent": 100, "cutoff_hours": 24},
    "business": {"refund_percent": 75, "cutoff_hours": None},
    "galaxium": {"refund_percent": 100, "cutoff_hours": None},
}


def parse_departure_time(value: str) -> datetime:
    """Parse an ISO departure string (with optional 'Z') into an aware UTC datetime."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def calculate_refund(
    seat_class: str, base_price: int, departure_time: str, now: datetime
) -> int:
    """Return the refund for a cancellation at `now`; 0 at/inside the cutoff or after departure."""
    rule = REFUND_RULES[seat_class]
    class_price = round(base_price * SEAT_CLASS_MULTIPLIERS[seat_class])
    time_left = parse_departure_time(departure_time) - now
    if time_left <= timedelta(0):
        return 0
    cutoff_hours = rule["cutoff_hours"]
    if cutoff_hours is not None and time_left <= timedelta(hours=cutoff_hours):
        return 0
    return round(class_price * rule["refund_percent"] / 100)


class FlightOut(BaseModel):
    flight_id: int
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price: int
    economy_seats: int
    flexi_seats: int
    business_seats: int
    galaxium_seats: int
    # Computed per-class prices (derived at serialisation time, not stored in DB)
    economy_price: int = 0
    flexi_price: int = 0
    business_price: int = 0
    galaxium_price: int = 0

    @model_validator(mode="after")
    def compute_class_prices(self) -> "FlightOut":
        self.economy_price = round(self.price * SEAT_CLASS_MULTIPLIERS["economy"])
        self.flexi_price = round(self.price * SEAT_CLASS_MULTIPLIERS["flexi"])
        self.business_price = round(self.price * SEAT_CLASS_MULTIPLIERS["business"])
        self.galaxium_price = round(self.price * SEAT_CLASS_MULTIPLIERS["galaxium"])
        return self

    class Config:
        from_attributes = True


class BookingRequest(BaseModel):
    user_id: int
    name: str
    flight_id: int
    seat_class: Literal["economy", "flexi", "business", "galaxium"]


class BookingOut(BaseModel):
    booking_id: int
    user_id: int
    flight_id: int
    status: str
    booking_time: str
    seat_class: str
    refund_amount: Optional[int] = None

    class Config:
        from_attributes = True


class RefundPreviewOut(BaseModel):
    booking_id: int
    seat_class: str
    class_price: int
    refund_amount: int
    refund_percent: int
    departure_time: str


class UserRegistration(BaseModel):
    name: str
    email: EmailStr


class UserOut(BaseModel):
    user_id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: str
    details: Optional[str] = None
