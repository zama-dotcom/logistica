"""
Client entity model for the logistics system.

Clients are hardware stores (ferreterías) with geographic coordinates
and credit limits for delivery management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Client:
    """
    Represents a client (ferretería) with location and credit information.

    Attributes:
        id: Unique identifier.
        business_name: Registered business name.
        contact_name: Primary contact person name.
        phone: Contact phone number.
        address: Street address for deliveries.
        latitude: Geographic latitude coordinate.
        longitude: Geographic longitude coordinate.
        credit_limit: Maximum credit allowed (in local currency).
        current_balance: Current outstanding balance.
        zone: Geographic zone or sector label.
        is_active: Whether the client account is active.
    """
    id: Optional[int] = field(default=None)
    business_name: str = field(default="")
    contact_name: str = field(default="")
    phone: str = field(default="")
    address: str = field(default="")
    latitude: float = field(default=0.0)
    longitude: float = field(default=0.0)
    credit_limit: float = field(default=0.0)
    current_balance: float = field(default=0.0)
    zone: str = field(default="")
    is_active: bool = field(default=True)

    @property
    def available_credit(self) -> float:
        """Calculate remaining available credit."""
        return max(0.0, self.credit_limit - self.current_balance)

    @property
    def has_coordinates(self) -> bool:
        """Check if the client has valid geographic coordinates."""
        return self.latitude != 0.0 and self.longitude != 0.0

    @property
    def credit_utilization_percent(self) -> float:
        """Return credit utilization as a percentage (0-100)."""
        if self.credit_limit <= 0:
            return 0.0
        return min(100.0, (self.current_balance / self.credit_limit) * 100.0)

    def __str__(self) -> str:
        return (
            f"Client(id={self.id}, business='{self.business_name}', "
            f"coords=({self.latitude}, {self.longitude}))"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Client):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)
