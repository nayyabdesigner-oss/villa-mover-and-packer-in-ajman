"""Inventory tracking for items to be moved."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ItemCategory(Enum):
    FURNITURE = "furniture"
    ELECTRONICS = "electronics"
    KITCHENWARE = "kitchenware"
    CLOTHING = "clothing"
    BOOKS = "books"
    FRAGILE = "fragile"
    HEAVY = "heavy"
    MISCELLANEOUS = "miscellaneous"


class PackingType(Enum):
    STANDARD = "standard"
    BUBBLE_WRAP = "bubble_wrap"
    WOODEN_CRATE = "wooden_crate"
    CUSTOM = "custom"


@dataclass
class InventoryItem:
    name: str
    category: ItemCategory
    quantity: int = 1
    weight_kg: float = 0.0
    is_fragile: bool = False
    packing_type: PackingType = PackingType.STANDARD
    special_instructions: str = ""
    item_id: str = ""


@dataclass
class InventoryList:
    booking_id: str
    items: list[InventoryItem] = field(default_factory=list)

    def add_item(self, item: InventoryItem) -> None:
        """Add an item to the inventory list."""
        if not item.name or not item.name.strip():
            raise ValueError("Item name is required")
        if item.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if item.weight_kg < 0:
            raise ValueError("Weight cannot be negative")
        item.item_id = f"{self.booking_id}-{len(self.items) + 1}"
        self.items.append(item)

    def remove_item(self, item_id: str) -> InventoryItem:
        """Remove an item from the inventory list by ID."""
        for i, item in enumerate(self.items):
            if item.item_id == item_id:
                return self.items.pop(i)
        raise KeyError(f"Item not found: {item_id}")

    def get_total_weight(self) -> float:
        """Calculate total weight of all items."""
        return sum(item.weight_kg * item.quantity for item in self.items)

    def get_total_items_count(self) -> int:
        """Get total number of individual items (accounting for quantity)."""
        return sum(item.quantity for item in self.items)

    def get_fragile_items(self) -> list[InventoryItem]:
        """Get all fragile items."""
        return [item for item in self.items if item.is_fragile]

    def get_heavy_items(self, threshold_kg: float = 50.0) -> list[InventoryItem]:
        """Get items exceeding a weight threshold."""
        if threshold_kg <= 0:
            raise ValueError("Threshold must be positive")
        return [item for item in self.items if item.weight_kg >= threshold_kg]

    def get_items_by_category(self, category: ItemCategory) -> list[InventoryItem]:
        """Get all items in a specific category."""
        return [item for item in self.items if item.category == category]

    def get_packing_summary(self) -> dict[PackingType, int]:
        """Get a summary of packing requirements."""
        summary: dict[PackingType, int] = {}
        for item in self.items:
            summary[item.packing_type] = summary.get(item.packing_type, 0) + item.quantity
        return summary

    def requires_special_vehicle(self) -> bool:
        """Determine if the inventory requires a special/larger vehicle."""
        total_weight = self.get_total_weight()
        has_oversized = any(item.weight_kg > 100 for item in self.items)
        total_items = self.get_total_items_count()
        return total_weight > 2000 or has_oversized or total_items > 50

    def estimate_boxes_needed(self) -> int:
        """Estimate number of standard boxes needed for non-furniture items."""
        non_furniture = [
            item for item in self.items
            if item.category not in (ItemCategory.FURNITURE, ItemCategory.HEAVY)
        ]
        total_small_items = sum(item.quantity for item in non_furniture)
        return max(1, (total_small_items + 9) // 10) if non_furniture else 0
