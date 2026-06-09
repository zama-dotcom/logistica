"""
RouteReport entity model for the logistics system.

Represents feedback submitted by the helper after a delivery,
including payment collection and product loss (merma/broken bags).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentMethod(Enum):
    """Enumeration of accepted payment methods."""
    CASH = "efectivo"
    TRANSFER = "transferencia"
    CHECK = "cheque"
    CREDIT = "credito"
    NONE = "sin_pago"


class LiquidationStatus(Enum):
    """Status of the route liquidation process."""
    PENDING = "pendiente"
    APPROVED = "aprobado"
    REJECTED = "rechazado"


@dataclass
class RouteReport:
    """
    Represents a helper's delivery report for a single client stop.

    Attributes:
        id: Unique identifier.
        delivery_group_id: Foreign key to the DeliveryGroup.
        client_id: Foreign key to the Client.
        client_name: Denormalized client name for display.
        bags_delivered: Number of bags successfully delivered.
        bags_returned: Number of bags returned (rejected by client).
        broken_bags: Number of damaged/broken bags (merma).
        payment_collected: Amount of money collected.
        payment_method: How the payment was made.
        liquidation_status: Approval status by the boss.
        notes: Additional notes from the helper.
        delivery_timestamp: When the delivery was completed.
        created_at: Record creation timestamp.
    """
    id: Optional[int] = field(default=None)
    delivery_group_id: int = field(default=0)
    client_id: int = field(default=0)
    client_name: str = field(default="")
    bags_delivered: int = field(default=0)
    bags_returned: int = field(default=0)
    broken_bags: int = field(default=0)
    payment_collected: float = field(default=0.0)
    payment_method: PaymentMethod = field(default=PaymentMethod.NONE)
    liquidation_status: LiquidationStatus = field(default=LiquidationStatus.PENDING)
    notes: str = field(default="")
    delivery_timestamp: Optional[datetime] = field(default=None)
    created_at: Optional[datetime] = field(default=None)

    @property
    def total_loss_bags(self) -> int:
        """Total bags lost (broken + returned)."""
        return self.broken_bags + self.bags_returned

    @property
    def payment_method_display(self) -> str:
        """Return a Spanish display label for the payment method."""
        method_labels: dict[PaymentMethod, str] = {
            PaymentMethod.CASH: "Efectivo",
            PaymentMethod.TRANSFER: "Transferencia",
            PaymentMethod.CHECK: "Cheque",
            PaymentMethod.CREDIT: "Crédito",
            PaymentMethod.NONE: "Sin Pago",
        }
        return method_labels.get(self.payment_method, "Desconocido")

    @property
    def liquidation_status_display(self) -> str:
        """Return a Spanish display label for liquidation status."""
        status_labels: dict[LiquidationStatus, str] = {
            LiquidationStatus.PENDING: "Pendiente",
            LiquidationStatus.APPROVED: "Aprobado",
            LiquidationStatus.REJECTED: "Rechazado",
        }
        return status_labels.get(self.liquidation_status, "Desconocido")

    def __str__(self) -> str:
        return (
            f"RouteReport(id={self.id}, group={self.delivery_group_id}, "
            f"client='{self.client_name}', collected={self.payment_collected}, "
            f"broken={self.broken_bags})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RouteReport):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)
