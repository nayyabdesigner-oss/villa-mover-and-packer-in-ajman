"""Unit tests for the inventory module."""

import pytest

from villa_mover.inventory import (
    InventoryItem,
    InventoryList,
    ItemCategory,
    PackingType,
)


@pytest.fixture
def inventory():
    return InventoryList(booking_id="BK-001")


@pytest.fixture
def sample_item():
    return InventoryItem(
        name="Sofa",
        category=ItemCategory.FURNITURE,
        quantity=1,
        weight_kg=45.0,
        is_fragile=False,
    )


@pytest.fixture
def fragile_item():
    return InventoryItem(
        name="Crystal Vase",
        category=ItemCategory.FRAGILE,
        quantity=2,
        weight_kg=3.0,
        is_fragile=True,
        packing_type=PackingType.BUBBLE_WRAP,
    )


class TestAddItem:
    def test_add_valid_item(self, inventory, sample_item):
        inventory.add_item(sample_item)
        assert len(inventory.items) == 1
        assert inventory.items[0].item_id == "BK-001-1"

    def test_add_multiple_items(self, inventory, sample_item, fragile_item):
        inventory.add_item(sample_item)
        inventory.add_item(fragile_item)
        assert len(inventory.items) == 2
        assert inventory.items[1].item_id == "BK-001-2"

    def test_empty_name_raises(self, inventory):
        item = InventoryItem(name="", category=ItemCategory.FURNITURE)
        with pytest.raises(ValueError, match="name is required"):
            inventory.add_item(item)

    def test_whitespace_name_raises(self, inventory):
        item = InventoryItem(name="   ", category=ItemCategory.FURNITURE)
        with pytest.raises(ValueError, match="name is required"):
            inventory.add_item(item)

    def test_zero_quantity_raises(self, inventory):
        item = InventoryItem(name="Table", category=ItemCategory.FURNITURE, quantity=0)
        with pytest.raises(ValueError, match="Quantity must be positive"):
            inventory.add_item(item)

    def test_negative_quantity_raises(self, inventory):
        item = InventoryItem(name="Table", category=ItemCategory.FURNITURE, quantity=-1)
        with pytest.raises(ValueError, match="Quantity must be positive"):
            inventory.add_item(item)

    def test_negative_weight_raises(self, inventory):
        item = InventoryItem(name="Table", category=ItemCategory.FURNITURE, weight_kg=-5.0)
        with pytest.raises(ValueError, match="Weight cannot be negative"):
            inventory.add_item(item)


class TestRemoveItem:
    def test_remove_existing_item(self, inventory, sample_item):
        inventory.add_item(sample_item)
        removed = inventory.remove_item("BK-001-1")
        assert removed.name == "Sofa"
        assert len(inventory.items) == 0

    def test_remove_nonexistent_raises(self, inventory):
        with pytest.raises(KeyError, match="not found"):
            inventory.remove_item("BK-001-99")


class TestGetTotalWeight:
    def test_empty_inventory(self, inventory):
        assert inventory.get_total_weight() == 0.0

    def test_single_item(self, inventory, sample_item):
        inventory.add_item(sample_item)
        assert inventory.get_total_weight() == 45.0

    def test_item_with_quantity(self, inventory):
        item = InventoryItem(name="Boxes", category=ItemCategory.BOOKS, quantity=5, weight_kg=10.0)
        inventory.add_item(item)
        assert inventory.get_total_weight() == 50.0

    def test_multiple_items(self, inventory, sample_item, fragile_item):
        inventory.add_item(sample_item)
        inventory.add_item(fragile_item)
        # 45.0 * 1 + 3.0 * 2 = 51.0
        assert inventory.get_total_weight() == 51.0


class TestGetTotalItemsCount:
    def test_empty_inventory(self, inventory):
        assert inventory.get_total_items_count() == 0

    def test_single_item(self, inventory, sample_item):
        inventory.add_item(sample_item)
        assert inventory.get_total_items_count() == 1

    def test_item_with_quantity(self, inventory, fragile_item):
        inventory.add_item(fragile_item)
        assert inventory.get_total_items_count() == 2


