

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DeliveryGroupStatus(Enum):
    """Enumeration of delivery group lifecycle statuses."""
    ASSEMBLING = "armando"
    READY = "listo"
    IN_ROUTE = "en_ruta"
    COMPLETED = "completado"
    LIQUIDATED = "liquidado"


@dataclass
class DeliveryGroup:
   
    id: Optional[int] = field(default=None)
    driver_id: int = field(default=0)
    driver_name: str = field(default="")
    helper_id: int = field(default=0)
    helper_name: str = field(default="")
    truck_id: int = field(default=0)
    truck_plate: str = field(default="")
    truck_capacity: int = field(default=560)
    assigned_order_ids: list[int] = field(default_factory=list)
    route_sequence: list[int] = field(default_factory=list)
    total_bags_loaded: int = field(default=0)
    status: DeliveryGroupStatus = field(default=DeliveryGroupStatus.ASSEMBLING)
    departure_time: Optional[datetime] = field(default=None)
    return_time: Optional[datetime] = field(default=None)
    created_at: Optional[datetime] = field(default=None)

    @property
    def capacity_used_percent(self) -> float:
        """Return percentage of truck capacity utilized."""
        if self.truck_capacity <= 0:
            return 0.0
        return min(100.0, (self.total_bags_loaded / self.truck_capacity) * 100.0)

    @property
    def remaining_capacity(self) -> int:
        """Return remaining bags that can be loaded."""
        return max(0, self.truck_capacity - self.total_bags_loaded)

    @property
    def status_display(self) -> str:
        """Return a Spanish display label for the status."""
        status_labels: dict[DeliveryGroupStatus, str] = {
            DeliveryGroupStatus.ASSEMBLING: "Armando",
            DeliveryGroupStatus.READY: "Listo",
            DeliveryGroupStatus.IN_ROUTE: "En Ruta",
            DeliveryGroupStatus.COMPLETED: "Completado",
            DeliveryGroupStatus.LIQUIDATED: "Liquidado",
        }
        return status_labels.get(self.status, "Desconocido")

    @property
    def is_full(self) -> bool:
        """Check if the truck is at or over capacity."""
        return self.total_bags_loaded >= self.truck_capacity

    def __str__(self) -> str:
        return (
            f"DeliveryGroup(id={self.id}, driver='{self.driver_name}', "
            f"helper='{self.helper_name}', truck='{self.truck_plate}', "
            f"loaded={self.total_bags_loaded}/{self.truck_capacity})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DeliveryGroup):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)
