"""Unit tests for the booking module."""

from datetime import date, timedelta

import pytest

from villa_mover.booking import (
    Booking,
    BookingManager,
    BookingStatus,
    TimeSlot,
)


@pytest.fixture
def manager():
    return BookingManager()


@pytest.fixture
def valid_date():
    return date.today() + timedelta(days=7)


@pytest.fixture
def sample_booking(manager, valid_date):
    return manager.create_booking(
        customer_id="CUST-00001",
        move_date=valid_date,
        time_slot=TimeSlot.MORNING,
        pickup_address="123 Al Rashidiya, Ajman",
        delivery_address="456 Al Nuaimiya, Ajman",
    )


class TestCreateBooking:
    def test_successful_creation(self, manager, valid_date):
        booking = manager.create_booking(
            customer_id="CUST-00001",
            move_date=valid_date,
            time_slot=TimeSlot.MORNING,
            pickup_address="123 Al Rashidiya, Ajman",
            delivery_address="456 Al Nuaimiya, Ajman",
        )
        assert booking.status == BookingStatus.PENDING
        assert booking.customer_id == "CUST-00001"
        assert booking.move_date == valid_date
        assert booking.booking_id

    def test_past_date_raises(self, manager):
        with pytest.raises(ValueError, match="past"):
            manager.create_booking(
                customer_id="CUST-00001",
                move_date=date.today() - timedelta(days=1),
                time_slot=TimeSlot.MORNING,
                pickup_address="123 Al Rashidiya, Ajman",
                delivery_address="456 Al Nuaimiya, Ajman",
            )

    def test_same_day_raises(self, manager):
        with pytest.raises(ValueError, match="24 hours"):
            manager.create_booking(
                customer_id="CUST-00001",
                move_date=date.today(),
                time_slot=TimeSlot.MORNING,
                pickup_address="123 Al Rashidiya, Ajman",
                delivery_address="456 Al Nuaimiya, Ajman",
            )

    def test_too_far_in_advance_raises(self, manager):
        with pytest.raises(ValueError, match="90 days"):
            manager.create_booking(
                customer_id="CUST-00001",
                move_date=date.today() + timedelta(days=91),
                time_slot=TimeSlot.MORNING,
                pickup_address="123 Al Rashidiya, Ajman",
                delivery_address="456 Al Nuaimiya, Ajman",
            )

    def test_empty_pickup_raises(self, manager, valid_date):
        with pytest.raises(ValueError, match="Pickup address"):
            manager.create_booking(
                customer_id="CUST-00001",
                move_date=valid_date,
                time_slot=TimeSlot.MORNING,
                pickup_address="",
                delivery_address="456 Al Nuaimiya, Ajman",
            )

    def test_empty_delivery_raises(self, manager, valid_date):
        with pytest.raises(ValueError, match="Delivery address"):
            manager.create_booking(
                customer_id="CUST-00001",
                move_date=valid_date,
                time_slot=TimeSlot.MORNING,
                pickup_address="123 Al Rashidiya, Ajman",
                delivery_address="",
            )

    def test_same_addresses_raises(self, manager, valid_date):
        with pytest.raises(ValueError, match="must be different"):
            manager.create_booking(
                customer_id="CUST-00001",
                move_date=valid_date,
                time_slot=TimeSlot.MORNING,
                pickup_address="123 Al Rashidiya, Ajman",
                delivery_address="123 Al Rashidiya, Ajman",
            )

    def test_slot_fully_booked_raises(self, manager, valid_date):
        for i in range(3):
            manager.create_booking(
                customer_id=f"CUST-{i:05d}",
                move_date=valid_date,
                time_slot=TimeSlot.MORNING,
                pickup_address=f"{i} Pickup St, Ajman",
                delivery_address=f"{i} Delivery St, Ajman",
            )
        with pytest.raises(ValueError, match="fully booked"):
            manager.create_booking(
                customer_id="CUST-99999",
                move_date=valid_date,
                time_slot=TimeSlot.MORNING,
                pickup_address="99 Pickup St, Ajman",
                delivery_address="99 Delivery St, Ajman",
            )

    def test_with_notes_and_cost(self, manager, valid_date):
        booking = manager.create_booking(
            customer_id="CUST-00001",
            move_date=valid_date,
            time_slot=TimeSlot.AFTERNOON,
            pickup_address="123 Al Rashidiya, Ajman",
            delivery_address="456 Al Nuaimiya, Ajman",
            notes="Handle with care",
            estimated_cost=1500.0,
        )
        assert booking.notes == "Handle with care"
        assert booking.estimated_cost == 1500.0


