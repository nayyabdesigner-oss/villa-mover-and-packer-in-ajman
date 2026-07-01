"""Pricing and cost estimation for moving services."""

from dataclasses import dataclass
from enum import Enum


class ServiceType(Enum):
    LOCAL_MOVE = "local_move"
    LONG_DISTANCE = "long_distance"
    PACKING_ONLY = "packing_only"
    FULL_SERVICE = "full_service"


class VillaSize(Enum):
    STUDIO = "studio"
    ONE_BEDROOM = "1br"
    TWO_BEDROOM = "2br"
    THREE_BEDROOM = "3br"
    FOUR_BEDROOM = "4br"
    FIVE_PLUS_BEDROOM = "5br+"


BASE_RATES = {
    VillaSize.STUDIO: 500.0,
    VillaSize.ONE_BEDROOM: 800.0,
    VillaSize.TWO_BEDROOM: 1200.0,
    VillaSize.THREE_BEDROOM: 1800.0,
    VillaSize.FOUR_BEDROOM: 2500.0,
    VillaSize.FIVE_PLUS_BEDROOM: 3500.0,
}

SERVICE_MULTIPLIERS = {
    ServiceType.LOCAL_MOVE: 1.0,
    ServiceType.LONG_DISTANCE: 2.5,
    ServiceType.PACKING_ONLY: 0.6,
    ServiceType.FULL_SERVICE: 1.8,
}


@dataclass
class PricingBreakdown:
    base_cost: float
    service_multiplier: float
    distance_surcharge: float
    floor_surcharge: float
    fragile_items_fee: float
    discount: float
    total: float


def calculate_floor_surcharge(floor: int, has_elevator: bool) -> float:
    """Calculate surcharge based on floor level and elevator availability."""
    if floor <= 0:
        return 0.0
    if has_elevator:
        return floor * 25.0
    return floor * 75.0


def calculate_distance_surcharge(distance_km: float) -> float:
    """Calculate surcharge based on distance in kilometers."""
    if distance_km <= 0:
        raise ValueError("Distance must be positive")
    if distance_km <= 10:
        return 0.0
    if distance_km <= 50:
        return (distance_km - 10) * 5.0
    return 200.0 + (distance_km - 50) * 8.0


def calculate_fragile_items_fee(num_fragile_items: int) -> float:
    """Calculate additional fee for fragile items requiring special handling."""
    if num_fragile_items < 0:
        raise ValueError("Number of fragile items cannot be negative")
    if num_fragile_items == 0:
        return 0.0
    if num_fragile_items <= 5:
        return num_fragile_items * 50.0
    return 250.0 + (num_fragile_items - 5) * 30.0


def calculate_discount(base_cost: float, is_returning_customer: bool, promo_code: str | None = None) -> float:
    """Calculate applicable discount."""
    discount = 0.0
    if is_returning_customer:
        discount += base_cost * 0.10
    if promo_code == "AJMAN20":
        discount += base_cost * 0.20
    elif promo_code == "WELCOME10":
        discount += base_cost * 0.10
    return min(discount, base_cost * 0.30)


def estimate_cost(
    villa_size: VillaSize,
    service_type: ServiceType,
    distance_km: float,
    floor: int = 0,
    has_elevator: bool = True,
    num_fragile_items: int = 0,
    is_returning_customer: bool = False,
    promo_code: str | None = None,
) -> PricingBreakdown:
    """Generate a full cost estimate for a move."""
    base_cost = BASE_RATES[villa_size]
    service_multiplier = SERVICE_MULTIPLIERS[service_type]
    adjusted_base = base_cost * service_multiplier

    distance_surcharge = calculate_distance_surcharge(distance_km)
    floor_surcharge = calculate_floor_surcharge(floor, has_elevator)
    fragile_fee = calculate_fragile_items_fee(num_fragile_items)

    subtotal = adjusted_base + distance_surcharge + floor_surcharge + fragile_fee
    discount = calculate_discount(subtotal, is_returning_customer, promo_code)
    total = subtotal - discount

    return PricingBreakdown(
        base_cost=base_cost,
        service_multiplier=service_multiplier,
        distance_surcharge=distance_surcharge,
        floor_surcharge=floor_surcharge,
        fragile_items_fee=fragile_fee,
        discount=discount,
        total=total,
    )
