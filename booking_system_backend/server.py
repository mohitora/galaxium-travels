from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from sqlalchemy.orm import Session
from typing import Union
from db import SessionLocal, init_db, get_db
from seed import seed
from services import flight, user, booking
from schemas import FlightOut, BookingOut, UserOut, ErrorResponse, BookingRequest, UserRegistration, RefundPreviewOut


# ==================== MCP SERVER (for AI agents) ====================
# NOTE: MCP server must be created before FastAPI app to properly combine lifespans

mcp = FastMCP("Galaxium Booking System")


@mcp.tool()
def list_flights() -> list[FlightOut]:
    """List all available flights.
    Returns a list of flights with origin, destination, times, price, and seats available."""
    db = SessionLocal()
    try:
        return flight.list_flights(db)
    finally:
        db.close()


@mcp.tool()
def book_flight(user_id: int, name: str, flight_id: int, seat_class: str) -> BookingOut:
    """Book a seat of a specific class on a flight for a user.
    Requires user_id, name, flight_id, and seat_class (economy, flexi, business, or galaxium).
    Decrements available seats for the chosen class if successful.
    Returns booking details or raises an error if booking is not possible."""
    db = SessionLocal()
    try:
        result = booking.book_flight(db, user_id, name, flight_id, seat_class)
        if isinstance(result, ErrorResponse):
            raise Exception(result.details or result.error)
        return result
    finally:
        db.close()


@mcp.tool()
def get_bookings(user_id: int) -> list[BookingOut]:
    """Retrieve all bookings for a specific user by user_id.
    Returns a list of booking details for the user."""
    db = SessionLocal()
    try:
        return booking.get_bookings(db, user_id)
    finally:
        db.close()


@mcp.tool()
def get_refund_preview(booking_id: int) -> RefundPreviewOut:
    """Preview the refund for cancelling a booked booking now, without cancelling it.
    Returns booking_id, seat_class, class_price, refund_amount, refund_percent and departure_time.
    refund_percent is the class rule; refund_amount is 0 when no refund applies now.
    Raises an error if the booking is not found, already cancelled, or not cancellable."""
    db = SessionLocal()
    try:
        result = booking.get_refund_preview(db, booking_id)
        if isinstance(result, ErrorResponse):
            raise Exception(result.details or result.error)
        return result
    finally:
        db.close()


@mcp.tool()
def cancel_booking(booking_id: int) -> BookingOut:
    """Cancel a booked booking by its booking_id and refund it per its seat class fare rules.
    Restores one seat to the flight and stores the refund on the booking.
    Returns updated booking details including refund_amount (use get_refund_preview first to see it).
    Raises an error: BOOKING_NOT_FOUND, ALREADY_CANCELLED, or BOOKING_NOT_CANCELLABLE (e.g. completed)."""
    db = SessionLocal()
    try:
        result = booking.cancel_booking(db, booking_id)
        if isinstance(result, ErrorResponse):
            raise Exception(result.details or result.error)
        return result
    finally:
        db.close()


@mcp.tool()
def register_user(name: str, email: str) -> UserOut:
    """Register a new user with a name and unique email.
    Returns the created user's details or raises an error if the email is already registered."""
    db = SessionLocal()
    try:
        result = user.register_user(db, name, email)
        if isinstance(result, ErrorResponse):
            raise Exception(result.details or result.error)
        return result
    finally:
        db.close()


@mcp.tool()
def get_user_id(name: str, email: str) -> UserOut:
    """Retrieve a user's information, including user_id, by providing both name and email.
    Returns user details or raises an error if not found."""
    db = SessionLocal()
    try:
        result = user.get_user(db, name, email)
        if isinstance(result, ErrorResponse):
            raise Exception(result.details or result.error)
        return result
    finally:
        db.close()


# Create the MCP HTTP app for mounting
mcp_app = mcp.http_app()


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    seed()
    yield
    # Shutdown (nothing to do)


# ==================== FASTAPI APP (REST + Swagger UI) ====================

app = FastAPI(
    title="Galaxium Booking System",
    description="API for booking interplanetary flights. Swagger UI available at /docs",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "OK"}


@app.get("/flights", response_model=list[FlightOut], tags=["Flights"])
def get_flights(db: Session = Depends(get_db)):
    """List all available flights with origin, destination, times, price, and seats available."""
    return flight.list_flights(db)


@app.post("/book", response_model=Union[BookingOut, ErrorResponse], tags=["Bookings"])
def book_flight_endpoint(request: BookingRequest, db: Session = Depends(get_db)):
    """Book a seat of a specific class on a flight for a user.

    Requires user_id, name, flight_id, and seat_class. Decrements seats for the chosen class if successful.
    """
    return booking.book_flight(db, request.user_id, request.name, request.flight_id, request.seat_class)


@app.get("/bookings/{user_id}", response_model=list[BookingOut], tags=["Bookings"])
def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    """Retrieve all bookings for a specific user by user_id."""
    return booking.get_bookings(db, user_id)


@app.post("/cancel/{booking_id}", response_model=Union[BookingOut, ErrorResponse], tags=["Bookings"])
def cancel_booking_endpoint(booking_id: int, db: Session = Depends(get_db)):
    """Cancel a booked booking by its booking_id and refund it per its seat class fare rules.

    Restores one seat and returns the booking with refund_amount.
    Errors: BOOKING_NOT_FOUND, ALREADY_CANCELLED, BOOKING_NOT_CANCELLABLE.
    """
    return booking.cancel_booking(db, booking_id)


@app.get("/refund-preview/{booking_id}", response_model=Union[RefundPreviewOut, ErrorResponse], tags=["Bookings"])
def refund_preview_endpoint(booking_id: int, db: Session = Depends(get_db)):
    """Preview the refund for cancelling a booked booking now, without cancelling it.

    Returns booking_id, seat_class, class_price, refund_amount, refund_percent and departure_time.
    refund_percent is the class rule; refund_amount is 0 when no refund applies now.
    Errors: BOOKING_NOT_FOUND, ALREADY_CANCELLED, BOOKING_NOT_CANCELLABLE, FLIGHT_NOT_FOUND.
    """
    return booking.get_refund_preview(db, booking_id)


@app.post("/register", response_model=Union[UserOut, ErrorResponse], tags=["Users"])
def register_user_endpoint(request: UserRegistration, db: Session = Depends(get_db)):
    """Register a new user with a name and unique email."""
    return user.register_user(db, request.name, request.email)


@app.get("/user", response_model=Union[UserOut, ErrorResponse], tags=["Users"])
def get_user_endpoint(name: str, email: str, db: Session = Depends(get_db)):
    """Retrieve a user's information by providing both name and email."""
    return user.get_user(db, name, email)


# ==================== MOUNT MCP INTO FASTAPI ====================

app.mount("/mcp", mcp_app)


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
