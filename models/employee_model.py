

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EmployeeRole(Enum):
    """Enumeration of employee roles in delivery operations."""
    DRIVER = "conductor"
    HELPER = "ayudante"


@dataclass
class Employee:

    id: Optional[int] = field(default=None)
    full_name: str = field(default="")
    role: EmployeeRole = field(default=EmployeeRole.DRIVER)
    phone: str = field(default="")
    license_number: str = field(default="")
    is_available: bool = field(default=True)
    is_active: bool = field(default=True)

    @property
    def role_display(self) -> str:
        """Return a Spanish display label for the role."""
        role_labels: dict[EmployeeRole, str] = {
            EmployeeRole.DRIVER: "Conductor",
            EmployeeRole.HELPER: "Ayudante",
        }
        return role_labels.get(self.role, "Desconocido")

    def __str__(self) -> str:
        return (
            f"Employee(id={self.id}, name='{self.full_name}', "
            f"role={self.role.value})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Employee):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)
