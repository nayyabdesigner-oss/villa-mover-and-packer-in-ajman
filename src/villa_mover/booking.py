"""Booking and scheduling management for moving services."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional
import uuid


class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TimeSlot(Enum):
    MORNING = "morning"  # 8:00 - 12:00
    AFTERNOON = "afternoon"  # 12:00 - 16:00
    EVENING = "evening"  # 16:00 - 20:00


@dataclass
class Booking:
    customer_id: str
    move_date: date
    time_slot: TimeSlot
    pickup_address: str
    delivery_address: str
    booking_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: BookingStatus = BookingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
    estimated_cost: float = 0.0


class BookingManager:
    """Manages booking lifecycle and scheduling."""

    MAX_BOOKINGS_PER_SLOT = 3

    def __init__(self):
        self._bookings: dict[str, Booking] = {}

    @property
    def bookings(self) -> dict[str, Booking]:
        return self._bookings.copy()

    def create_booking(
        self,
        customer_id: str,
        move_date: date,
        time_slot: TimeSlot,
        pickup_address: str,
        delivery_address: str,
        notes: str = "",
        estimated_cost: float = 0.0,
    ) -> Booking:
        """Create a new booking after validating constraints."""
        self._validate_booking_date(move_date)
        self._validate_addresses(pickup_address, delivery_address)
        self._check_slot_availability(move_date, time_slot)

        booking = Booking(
            customer_id=customer_id,
            move_date=move_date,
            time_slot=time_slot,
            pickup_address=pickup_address,
            delivery_address=delivery_address,
            notes=notes,
            estimated_cost=estimated_cost,
        )
        self._bookings[booking.booking_id] = booking
        return booking

    def confirm_booking(self, booking_id: str) -> Booking:
        """Confirm a pending booking."""
        booking = self._get_booking(booking_id)
        if booking.status != BookingStatus.PENDING:
            raise ValueError(f"Cannot confirm booking with status: {booking.status.value}")
        booking.status = BookingStatus.CONFIRMED
        return booking

    def cancel_booking(self, booking_id: str, reason: str = "") -> Booking:
        """Cancel a booking if it hasn't started."""
        booking = self._get_booking(booking_id)
        if booking.status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
            raise ValueError(f"Cannot cancel booking with status: {booking.status.value}")
        if booking.status == BookingStatus.IN_PROGRESS:
            raise ValueError("Cannot cancel a booking that is already in progress")
        booking.status = BookingStatus.CANCELLED
        if reason:
            booking.notes = f"{booking.notes}\nCancellation reason: {reason}".strip()
        return booking

    def start_booking(self, booking_id: str) -> Booking:
        """Mark booking as in progress."""
        booking = self._get_booking(booking_id)
        if booking.status != BookingStatus.CONFIRMED:
            raise ValueError(f"Cannot start booking with status: {booking.status.value}")
        booking.status = BookingStatus.IN_PROGRESS
        return booking

    def complete_booking(self, booking_id: str) -> Booking:
        """Mark booking as completed."""
        booking = self._get_booking(booking_id)
        if booking.status != BookingStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete booking with status: {booking.status.value}")
        booking.status = BookingStatus.COMPLETED
        return booking

    def reschedule_booking(self, booking_id: str, new_date: date, new_slot: TimeSlot) -> Booking:
        """Reschedule a pending or confirmed booking."""
        booking = self._get_booking(booking_id)
        if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            raise ValueError(f"Cannot reschedule booking with status: {booking.status.value}")
        self._validate_booking_date(new_date)
        self._check_slot_availability(new_date, new_slot)
        booking.move_date = new_date
        booking.time_slot = new_slot
        return booking

    def get_bookings_for_date(self, target_date: date) -> list[Booking]:
        """Get all bookings scheduled for a specific date."""
        return [b for b in self._bookings.values() if b.move_date == target_date and b.status != BookingStatus.CANCELLED]

    def get_customer_bookings(self, customer_id: str) -> list[Booking]:
        """Get all bookings for a customer."""
        return [b for b in self._bookings.values() if b.customer_id == customer_id]

    def _get_booking(self, booking_id: str) -> Booking:
        if booking_id not in self._bookings:
            raise KeyError(f"Booking not found: {booking_id}")
        return self._bookings[booking_id]

    def _validate_booking_date(self, move_date: date) -> None:
        today = date.today()
        if move_date < today:
            raise ValueError("Cannot book a move in the past")
        if move_date < today + timedelta(days=1):
            raise ValueError("Bookings require at least 24 hours notice")
        if move_date > today + timedelta(days=90):
            raise ValueError("Cannot book more than 90 days in advance")

    def _validate_addresses(self, pickup: str, delivery: str) -> None:
        if not pickup or not pickup.strip():
            raise ValueError("Pickup address is required")
        if not delivery or not delivery.strip():
            raise ValueError("Delivery address is required")
        if pickup.strip() == delivery.strip():
            raise ValueError("Pickup and delivery addresses must be different")

    def _check_slot_availability(self, move_date: date, time_slot: TimeSlot) -> None:
        existing = [
            b for b in self._bookings.values()
            if b.move_date == move_date
            and b.time_slot == time_slot
            and b.status not in (BookingStatus.CANCELLED,)
        ]
        if len(existing) >= self.MAX_BOOKINGS_PER_SLOT:
            raise ValueError(f"Time slot {time_slot.value} on {move_date} is fully booked")
