"""Unit tests for the customer module."""

import pytest

from villa_mover.customer import Customer, CustomerManager


@pytest.fixture
def manager():
    return CustomerManager()


@pytest.fixture
def sample_customer(manager):
    return manager.register_customer(
        name="Ahmed Al Maktoum",
        email="ahmed@example.com",
        phone="+971501234567",
        address="Villa 12, Al Rashidiya, Ajman, UAE",
    )


class TestRegisterCustomer:
    def test_successful_registration(self, manager):
        customer = manager.register_customer(
            name="Ahmed Al Maktoum",
            email="ahmed@example.com",
            phone="+971501234567",
            address="Villa 12, Al Rashidiya, Ajman, UAE",
        )
        assert customer.customer_id == "CUST-00001"
        assert customer.name == "Ahmed Al Maktoum"
        assert customer.email == "ahmed@example.com"
        assert customer.is_active is True
        assert customer.total_bookings == 0

    def test_sequential_ids(self, manager):
        c1 = manager.register_customer(
            name="Customer One",
            email="c1@example.com",
            phone="+971501111111",
            address="Address One, Ajman, UAE",
        )
        c2 = manager.register_customer(
            name="Customer Two",
            email="c2@example.com",
            phone="+971502222222",
            address="Address Two, Ajman, UAE",
        )
        assert c1.customer_id == "CUST-00001"
        assert c2.customer_id == "CUST-00002"

    def test_email_normalized_lowercase(self, manager):
        customer = manager.register_customer(
            name="Test User",
            email="Test.User@EXAMPLE.com",
            phone="+971501234567",
            address="Villa 12, Al Rashidiya, Ajman, UAE",
        )
        assert customer.email == "test.user@example.com"

    def test_phone_normalized(self, manager):
        customer = manager.register_customer(
            name="Test User",
            email="test@example.com",
            phone="+971 50 123 4567",
            address="Villa 12, Al Rashidiya, Ajman, UAE",
        )
        assert customer.phone == "+971501234567"

    def test_empty_name_raises(self, manager):
        with pytest.raises(ValueError, match="name is required"):
            manager.register_customer(
                name="",
                email="test@example.com",
                phone="+971501234567",
                address="Villa 12, Al Rashidiya, Ajman, UAE",
            )

    def test_short_name_raises(self, manager):
        with pytest.raises(ValueError, match="at least 2 characters"):
            manager.register_customer(
                name="A",
                email="test@example.com",
                phone="+971501234567",
                address="Villa 12, Al Rashidiya, Ajman, UAE",
            )

    def test_invalid_email_raises(self, manager):
        with pytest.raises(ValueError, match="Invalid email"):
            manager.register_customer(
                name="Test User",
                email="not-an-email",
                phone="+971501234567",
                address="Villa 12, Al Rashidiya, Ajman, UAE",
            )

    def test_empty_email_raises(self, manager):
        with pytest.raises(ValueError, match="Email is required"):
            manager.register_customer(
                name="Test User",
                email="",
                phone="+971501234567",
                address="Villa 12, Al Rashidiya, Ajman, UAE",
            )

    def test_invalid_phone_raises(self, manager):
        with pytest.raises(ValueError, match="Invalid phone"):
            manager.register_customer(
                name="Test User",
                email="test@example.com",
                phone="123",
                address="Villa 12, Al Rashidiya, Ajman, UAE",
            )

    def test_empty_phone_raises(self, manager):
        with pytest.raises(ValueError, match="Phone number is required"):
            manager.register_customer(
                name="Test User",
                email="test@example.com",
                phone="",
                address="Villa 12, Al Rashidiya, Ajman, UAE",
            )

    def test_short_address_raises(self, manager):
        with pytest.raises(ValueError, match="at least 10 characters"):
            manager.register_customer(
                name="Test User",
                email="test@example.com",
                phone="+971501234567",
                address="Short",
            )

    def test_duplicate_email_raises(self, manager, sample_customer):
        with pytest.raises(ValueError, match="already registered"):
            manager.register_customer(
                name="Another User",
                email="ahmed@example.com",
                phone="+971509999999",
                address="Another Address, Ajman, UAE",
            )


class TestGetCustomer:
    def test_get_existing(self, manager, sample_customer):
        result = manager.get_customer(sample_customer.customer_id)
        assert result.name == "Ahmed Al Maktoum"

    def test_get_nonexistent_raises(self, manager):
        with pytest.raises(KeyError, match="not found"):
            manager.get_customer("CUST-99999")


