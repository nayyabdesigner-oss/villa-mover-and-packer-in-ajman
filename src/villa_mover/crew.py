"""Crew and vehicle assignment management."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class VehicleType(Enum):
    SMALL_VAN = "small_van"  # Up to 1000 kg
    MEDIUM_TRUCK = "medium_truck"  # Up to 3000 kg
    LARGE_TRUCK = "large_truck"  # Up to 7000 kg
    SPECIAL = "special"  # Oversized/heavy items


class CrewRole(Enum):
    DRIVER = "driver"
    MOVER = "mover"
    PACKER = "packer"
    SUPERVISOR = "supervisor"


@dataclass
class CrewMember:
    name: str
    role: CrewRole
    crew_id: str = ""
    is_available: bool = True
    certifications: list[str] = field(default_factory=list)


@dataclass
class Vehicle:
    vehicle_id: str
    vehicle_type: VehicleType
    capacity_kg: float
    plate_number: str
    is_available: bool = True


@dataclass
class Assignment:
    booking_id: str
    assignment_date: date
    crew_members: list[CrewMember] = field(default_factory=list)
    vehicle: Optional[Vehicle] = None


class CrewManager:
    """Manages crew members, vehicles, and assignments."""

    MINIMUM_CREW_SIZE = {
        VehicleType.SMALL_VAN: 2,
        VehicleType.MEDIUM_TRUCK: 3,
        VehicleType.LARGE_TRUCK: 4,
        VehicleType.SPECIAL: 5,
    }

    def __init__(self):
        self._crew: dict[str, CrewMember] = {}
        self._vehicles: dict[str, Vehicle] = {}
        self._assignments: dict[str, Assignment] = {}
        self._next_crew_id: int = 1

    def add_crew_member(self, name: str, role: CrewRole, certifications: list[str] | None = None) -> CrewMember:
        """Register a new crew member."""
        if not name or not name.strip():
            raise ValueError("Crew member name is required")

        crew_id = f"CREW-{self._next_crew_id:04d}"
        self._next_crew_id += 1

        member = CrewMember(
            name=name.strip(),
            role=role,
            crew_id=crew_id,
            certifications=certifications or [],
        )
        self._crew[crew_id] = member
        return member

    def add_vehicle(self, vehicle_type: VehicleType, capacity_kg: float, plate_number: str) -> Vehicle:
        """Register a new vehicle."""
        if capacity_kg <= 0:
            raise ValueError("Vehicle capacity must be positive")
        if not plate_number or not plate_number.strip():
            raise ValueError("Plate number is required")

        vehicle_id = f"VEH-{plate_number.strip().upper()}"
        if vehicle_id in self._vehicles:
            raise ValueError(f"Vehicle already registered: {plate_number}")

        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            capacity_kg=capacity_kg,
            plate_number=plate_number.strip().upper(),
        )
        self._vehicles[vehicle_id] = vehicle
        return vehicle

    def get_available_crew(self, role: Optional[CrewRole] = None) -> list[CrewMember]:
        """Get available crew members, optionally filtered by role."""
        members = [m for m in self._crew.values() if m.is_available]
        if role:
            members = [m for m in members if m.role == role]
        return members

    def get_available_vehicles(self, min_capacity_kg: float = 0) -> list[Vehicle]:
        """Get available vehicles, optionally filtered by minimum capacity."""
        return [
            v for v in self._vehicles.values()
            if v.is_available and v.capacity_kg >= min_capacity_kg
        ]

    def select_vehicle_for_weight(self, total_weight_kg: float) -> Optional[Vehicle]:
        """Select the most appropriate available vehicle for a given weight."""
        if total_weight_kg <= 0:
            raise ValueError("Weight must be positive")

        suitable = [
            v for v in self._vehicles.values()
            if v.is_available and v.capacity_kg >= total_weight_kg
        ]
        if not suitable:
            return None
        return min(suitable, key=lambda v: v.capacity_kg)

    def create_assignment(
        self,
        booking_id: str,
        assignment_date: date,
        crew_ids: list[str],
        vehicle_id: str,
    ) -> Assignment:
        """Create an assignment for a booking."""
        if not crew_ids:
            raise ValueError("At least one crew member is required")

        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            raise KeyError(f"Vehicle not found: {vehicle_id}")
        if not vehicle.is_available:
            raise ValueError(f"Vehicle {vehicle_id} is not available")

        crew_members = []
        for cid in crew_ids:
            member = self._crew.get(cid)
            if not member:
                raise KeyError(f"Crew member not found: {cid}")
            if not member.is_available:
                raise ValueError(f"Crew member {cid} is not available")
            crew_members.append(member)

        min_size = self.MINIMUM_CREW_SIZE.get(vehicle.vehicle_type, 2)
        if len(crew_members) < min_size:
            raise ValueError(
                f"Vehicle type {vehicle.vehicle_type.value} requires at least {min_size} crew members"
            )

        has_driver = any(m.role == CrewRole.DRIVER for m in crew_members)
        if not has_driver:
            raise ValueError("Assignment must include at least one driver")

        assignment = Assignment(
            booking_id=booking_id,
            assignment_date=assignment_date,
            crew_members=crew_members,
            vehicle=vehicle,
        )
        self._assignments[booking_id] = assignment

        vehicle.is_available = False
        for member in crew_members:
            member.is_available = False

        return assignment

    def release_assignment(self, booking_id: str) -> None:
        """Release crew and vehicle from an assignment."""
        if booking_id not in self._assignments:
            raise KeyError(f"Assignment not found: {booking_id}")

        assignment = self._assignments[booking_id]
        if assignment.vehicle:
            assignment.vehicle.is_available = True
        for member in assignment.crew_members:
            member.is_available = True

        del self._assignments[booking_id]

    def get_assignment(self, booking_id: str) -> Assignment:
        """Get assignment details for a booking."""
        if booking_id not in self._assignments:
            raise KeyError(f"Assignment not found: {booking_id}")
        return self._assignments[booking_id]
