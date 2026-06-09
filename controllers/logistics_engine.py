


from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from models.client_model import Client
from models.delivery_group_model import DeliveryGroup, DeliveryGroupStatus
from models.employee_model import Employee, EmployeeRole
from models.order_model import Order, OrderStatus
from models.truck_model import Truck


# Default depot coordinates
DEPOT_LATITUDE: float = 14.6349
DEPOT_LONGITUDE: float = -90.5069

# window for scheduling 
DEFAULT_LOOKAHEAD_DAYS: int = 5

# Earth radius in kilometers
EARTH_RADIUS_KM: float = 6371.0

# Priority weight factors for the knapsack value function
WEIGHT_URGENCY: float = 3.0 
WEIGHT_QUANTITY: float = 1.0    
WEIGHT_CREDIT: float = 0.5     



#  Distance Calculation

def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Args:
        lat1: Latitude of point 1 (degrees).
        lon1: Longitude of point 1 (degrees).
        lat2: Latitude of point 2 (degrees).
        lon2: Longitude of point 2 (degrees).

    Returns:
        Distance in kilometers.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2)
        * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_KM * c


def compute_order_priority(
    order: Order,
    client: Optional[Client] = None,
) -> float:
    days_ahead = order.days_until_scheduled
    urgency_score = max(0.0, (DEFAULT_LOOKAHEAD_DAYS - days_ahead + 1))

    quantity_score = min(order.quantity_bags / 100.0, 3.0)

    credit_score = 0.0
    if client is not None and client.credit_limit > 0:
        utilization = client.credit_utilization_percent
        credit_score = max(0.0, (100.0 - utilization) / 100.0)

    priority = (
        WEIGHT_URGENCY * urgency_score
        + WEIGHT_QUANTITY * quantity_score
        + WEIGHT_CREDIT * credit_score
    )
    return round(priority, 2)


def select_orders_for_truck(
    orders: list[Order],
    truck_capacity: int,
    clients: Optional[list[Client]] = None,
    lookahead_days: int = DEFAULT_LOOKAHEAD_DAYS,
) -> list[Order]:
    # Build client lookup
    client_map: dict[int, Client] = {}
    if clients:
        client_map = {c.id: c for c in clients if c.id is not None}

    cutoff_date = date.today() + timedelta(days=lookahead_days)
    eligible: list[Order] = []

    for order in orders:
        if order.status != OrderStatus.PENDING:
            continue
        if order.quantity_bags <= 0:
            continue
        if order.quantity_bags > truck_capacity:
            continue  # Single order exceeds truck — skip
        if order.scheduled_date is not None and order.scheduled_date > cutoff_date:
            continue  # Beyond lookahead window
        eligible.append(order)

    if not eligible:
        return []

    # Compute priority scores
    for order in eligible:
        client = client_map.get(order.client_id)
        order.priority = compute_order_priority(order, client)

    n = len(eligible)
    capacity = truck_capacity

    # Weights and values arrays
    weights: list[int] = [o.quantity_bags for o in eligible]
    values: list[float] = [o.priority for o in eligible]

    # DP table: dp[i][w] = max value using first i items with capacity w
    dp: list[list[float]] = [
        [0.0] * (capacity + 1) for _ in range(n + 1)
    ]

    for i in range(1, n + 1):
        w_i = weights[i - 1]
        v_i = values[i - 1]
        for w in range(capacity + 1):
            # Don't take item i
            dp[i][w] = dp[i - 1][w]
            # Take item i if it fits
            if w_i <= w:
                candidate = dp[i - 1][w - w_i] + v_i
                if candidate > dp[i][w]:
                    dp[i][w] = candidate

    # Backtrack to find which orders were selected
    selected: list[Order] = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(eligible[i - 1])
            w -= weights[i - 1]

    selected.sort(key=lambda o: o.priority, reverse=True)

    return selected



#  Route Optimization

def optimize_route(
    clients: list[Client],
    depot_lat: float = DEPOT_LATITUDE,
    depot_lon: float = DEPOT_LONGITUDE,
) -> list[Client]:

    if not clients:
        return []

    if len(clients) == 1:
        return list(clients)

    valid_clients = [c for c in clients if c.has_coordinates]
    if not valid_clients:
        return list(clients)  # Return original order if no coords

    unvisited: list[Client] = list(valid_clients)
    route: list[Client] = []

    current_lat = depot_lat
    current_lon = depot_lon

    while unvisited:
        # Find nearest unvisited client
        nearest: Optional[Client] = None
        nearest_distance = float("inf")

        for client in unvisited:
            dist = haversine_distance(
                current_lat, current_lon,
                client.latitude, client.longitude
            )
            if dist < nearest_distance:
                nearest_distance = dist
                nearest = client

        if nearest is None:
            break

        route.append(nearest)
        unvisited.remove(nearest)
        current_lat = nearest.latitude
        current_lon = nearest.longitude

    return route