class TestFindCustomer:
    def test_find_by_email(self, manager, sample_customer):
        result = manager.find_by_email("ahmed@example.com")
        assert result is not None
        assert result.customer_id == sample_customer.customer_id

    def test_find_by_email_case_insensitive(self, manager, sample_customer):
        result = manager.find_by_email("AHMED@EXAMPLE.COM")
        assert result is not None

    def test_find_by_email_not_found(self, manager):
        result = manager.find_by_email("nobody@example.com")
        assert result is None

    def test_find_by_phone(self, manager, sample_customer):
        result = manager.find_by_phone("+971501234567")
        assert result is not None
        assert result.customer_id == sample_customer.customer_id

    def test_find_by_phone_not_found(self, manager):
        result = manager.find_by_phone("+971500000000")
        assert result is None


class TestUpdateCustomer:
    def test_update_name(self, manager, sample_customer):
        updated = manager.update_customer(sample_customer.customer_id, name="New Name")
        assert updated.name == "New Name"

    def test_update_email(self, manager, sample_customer):
        updated = manager.update_customer(sample_customer.customer_id, email="new@example.com")
        assert updated.email == "new@example.com"

    def test_update_email_duplicate_raises(self, manager, sample_customer):
        manager.register_customer(
            name="Other User",
            email="other@example.com",
            phone="+971509999999",
            address="Another Address, Ajman, UAE",
        )
        with pytest.raises(ValueError, match="already registered"):
            manager.update_customer(sample_customer.customer_id, email="other@example.com")

    def test_update_same_email_no_error(self, manager, sample_customer):
        updated = manager.update_customer(sample_customer.customer_id, email="ahmed@example.com")
        assert updated.email == "ahmed@example.com"

    def test_update_phone(self, manager, sample_customer):
        updated = manager.update_customer(sample_customer.customer_id, phone="+971559876543")
        assert updated.phone == "+971559876543"

    def test_update_address(self, manager, sample_customer):
        updated = manager.update_customer(
            sample_customer.customer_id, address="New Villa, Al Hamidiya, Ajman"
        )
        assert updated.address == "New Villa, Al Hamidiya, Ajman"

    def test_update_notes(self, manager, sample_customer):
        updated = manager.update_customer(sample_customer.customer_id, notes="VIP customer")
        assert updated.notes == "VIP customer"

    def test_update_empty_address_raises(self, manager, sample_customer):
        with pytest.raises(ValueError, match="Address is required"):
            manager.update_customer(sample_customer.customer_id, address="")


class TestDeactivateReactivate:
    def test_deactivate(self, manager, sample_customer):
        result = manager.deactivate_customer(sample_customer.customer_id)
        assert result.is_active is False

    def test_deactivate_already_inactive_raises(self, manager, sample_customer):
        manager.deactivate_customer(sample_customer.customer_id)
        with pytest.raises(ValueError, match="already inactive"):
            manager.deactivate_customer(sample_customer.customer_id)

    def test_reactivate(self, manager, sample_customer):
        manager.deactivate_customer(sample_customer.customer_id)
        result = manager.reactivate_customer(sample_customer.customer_id)
        assert result.is_active is True

    def test_reactivate_already_active_raises(self, manager, sample_customer):
        with pytest.raises(ValueError, match="already active"):
            manager.reactivate_customer(sample_customer.customer_id)


class TestSearchAndQueries:
    def test_search_by_name(self, manager, sample_customer):
        results = manager.search_customers("ahmed")
        assert len(results) == 1

    def test_search_by_email(self, manager, sample_customer):
        results = manager.search_customers("example.com")
        assert len(results) == 1

    def test_search_empty_query(self, manager, sample_customer):
        results = manager.search_customers("")
        assert results == []

    def test_get_active_customers(self, manager, sample_customer):
        active = manager.get_active_customers()
        assert len(active) == 1

    def test_get_active_excludes_inactive(self, manager, sample_customer):
        manager.deactivate_customer(sample_customer.customer_id)
        active = manager.get_active_customers()
        assert len(active) == 0

    def test_customer_count(self, manager, sample_customer):
        assert manager.customer_count == 1


class TestBookingCount:
    def test_increment_booking_count(self, manager, sample_customer):
        manager.increment_booking_count(sample_customer.customer_id)
        assert sample_customer.total_bookings == 1

    def test_is_returning_customer_false(self, manager, sample_customer):
        assert manager.is_returning_customer(sample_customer.customer_id) is False

    def test_is_returning_customer_true(self, manager, sample_customer):
        manager.increment_booking_count(sample_customer.customer_id)
        assert manager.is_returning_customer(sample_customer.customer_id) is True
