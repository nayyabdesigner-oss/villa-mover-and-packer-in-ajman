"""Unit tests for the crew module."""

from datetime import date, timedelta

import pytest

from villa_mover.crew import (
    Assignment,
    CrewManager,
    CrewMember,
    CrewRole,
    Vehicle,
    VehicleType,
)


@pytest.fixture
def manager():
    return CrewManager()


@pytest.fixture
def driver(manager):
    return manager.add_crew_member("Ali Driver", CrewRole.DRIVER)


@pytest.fixture
def mover1(manager):
    return manager.add_crew_member("Hassan Mover", CrewRole.MOVER)


@pytest.fixture
def mover2(manager):
    return manager.add_crew_member("Omar Mover", CrewRole.MOVER)


@pytest.fixture
def small_van(manager):
    return manager.add_vehicle(VehicleType.SMALL_VAN, 1000.0, "AJM-1234")


@pytest.fixture
def large_truck(manager):
    return manager.add_vehicle(VehicleType.LARGE_TRUCK, 7000.0, "AJM-5678")


class TestAddCrewMember:
    def test_add_valid_member(self, manager):
        member = manager.add_crew_member("Ali Hassan", CrewRole.DRIVER)
        assert member.crew_id == "CREW-0001"
        assert member.name == "Ali Hassan"
        assert member.role == CrewRole.DRIVER
        assert member.is_available is True

    def test_sequential_ids(self, manager):
        m1 = manager.add_crew_member("Member One", CrewRole.MOVER)
        m2 = manager.add_crew_member("Member Two", CrewRole.PACKER)
        assert m1.crew_id == "CREW-0001"
        assert m2.crew_id == "CREW-0002"

    def test_with_certifications(self, manager):
        member = manager.add_crew_member(
            "Expert Mover", CrewRole.MOVER, certifications=["heavy_lift", "fragile"]
        )
        assert "heavy_lift" in member.certifications

    def test_empty_name_raises(self, manager):
        with pytest.raises(ValueError, match="name is required"):
            manager.add_crew_member("", CrewRole.MOVER)

    def test_whitespace_name_raises(self, manager):
        with pytest.raises(ValueError, match="name is required"):
            manager.add_crew_member("   ", CrewRole.MOVER)


class TestAddVehicle:
    def test_add_valid_vehicle(self, manager):
        vehicle = manager.add_vehicle(VehicleType.SMALL_VAN, 1000.0, "AJM-1234")
        assert vehicle.vehicle_id == "VEH-AJM-1234"
        assert vehicle.vehicle_type == VehicleType.SMALL_VAN
        assert vehicle.capacity_kg == 1000.0
        assert vehicle.is_available is True

    def test_zero_capacity_raises(self, manager):
        with pytest.raises(ValueError, match="capacity must be positive"):
            manager.add_vehicle(VehicleType.SMALL_VAN, 0, "AJM-0000")

    def test_negative_capacity_raises(self, manager):
        with pytest.raises(ValueError, match="capacity must be positive"):
            manager.add_vehicle(VehicleType.SMALL_VAN, -100, "AJM-0000")

    def test_empty_plate_raises(self, manager):
        with pytest.raises(ValueError, match="Plate number is required"):
            manager.add_vehicle(VehicleType.SMALL_VAN, 1000.0, "")

    def test_duplicate_plate_raises(self, manager, small_van):
        with pytest.raises(ValueError, match="already registered"):
            manager.add_vehicle(VehicleType.MEDIUM_TRUCK, 3000.0, "AJM-1234")


class TestGetAvailableCrew:
    def test_all_available(self, manager, driver, mover1):
        available = manager.get_available_crew()
        assert len(available) == 2

    def test_filter_by_role(self, manager, driver, mover1, mover2):
        movers = manager.get_available_crew(role=CrewRole.MOVER)
        assert len(movers) == 2
        drivers = manager.get_available_crew(role=CrewRole.DRIVER)
        assert len(drivers) == 1

    def test_excludes_unavailable(self, manager, driver, mover1):
        driver.is_available = False
        available = manager.get_available_crew()
        assert len(available) == 1


class TestGetAvailableVehicles:
    def test_all_available(self, manager, small_van, large_truck):
        vehicles = manager.get_available_vehicles()
        assert len(vehicles) == 2

    def test_filter_by_capacity(self, manager, small_van, large_truck):
        result = manager.get_available_vehicles(min_capacity_kg=5000.0)
        assert len(result) == 1
        assert result[0].vehicle_type == VehicleType.LARGE_TRUCK

    def test_excludes_unavailable(self, manager, small_van, large_truck):
        small_van.is_available = False
        vehicles = manager.get_available_vehicles()
        assert len(vehicles) == 1


class TestSelectVehicleForWeight:
    def test_selects_smallest_suitable(self, manager, small_van, large_truck):
        vehicle = manager.select_vehicle_for_weight(500.0)
        assert vehicle.vehicle_type == VehicleType.SMALL_VAN

    def test_selects_larger_when_needed(self, manager, small_van, large_truck):
        vehicle = manager.select_vehicle_for_weight(3000.0)
        assert vehicle.vehicle_type == VehicleType.LARGE_TRUCK

    def test_none_when_too_heavy(self, manager, small_van):
        vehicle = manager.select_vehicle_for_weight(5000.0)
        assert vehicle is None

    def test_zero_weight_raises(self, manager, small_van):
        with pytest.raises(ValueError, match="Weight must be positive"):
            manager.select_vehicle_for_weight(0)

    def test_negative_weight_raises(self, manager, small_van):
        with pytest.raises(ValueError, match="Weight must be positive"):
            manager.select_vehicle_for_weight(-100)


