"""
Order entity model for the logistics system.

Represents pending delivery requests from clients, scheduled up to 4-5 days ahead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class OrderStatus(Enum):
    """Enumeration of order lifecycle statuses."""
    PENDING = "pendiente"
    LOADED = "cargado"
    IN_TRANSIT = "en_transito"
    DELIVERED = "entregado"
    CANCELLED = "cancelado"


@dataclass
class Order:
    """
    Represents a client delivery order.

    Attributes:
        id: Unique identifier.
        client_id: Foreign key to the Client entity.
        client_name: Denormalized client name for display convenience.
        quantity_bags: Number of bags to deliver.
        scheduled_date: Date when the delivery is scheduled.
        status: Current order status.
        priority: Priority score (higher = more urgent). Computed by engine.
        unit_price: Price per bag in local currency.
        notes: Additional order notes.
        created_at: Timestamp of order creation.
    """
    id: Optional[int] = field(default=None)
    client_id: int = field(default=0)
    client_name: str = field(default="")
    quantity_bags: int = field(default=0)
    scheduled_date: Optional[date] = field(default=None)
    status: OrderStatus = field(default=OrderStatus.PENDING)
    priority: float = field(default=0.0)
    unit_price: float = field(default=0.0)
    notes: str = field(default="")
    created_at: Optional[datetime] = field(default=None)

    @property
    def total_value(self) -> float:
        """Calculate total monetary value of the order."""
        return self.quantity_bags * self.unit_price

    @property
    def days_until_scheduled(self) -> int:
        """Return number of days until the scheduled delivery date."""
        if self.scheduled_date is None:
            return 999  # No date set, low priority
        delta = self.scheduled_date - date.today()
        return max(0, delta.days)

    @property
    def is_overdue(self) -> bool:
        """Check if the order is past its scheduled date."""
        if self.scheduled_date is None:
            return False
        return date.today() > self.scheduled_date

    @property
    def status_display(self) -> str:
        """Return a Spanish display label for the status."""
        status_labels: dict[OrderStatus, str] = {
            OrderStatus.PENDING: "Pendiente",
            OrderStatus.LOADED: "Cargado",
            OrderStatus.IN_TRANSIT: "En Tránsito",
            OrderStatus.DELIVERED: "Entregado",
            OrderStatus.CANCELLED: "Cancelado",
        }
        return status_labels.get(self.status, "Desconocido")

    def __str__(self) -> str:
        return (
            f"Order(id={self.id}, client={self.client_id}, "
            f"bags={self.quantity_bags}, date={self.scheduled_date}, "
            f"status={self.status.value})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Order):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)
