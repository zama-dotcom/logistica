"""
User entity model for the logistics system.

Supports three roles: Boss (Jefe), Dispatch (Despacho), and Promoter (Promotor).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class UserRole(Enum):
    """Enumeration of user roles in the system."""
    BOSS = "jefe"
    DISPATCH = "despacho"
    PROMOTER = "promotor"


@dataclass
class User:
    """
    Represents a system user with role-based access.

    Attributes:
        id: Unique identifier.
        username: Login username.
        password_hash: Hashed password (never store plaintext).
        full_name: Display name of the user.
        role: One of BOSS, DISPATCH, or PROMOTER.
        is_active: Whether the user account is enabled.
    """
    id: Optional[int] = field(default=None)
    username: str = field(default="")
    password_hash: str = field(default="")
    full_name: str = field(default="")
    role: UserRole = field(default=UserRole.DISPATCH)
    is_active: bool = field(default=True)

    def has_permission(self, required_role: UserRole) -> bool:
        """Check if the user has the required role permission."""
        role_hierarchy: dict[UserRole, int] = {
            UserRole.PROMOTER: 1,
            UserRole.DISPATCH: 2,
            UserRole.BOSS: 3,
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

    def __str__(self) -> str:
        return f"User(id={self.id}, username='{self.username}', role={self.role.value})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.id == other.id and self.username == other.username
        return False

    def __hash__(self) -> int:
        return hash((self.id, self.username))