def calculate_route_distances(
    route: list[Client],
    depot_lat: float = DEPOT_LATITUDE,
    depot_lon: float = DEPOT_LONGITUDE,
) -> list[dict[str, float | str]]:
    """
    Calculate the distance from each stop to the next in the route.

    Args:
        route: Ordered list of clients in the route.
        depot_lat: Latitude of the starting depot.
        depot_lon: Longitude of the starting depot.

    Returns:
        List of dicts with 'client_name', 'distance_km', and
        'cumulative_km' for each stop.
    """
    distances: list[dict[str, float | str]] = []
    current_lat = depot_lat
    current_lon = depot_lon
    cumulative = 0.0

    for client in route:
        dist = haversine_distance(
            current_lat, current_lon,
            client.latitude, client.longitude,
        )
        cumulative += dist
        distances.append({
            "client_name": client.business_name,
            "distance_km": round(dist, 2),
            "cumulative_km": round(cumulative, 2),
        })
        current_lat = client.latitude
        current_lon = client.longitude

    return distances


# ──────────────────────────────────────────────────────────────────────
#  Group Assignment
# ──────────────────────────────────────────────────────────────────────

def validate_delivery_group(
    driver: Employee,
    helper: Employee,
    truck: Truck,
) -> list[str]:
    """
    Validate that a delivery group configuration is valid.

    Args:
        driver: The proposed driver.
        helper: The proposed helper.
        truck: The proposed truck.

    Returns:
        A list of error messages. Empty list means valid.
    """
    errors: list[str] = []

    if driver.role != EmployeeRole.DRIVER:
        errors.append(
            f"'{driver.full_name}' no tiene el rol de Conductor."
        )

    if helper.role != EmployeeRole.HELPER:
        errors.append(
            f"'{helper.full_name}' no tiene el rol de Ayudante."
        )

    if not driver.is_available:
        errors.append(
            f"El conductor '{driver.full_name}' no está disponible."
        )

    if not helper.is_available:
        errors.append(
            f"El ayudante '{helper.full_name}' no está disponible."
        )

    if not truck.is_available:
        errors.append(
            f"El camión '{truck.plate_number}' no está disponible."
        )

    if driver.id == helper.id:
        errors.append(
            "El conductor y el ayudante no pueden ser la misma persona."
        )

    return errors


def create_delivery_group(
    driver: Employee,
    helper: Employee,
    truck: Truck,
    selected_orders: list[Order],
    optimized_route: list[Client],
    group_id: Optional[int] = None,
) -> DeliveryGroup:
    """
    Assemble a complete DeliveryGroup with assigned orders and route.

    Args:
        driver: The assigned driver.
        helper: The assigned helper.
        truck: The assigned truck.
        selected_orders: Orders selected by the knapsack algorithm.
        optimized_route: Client visit order from nearest neighbor.
        group_id: Optional ID for the group.

    Returns:
        A fully assembled DeliveryGroup instance.

    Raises:
        ValueError: If validation fails or capacity exceeded.
    """
    # Validate group composition
    validation_errors = validate_delivery_group(driver, helper, truck)
    if validation_errors:
        raise ValueError(
            "Errores de validación:\n" + "\n".join(validation_errors)
        )

    # Check capacity
    total_bags = sum(order.quantity_bags for order in selected_orders)
    if total_bags > truck.capacity:
        raise ValueError(
            f"La carga total ({total_bags} bolsas) excede la capacidad "
            f"del camión ({truck.capacity} bolsas)."
        )

    # Build the group
    from datetime import datetime

    group = DeliveryGroup(
        id=group_id,
        driver_id=driver.id if driver.id is not None else 0,
        driver_name=driver.full_name,
        helper_id=helper.id if helper.id is not None else 0,
        helper_name=helper.full_name,
        truck_id=truck.id if truck.id is not None else 0,
        truck_plate=truck.plate_number,
        truck_capacity=truck.capacity,
        assigned_order_ids=[
            o.id for o in selected_orders if o.id is not None
        ],
        route_sequence=[
            c.id for c in optimized_route if c.id is not None
        ],
        total_bags_loaded=total_bags,
        status=DeliveryGroupStatus.READY,
        created_at=datetime.now(),
    )

    # Update order statuses
    for order in selected_orders:
        order.status = OrderStatus.LOADED

    return group


def get_total_bags(orders: list[Order]) -> int:
    """Calculate the sum of bags across a list of orders."""
    return sum(order.quantity_bags for order in orders)