class TestGetFragileItems:
    def test_no_fragile_items(self, inventory, sample_item):
        inventory.add_item(sample_item)
        assert inventory.get_fragile_items() == []

    def test_with_fragile_items(self, inventory, sample_item, fragile_item):
        inventory.add_item(sample_item)
        inventory.add_item(fragile_item)
        fragile = inventory.get_fragile_items()
        assert len(fragile) == 1
        assert fragile[0].name == "Crystal Vase"


class TestGetHeavyItems:
    def test_no_heavy_items(self, inventory, sample_item):
        inventory.add_item(sample_item)
        assert inventory.get_heavy_items() == []

    def test_with_heavy_items(self, inventory):
        heavy = InventoryItem(name="Piano", category=ItemCategory.HEAVY, weight_kg=200.0)
        inventory.add_item(heavy)
        result = inventory.get_heavy_items()
        assert len(result) == 1

    def test_custom_threshold(self, inventory, sample_item):
        inventory.add_item(sample_item)
        result = inventory.get_heavy_items(threshold_kg=40.0)
        assert len(result) == 1

    def test_invalid_threshold_raises(self, inventory):
        with pytest.raises(ValueError, match="Threshold must be positive"):
            inventory.get_heavy_items(threshold_kg=0)


class TestGetItemsByCategory:
    def test_filter_by_category(self, inventory):
        inventory.add_item(InventoryItem(name="Sofa", category=ItemCategory.FURNITURE, weight_kg=40.0))
        inventory.add_item(InventoryItem(name="TV", category=ItemCategory.ELECTRONICS, weight_kg=15.0))
        inventory.add_item(InventoryItem(name="Table", category=ItemCategory.FURNITURE, weight_kg=30.0))
        result = inventory.get_items_by_category(ItemCategory.FURNITURE)
        assert len(result) == 2


class TestGetPackingSummary:
    def test_empty_inventory(self, inventory):
        assert inventory.get_packing_summary() == {}

    def test_mixed_packing(self, inventory, sample_item, fragile_item):
        inventory.add_item(sample_item)
        inventory.add_item(fragile_item)
        summary = inventory.get_packing_summary()
        assert summary[PackingType.STANDARD] == 1
        assert summary[PackingType.BUBBLE_WRAP] == 2


class TestRequiresSpecialVehicle:
    def test_light_inventory_no_special(self, inventory, sample_item):
        inventory.add_item(sample_item)
        assert not inventory.requires_special_vehicle()

    def test_heavy_total_weight(self, inventory):
        for i in range(50):
            inventory.add_item(
                InventoryItem(name=f"Box-{i}", category=ItemCategory.BOOKS, weight_kg=50.0)
            )
        assert inventory.requires_special_vehicle()

    def test_oversized_single_item(self, inventory):
        inventory.add_item(
            InventoryItem(name="Grand Piano", category=ItemCategory.HEAVY, weight_kg=150.0)
        )
        assert inventory.requires_special_vehicle()

    def test_too_many_items(self, inventory):
        inventory.add_item(
            InventoryItem(name="Books", category=ItemCategory.BOOKS, quantity=51, weight_kg=1.0)
        )
        assert inventory.requires_special_vehicle()


class TestEstimateBoxesNeeded:
    def test_empty_inventory(self, inventory):
        assert inventory.estimate_boxes_needed() == 0

    def test_only_furniture(self, inventory, sample_item):
        inventory.add_item(sample_item)
        assert inventory.estimate_boxes_needed() == 0

    def test_small_items(self, inventory):
        inventory.add_item(
            InventoryItem(name="Books", category=ItemCategory.BOOKS, quantity=5, weight_kg=2.0)
        )
        assert inventory.estimate_boxes_needed() == 1

    def test_many_small_items(self, inventory):
        inventory.add_item(
            InventoryItem(name="Books", category=ItemCategory.BOOKS, quantity=25, weight_kg=2.0)
        )
        assert inventory.estimate_boxes_needed() == 3

    def test_mixed_items_excludes_furniture(self, inventory):
        inventory.add_item(
            InventoryItem(name="Sofa", category=ItemCategory.FURNITURE, quantity=2, weight_kg=40.0)
        )
        inventory.add_item(
            InventoryItem(name="Plates", category=ItemCategory.KITCHENWARE, quantity=15, weight_kg=1.0)
        )
        assert inventory.estimate_boxes_needed() == 2
