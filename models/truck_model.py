"""
Truck entity model for the logistics system.

Trucks have fixed capacities of 560 or 300 bags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class TruckCapacity(IntEnum):
    """Fixed truck capacity options (in bags)."""
    LARGE = 560
    SMALL = 300


@dataclass
class Truck:
    """
    Represents a delivery truck with a fixed capacity.

    Attributes:
        id: Unique identifier.
        plate_number: Vehicle license plate.
        capacity: Maximum load in bags (560 or 300).
        brand: Truck brand/manufacturer.
        model_year: Year of manufacture.
        is_available: Whether the truck is currently available for assignment.
        is_active: Whether the truck is in service (not decommissioned).
    """
    id: Optional[int] = field(default=None)
    plate_number: str = field(default="")
    capacity: int = field(default=TruckCapacity.LARGE)
    brand: str = field(default="")
    model_year: int = field(default=2024)
    is_available: bool = field(default=True)
    is_active: bool = field(default=True)

    def __post_init__(self) -> None:
        """Validate that capacity is one of the allowed values."""
        valid_capacities = {cap.value for cap in TruckCapacity}
        if self.capacity not in valid_capacities:
            raise ValueError(
                f"Truck capacity must be one of {valid_capacities}, "
                f"got {self.capacity}"
            )

    @property
    def capacity_label(self) -> str:
        """Return a human-readable label for the truck capacity."""
        if self.capacity == TruckCapacity.LARGE:
            return "Grande (560)"
        return "Pequeño (300)"

    def __str__(self) -> str:
        return (
            f"Truck(id={self.id}, plate='{self.plate_number}', "
            f"capacity={self.capacity})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Truck):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)
