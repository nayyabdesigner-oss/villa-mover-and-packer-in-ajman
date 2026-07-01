"""Unit tests for the pricing module."""

import pytest

from villa_mover.pricing import (
    PricingBreakdown,
    ServiceType,
    VillaSize,
    calculate_discount,
    calculate_distance_surcharge,
    calculate_floor_surcharge,
    calculate_fragile_items_fee,
    estimate_cost,
)


class TestCalculateFloorSurcharge:
    def test_ground_floor_no_surcharge(self):
        assert calculate_floor_surcharge(0, has_elevator=True) == 0.0

    def test_negative_floor_no_surcharge(self):
        assert calculate_floor_surcharge(-1, has_elevator=False) == 0.0

    def test_with_elevator(self):
        assert calculate_floor_surcharge(3, has_elevator=True) == 75.0

    def test_without_elevator(self):
        assert calculate_floor_surcharge(3, has_elevator=False) == 225.0

    def test_high_floor_no_elevator(self):
        assert calculate_floor_surcharge(10, has_elevator=False) == 750.0

    def test_high_floor_with_elevator(self):
        assert calculate_floor_surcharge(10, has_elevator=True) == 250.0


class TestCalculateDistanceSurcharge:
    def test_short_distance_no_surcharge(self):
        assert calculate_distance_surcharge(5.0) == 0.0

    def test_at_10km_boundary(self):
        assert calculate_distance_surcharge(10.0) == 0.0

    def test_medium_distance(self):
        assert calculate_distance_surcharge(30.0) == 100.0

    def test_at_50km_boundary(self):
        assert calculate_distance_surcharge(50.0) == 200.0

    def test_long_distance(self):
        assert calculate_distance_surcharge(70.0) == 360.0

    def test_zero_distance_raises(self):
        with pytest.raises(ValueError, match="Distance must be positive"):
            calculate_distance_surcharge(0)

    def test_negative_distance_raises(self):
        with pytest.raises(ValueError, match="Distance must be positive"):
            calculate_distance_surcharge(-5.0)


class TestCalculateFragileItemsFee:
    def test_no_fragile_items(self):
        assert calculate_fragile_items_fee(0) == 0.0

    def test_few_fragile_items(self):
        assert calculate_fragile_items_fee(3) == 150.0

    def test_five_fragile_items(self):
        assert calculate_fragile_items_fee(5) == 250.0

    def test_many_fragile_items(self):
        assert calculate_fragile_items_fee(8) == 340.0

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_fragile_items_fee(-1)


class TestCalculateDiscount:
    def test_no_discount(self):
        assert calculate_discount(1000.0, is_returning_customer=False) == 0.0

    def test_returning_customer_discount(self):
        assert calculate_discount(1000.0, is_returning_customer=True) == 100.0

    def test_ajman20_promo(self):
        assert calculate_discount(1000.0, is_returning_customer=False, promo_code="AJMAN20") == 200.0

    def test_welcome10_promo(self):
        assert calculate_discount(1000.0, is_returning_customer=False, promo_code="WELCOME10") == 100.0

    def test_combined_discount_capped_at_30_percent(self):
        # Returning (10%) + AJMAN20 (20%) = 30% cap
        result = calculate_discount(1000.0, is_returning_customer=True, promo_code="AJMAN20")
        assert result == 300.0

    def test_invalid_promo_no_discount(self):
        assert calculate_discount(1000.0, is_returning_customer=False, promo_code="INVALID") == 0.0


class TestEstimateCost:
    def test_basic_local_move(self):
        result = estimate_cost(
            villa_size=VillaSize.TWO_BEDROOM,
            service_type=ServiceType.LOCAL_MOVE,
            distance_km=5.0,
        )
        assert isinstance(result, PricingBreakdown)
        assert result.base_cost == 1200.0
        assert result.service_multiplier == 1.0
        assert result.distance_surcharge == 0.0
        assert result.total == 1200.0

    def test_full_service_long_distance(self):
        result = estimate_cost(
            villa_size=VillaSize.THREE_BEDROOM,
            service_type=ServiceType.FULL_SERVICE,
            distance_km=60.0,
            floor=5,
            has_elevator=False,
            num_fragile_items=3,
        )
        assert result.base_cost == 1800.0
        assert result.service_multiplier == 1.8
        assert result.distance_surcharge == 280.0
        assert result.floor_surcharge == 375.0
        assert result.fragile_items_fee == 150.0
        assert result.total > 0

    def test_packing_only_service(self):
        result = estimate_cost(
            villa_size=VillaSize.STUDIO,
            service_type=ServiceType.PACKING_ONLY,
            distance_km=1.0,
        )
        assert result.service_multiplier == 0.6
        assert result.total == 300.0

    def test_with_discount(self):
        result = estimate_cost(
            villa_size=VillaSize.ONE_BEDROOM,
            service_type=ServiceType.LOCAL_MOVE,
            distance_km=5.0,
            is_returning_customer=True,
        )
        assert result.discount > 0
        assert result.total < 800.0

    def test_five_plus_bedroom(self):
        result = estimate_cost(
            villa_size=VillaSize.FIVE_PLUS_BEDROOM,
            service_type=ServiceType.LOCAL_MOVE,
            distance_km=5.0,
        )
        assert result.base_cost == 3500.0