class TestBookingLifecycle:
    def test_confirm_booking(self, manager, sample_booking):
        confirmed = manager.confirm_booking(sample_booking.booking_id)
        assert confirmed.status == BookingStatus.CONFIRMED

    def test_confirm_non_pending_raises(self, manager, sample_booking):
        manager.confirm_booking(sample_booking.booking_id)
        with pytest.raises(ValueError, match="Cannot confirm"):
            manager.confirm_booking(sample_booking.booking_id)

    def test_start_confirmed_booking(self, manager, sample_booking):
        manager.confirm_booking(sample_booking.booking_id)
        started = manager.start_booking(sample_booking.booking_id)
        assert started.status == BookingStatus.IN_PROGRESS

    def test_start_pending_raises(self, manager, sample_booking):
        with pytest.raises(ValueError, match="Cannot start"):
            manager.start_booking(sample_booking.booking_id)

    def test_complete_in_progress_booking(self, manager, sample_booking):
        manager.confirm_booking(sample_booking.booking_id)
        manager.start_booking(sample_booking.booking_id)
        completed = manager.complete_booking(sample_booking.booking_id)
        assert completed.status == BookingStatus.COMPLETED

    def test_complete_not_in_progress_raises(self, manager, sample_booking):
        with pytest.raises(ValueError, match="Cannot complete"):
            manager.complete_booking(sample_booking.booking_id)

    def test_cancel_pending_booking(self, manager, sample_booking):
        cancelled = manager.cancel_booking(sample_booking.booking_id, "Changed plans")
        assert cancelled.status == BookingStatus.CANCELLED
        assert "Changed plans" in cancelled.notes

    def test_cancel_confirmed_booking(self, manager, sample_booking):
        manager.confirm_booking(sample_booking.booking_id)
        cancelled = manager.cancel_booking(sample_booking.booking_id)
        assert cancelled.status == BookingStatus.CANCELLED

    def test_cancel_in_progress_raises(self, manager, sample_booking):
        manager.confirm_booking(sample_booking.booking_id)
        manager.start_booking(sample_booking.booking_id)
        with pytest.raises(ValueError, match="already in progress"):
            manager.cancel_booking(sample_booking.booking_id)

    def test_cancel_completed_raises(self, manager, sample_booking):
        manager.confirm_booking(sample_booking.booking_id)
        manager.start_booking(sample_booking.booking_id)
        manager.complete_booking(sample_booking.booking_id)
        with pytest.raises(ValueError, match="Cannot cancel"):
            manager.cancel_booking(sample_booking.booking_id)

    def test_nonexistent_booking_raises(self, manager):
        with pytest.raises(KeyError, match="not found"):
            manager.confirm_booking("nonexistent-id")


class TestRescheduleBooking:
    def test_reschedule_pending(self, manager, sample_booking):
        new_date = date.today() + timedelta(days=14)
        rescheduled = manager.reschedule_booking(
            sample_booking.booking_id, new_date, TimeSlot.EVENING
        )
        assert rescheduled.move_date == new_date
        assert rescheduled.time_slot == TimeSlot.EVENING

    def test_reschedule_confirmed(self, manager, sample_booking):
        manager.confirm_booking(sample_booking.booking_id)
        new_date = date.today() + timedelta(days=14)
        rescheduled = manager.reschedule_booking(
            sample_booking.booking_id, new_date, TimeSlot.AFTERNOON
        )
        assert rescheduled.move_date == new_date

    def test_reschedule_in_progress_raises(self, manager, sample_booking):
        manager.confirm_booking(sample_booking.booking_id)
        manager.start_booking(sample_booking.booking_id)
        with pytest.raises(ValueError, match="Cannot reschedule"):
            manager.reschedule_booking(
                sample_booking.booking_id,
                date.today() + timedelta(days=14),
                TimeSlot.EVENING,
            )


class TestBookingQueries:
    def test_get_bookings_for_date(self, manager, valid_date):
        manager.create_booking(
            customer_id="CUST-00001",
            move_date=valid_date,
            time_slot=TimeSlot.MORNING,
            pickup_address="1 Pickup St, Ajman",
            delivery_address="1 Delivery St, Ajman",
        )
        manager.create_booking(
            customer_id="CUST-00002",
            move_date=valid_date,
            time_slot=TimeSlot.AFTERNOON,
            pickup_address="2 Pickup St, Ajman",
            delivery_address="2 Delivery St, Ajman",
        )
        bookings = manager.get_bookings_for_date(valid_date)
        assert len(bookings) == 2

    def test_get_bookings_excludes_cancelled(self, manager, valid_date):
        booking = manager.create_booking(
            customer_id="CUST-00001",
            move_date=valid_date,
            time_slot=TimeSlot.MORNING,
            pickup_address="1 Pickup St, Ajman",
            delivery_address="1 Delivery St, Ajman",
        )
        manager.cancel_booking(booking.booking_id)
        bookings = manager.get_bookings_for_date(valid_date)
        assert len(bookings) == 0

    def test_get_customer_bookings(self, manager, valid_date):
        manager.create_booking(
            customer_id="CUST-00001",
            move_date=valid_date,
            time_slot=TimeSlot.MORNING,
            pickup_address="1 Pickup St, Ajman",
            delivery_address="1 Delivery St, Ajman",
        )
        manager.create_booking(
            customer_id="CUST-00001",
            move_date=valid_date,
            time_slot=TimeSlot.AFTERNOON,
            pickup_address="2 Pickup St, Ajman",
            delivery_address="2 Delivery St, Ajman",
        )
        bookings = manager.get_customer_bookings("CUST-00001")
        assert len(bookings) == 2

    def test_bookings_property_returns_copy(self, manager, sample_booking):
        bookings = manager.bookings
        bookings.clear()
        assert len(manager.bookings) == 1