class TestCreateAssignment:
    def test_successful_assignment(self, manager, driver, mover1, small_van):
        assignment = manager.create_assignment(
            booking_id="BK-001",
            assignment_date=date.today() + timedelta(days=7),
            crew_ids=[driver.crew_id, mover1.crew_id],
            vehicle_id=small_van.vehicle_id,
        )
        assert assignment.booking_id == "BK-001"
        assert len(assignment.crew_members) == 2
        assert assignment.vehicle == small_van

    def test_marks_resources_unavailable(self, manager, driver, mover1, small_van):
        manager.create_assignment(
            booking_id="BK-001",
            assignment_date=date.today() + timedelta(days=7),
            crew_ids=[driver.crew_id, mover1.crew_id],
            vehicle_id=small_van.vehicle_id,
        )
        assert not driver.is_available
        assert not mover1.is_available
        assert not small_van.is_available

    def test_no_crew_raises(self, manager, small_van):
        with pytest.raises(ValueError, match="[Aa]t least one crew member"):
            manager.create_assignment(
                booking_id="BK-001",
                assignment_date=date.today() + timedelta(days=7),
                crew_ids=[],
                vehicle_id=small_van.vehicle_id,
            )

    def test_vehicle_not_found_raises(self, manager, driver, mover1):
        with pytest.raises(KeyError, match="Vehicle not found"):
            manager.create_assignment(
                booking_id="BK-001",
                assignment_date=date.today() + timedelta(days=7),
                crew_ids=[driver.crew_id, mover1.crew_id],
                vehicle_id="VEH-NONEXIST",
            )

    def test_unavailable_vehicle_raises(self, manager, driver, mover1, small_van):
        small_van.is_available = False
        with pytest.raises(ValueError, match="not available"):
            manager.create_assignment(
                booking_id="BK-001",
                assignment_date=date.today() + timedelta(days=7),
                crew_ids=[driver.crew_id, mover1.crew_id],
                vehicle_id=small_van.vehicle_id,
            )

    def test_crew_not_found_raises(self, manager, driver, small_van):
        with pytest.raises(KeyError, match="Crew member not found"):
            manager.create_assignment(
                booking_id="BK-001",
                assignment_date=date.today() + timedelta(days=7),
                crew_ids=[driver.crew_id, "CREW-9999"],
                vehicle_id=small_van.vehicle_id,
            )

    def test_unavailable_crew_raises(self, manager, driver, mover1, small_van):
        mover1.is_available = False
        with pytest.raises(ValueError, match="not available"):
            manager.create_assignment(
                booking_id="BK-001",
                assignment_date=date.today() + timedelta(days=7),
                crew_ids=[driver.crew_id, mover1.crew_id],
                vehicle_id=small_van.vehicle_id,
            )

    def test_insufficient_crew_for_large_truck(self, manager, driver, mover1, large_truck):
        with pytest.raises(ValueError, match="requires at least"):
            manager.create_assignment(
                booking_id="BK-001",
                assignment_date=date.today() + timedelta(days=7),
                crew_ids=[driver.crew_id, mover1.crew_id],
                vehicle_id=large_truck.vehicle_id,
            )

    def test_no_driver_raises(self, manager, mover1, mover2, small_van):
        with pytest.raises(ValueError, match="at least one driver"):
            manager.create_assignment(
                booking_id="BK-001",
                assignment_date=date.today() + timedelta(days=7),
                crew_ids=[mover1.crew_id, mover2.crew_id],
                vehicle_id=small_van.vehicle_id,
            )


class TestReleaseAssignment:
    def test_release_makes_resources_available(self, manager, driver, mover1, small_van):
        manager.create_assignment(
            booking_id="BK-001",
            assignment_date=date.today() + timedelta(days=7),
            crew_ids=[driver.crew_id, mover1.crew_id],
            vehicle_id=small_van.vehicle_id,
        )
        manager.release_assignment("BK-001")
        assert driver.is_available
        assert mover1.is_available
        assert small_van.is_available

    def test_release_nonexistent_raises(self, manager):
        with pytest.raises(KeyError, match="not found"):
            manager.release_assignment("BK-NONEXIST")


class TestGetAssignment:
    def test_get_existing(self, manager, driver, mover1, small_van):
        manager.create_assignment(
            booking_id="BK-001",
            assignment_date=date.today() + timedelta(days=7),
            crew_ids=[driver.crew_id, mover1.crew_id],
            vehicle_id=small_van.vehicle_id,
        )
        assignment = manager.get_assignment("BK-001")
        assert assignment.booking_id == "BK-001"

    def test_get_nonexistent_raises(self, manager):
        with pytest.raises(KeyError, match="not found"):
            manager.get_assignment("BK-NONEXIST")
