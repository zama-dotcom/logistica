

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional
import random

from models.client_model import Client
from models.delivery_group_model import DeliveryGroup, DeliveryGroupStatus
from models.employee_model import Employee, EmployeeRole
from models.order_model import Order, OrderStatus
from models.route_report_model import (
    LiquidationStatus,
    PaymentMethod,
    RouteReport,
)
from models.truck_model import Truck, TruckCapacity


class DeliveryController:
    

    def __init__(self) -> None:
        self._trucks: list[Truck] = []
        self._drivers: list[Employee] = []
        self._helpers: list[Employee] = []
        self._clients: list[Client] = []
        self._orders: list[Order] = []
        self._delivery_groups: list[DeliveryGroup] = []
        self._route_reports: list[RouteReport] = []
        self._next_group_id: int = 1
        self._next_report_id: int = 1

        self._load_sample_data()


    #  Accessors
    
    def get_trucks(self, available_only: bool = False) -> list[Truck]:
        #Return all trucks, optionally filtered to available only.
        if available_only:
            return [t for t in self._trucks if t.is_available and t.is_active]
        return list(self._trucks)

    def get_drivers(self, available_only: bool = False) -> list[Employee]:
        #Return all drivers, optionally filtered to available only.
        if available_only:
            return [
                d for d in self._drivers
                if d.is_available and d.is_active
            ]
        return list(self._drivers)

    def get_helpers(self, available_only: bool = False) -> list[Employee]:
        #Return all helpers, optionally filtered to available only.
        if available_only:
            return [
                h for h in self._helpers
                if h.is_available and h.is_active
            ]
        return list(self._helpers)

    def get_clients(self, active_only: bool = True) -> list[Client]:
        #Return all clients, optionally filtered to active only."""
        if active_only:
            return [c for c in self._clients if c.is_active]
        return list(self._clients)

    def get_pending_orders(self) -> list[Order]:
        #Return all orders with PENDING status.
        return [o for o in self._orders if o.status == OrderStatus.PENDING]

    def get_all_orders(self) -> list[Order]:
        #Return all orders regardless of status.
        return list(self._orders)

    def get_delivery_groups(self) -> list[DeliveryGroup]:
        #Return all delivery groups.
        return list(self._delivery_groups)

    def get_route_reports(
        self, group_id: Optional[int] = None
    ) -> list[RouteReport]:
        #Return route reports, optionally filtered by group ID.
        if group_id is not None:
            return [
                r for r in self._route_reports
                if r.delivery_group_id == group_id
            ]
        return list(self._route_reports)

    def get_realized_orders_info(self) -> list[dict]:
        realized = []
        group_driver_map = {}
        for group in self._delivery_groups:
            driver_name = "Desconocido"
            for d in self._drivers:
                if d.id == group.driver_id:
                    driver_name = d.full_name
                    break
            group_driver_map[group.id] = driver_name

        for report in self._route_reports:
            driver_name = group_driver_map.get(report.delivery_group_id, "Desconocido")
            realized.append({
                "client_name": report.client_name,
                "bags_delivered": report.bags_delivered,
                "payment_collected": report.payment_collected,
                "group_id": report.delivery_group_id,
                "driver_name": driver_name,
                "delivery_timestamp": report.delivery_timestamp
            })
        return realized


    #  Mutations
    

    def add_client(self, client: Client) -> bool:
        if client.id is None or client.id == 0:
            client.id = max((c.id for c in self._clients if c.id is not None), default=0) + 1
        elif any(c.id == client.id for c in self._clients):
            return False
        self._clients.append(client)
        return True

    def add_delivery_group(self, group: DeliveryGroup) -> DeliveryGroup:
        
        group.id = self._next_group_id
        self._next_group_id += 1
        self._delivery_groups.append(group)

        # Mark driver, helper, truck as unavailable
        for driver in self._drivers:
            if driver.id == group.driver_id:
                driver.is_available = False
        for helper in self._helpers:
            if helper.id == group.helper_id:
                helper.is_available = False
        for truck in self._trucks:
            if truck.id == group.truck_id:
                truck.is_available = False

        return group

    def remove_order_from_pending(self, order_id: int) -> Optional[Order]:
        
        for order in self._orders:
            if order.id == order_id and order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                return order
        return None

    def update_liquidation_status(
        self, report_id: int, status: LiquidationStatus
    ) -> bool:
        
        for report in self._route_reports:
            if report.id == report_id:
                report.liquidation_status = status
                return True
        return False

    def save_approved_liquidations(self) -> int:
        """
        Saves all approved liquidations to the database (simulated)
        and removes them from the pending list.
        Returns the number of liquidations saved.
        """
        approved_reports = [
            r for r in self._route_reports
            if r.liquidation_status == LiquidationStatus.APPROVED
        ]
        
        # Simulate saving to client's folder / database
        count = len(approved_reports)
        
        # Remove from active list
        self._route_reports = [
            r for r in self._route_reports
            if r.liquidation_status != LiquidationStatus.APPROVED
        ]
        
        return count

    def get_financial_summary(self) -> dict[str, float]:
        
        total_collected = sum(r.payment_collected for r in self._route_reports)
        total_pending = sum(
            r.payment_collected
            for r in self._route_reports
            if r.liquidation_status == LiquidationStatus.PENDING
        )
        total_approved = sum(
            r.payment_collected
            for r in self._route_reports
            if r.liquidation_status == LiquidationStatus.APPROVED
        )
        total_broken_bags = sum(r.broken_bags for r in self._route_reports)
        total_returned_bags = sum(r.bags_returned for r in self._route_reports)

        return {
            "total_collected": total_collected,
            "total_pending": total_pending,
            "total_approved": total_approved,
            "total_broken_bags": float(total_broken_bags),
            "total_returned_bags": float(total_returned_bags),
            "total_groups": float(len(self._delivery_groups)),
        }

    
    #  Sample Data
    

    def _load_sample_data(self) -> None:
        
        self._load_trucks()
        self._load_employees()
        self._load_clients()
        self._load_orders()
        self._load_sample_reports()

    def _load_trucks(self) -> None:
    
        self._trucks = [
            Truck(id=1, plate_number="P-0451A", capacity=TruckCapacity.LARGE,
                  brand="Hino", model_year=2022),
            Truck(id=2, plate_number="P-0892B", capacity=TruckCapacity.LARGE,
                  brand="Isuzu", model_year=2023),
            Truck(id=3, plate_number="P-1234C", capacity=TruckCapacity.SMALL,
                  brand="Mitsubishi", model_year=2021),
            Truck(id=4, plate_number="P-5678D", capacity=TruckCapacity.SMALL,
                  brand="Toyota", model_year=2024),
        ]

    def _load_employees(self) -> None:
        #Load sample drivers and helpers.
        self._drivers = [
            Employee(id=1, full_name="Carlos Méndez", role=EmployeeRole.DRIVER,
                     phone="5550-1001", license_number="B-12345"),
            Employee(id=2, full_name="Roberto Juárez", role=EmployeeRole.DRIVER,
                     phone="5550-1002", license_number="B-12346"),
            Employee(id=3, full_name="Miguel Santos", role=EmployeeRole.DRIVER,
                     phone="5550-1003", license_number="B-12347"),
        ]
        self._helpers = [
            Employee(id=4, full_name="José López", role=EmployeeRole.HELPER,
                     phone="5550-2001"),
            Employee(id=5, full_name="Pedro García", role=EmployeeRole.HELPER,
                     phone="5550-2002"),
            Employee(id=6, full_name="Luis Ramírez", role=EmployeeRole.HELPER,
                     phone="5550-2003"),
        ]

    def _load_clients(self) -> None:
        self._clients = [
            Client(id=1, business_name="Ferretería El Maestro",
                   contact_name="Ana Morales", phone="2200-1001",
                   address="6a Av. 12-45, Zona 1",
                   latitude=14.6407, longitude=-90.5133,
                   credit_limit=50000.0, current_balance=12000.0,
                   zone="Zona 1"),
            Client(id=2, business_name="Materiales Don Pedro",
                   contact_name="Pedro Castillo", phone="2200-1002",
                   address="Calz. Roosevelt 25-80, Zona 11",
                   latitude=14.6170, longitude=-90.5560,
                   credit_limit=75000.0, current_balance=30000.0,
                   zone="Zona 11"),
            Client(id=3, business_name="Ferretería La Económica",
                   contact_name="María Fuentes", phone="2200-1003",
                   address="7a Av. 3-12, Zona 9",
                   latitude=14.6080, longitude=-90.5230,
                   credit_limit=30000.0, current_balance=5000.0,
                   zone="Zona 9"),
            Client(id=4, business_name="Distribuidora Central",
                   contact_name="Jorge Hernández", phone="2200-1004",
                   address="Blvd. Los Próceres 18-90, Zona 10",
                   latitude=14.5920, longitude=-90.5070,
                   credit_limit=100000.0, current_balance=45000.0,
                   zone="Zona 10"),
            Client(id=5, business_name="Ferretería El Constructor",
                   contact_name="Carlos Paz", phone="2200-1005",
                   address="11 Calle 5-60, Zona 7",
                   latitude=14.6350, longitude=-90.5440,
                   credit_limit=60000.0, current_balance=20000.0,
                   zone="Zona 7"),
            Client(id=6, business_name="Hierros y Más",
                   contact_name="Lucía Ortega", phone="2200-1006",
                   address="Petapa Km 12, Zona 12",
                   latitude=14.5740, longitude=-90.5290,
                   credit_limit=40000.0, current_balance=15000.0,
                   zone="Zona 12"),
            Client(id=7, business_name="Mega Ferretería Sur",
                   contact_name="Fernando Solís", phone="2200-1007",
                   address="Av. Hincapié 9-30, Zona 13",
                   latitude=14.5830, longitude=-90.5190,
                   credit_limit=80000.0, current_balance=60000.0,
                   zone="Zona 13"),
            Client(id=8, business_name="Materiales Rápidos",
                   contact_name="Sandra Mejía", phone="2200-1008",
                   address="6a Calle 0-60, Zona 4",
                   latitude=14.6260, longitude=-90.5150,
                   credit_limit=35000.0, current_balance=10000.0,
                   zone="Zona 4"),
            Client(id=9, business_name="Ferretería Industrial",
                   contact_name="Raúl Estrada", phone="2200-1009",
                   address="Calz. Atanasio Tzul, Zona 12",
                   latitude=14.5800, longitude=-90.5350,
                   credit_limit=90000.0, current_balance=25000.0,
                   zone="Zona 12"),
            Client(id=10, business_name="El Clavo de Oro",
                   contact_name="Gloria Vásquez", phone="2200-1010",
                   address="18 Calle 2-15, Zona 15",
                   latitude=14.5890, longitude=-90.4870,
                   credit_limit=55000.0, current_balance=8000.0,
                   zone="Zona 15"),
        ]

    def _load_orders(self) -> None:
    
        today = date.today()
        order_data = [
            (1, 1, "Ferretería El Maestro", 80, 0),
            (2, 2, "Materiales Don Pedro", 120, 1),
            (3, 3, "Ferretería La Económica", 45, 0),
            (4, 4, "Distribuidora Central", 200, 2),
            (5, 5, "Ferretería El Constructor", 60, 1),
            (6, 6, "Hierros y Más", 90, 3),
            (7, 7, "Mega Ferretería Sur", 150, 2),
            (8, 8, "Materiales Rápidos", 35, 0),
            (9, 9, "Ferretería Industrial", 110, 4),
            (10, 10, "El Clavo de Oro", 70, 1),
            (11, 1, "Ferretería El Maestro", 55, 3),
            (12, 3, "Ferretería La Económica", 40, 2),
            (13, 4, "Distribuidora Central", 95, 4),
            (14, 6, "Hierros y Más", 130, 3),
            (15, 8, "Materiales Rápidos", 25, 1),
        ]

        self._orders = []
        for oid, cid, cname, bags, day_offset in order_data:
            self._orders.append(
                Order(
                    id=oid,
                    client_id=cid,
                    client_name=cname,
                    quantity_bags=bags,
                    scheduled_date=today + timedelta(days=day_offset),
                    status=OrderStatus.PENDING,
                    unit_price=round(random.uniform(45.0, 85.0), 2),
                    created_at=datetime.now() - timedelta(hours=random.randint(1, 48)),
                )
            )

    def _load_sample_reports(self) -> None:
        """Load sample route reports for the boss dashboard."""
        payment_methods = [
            PaymentMethod.CASH, PaymentMethod.TRANSFER,
        ]
        liquidation_statuses = [
            LiquidationStatus.PENDING, LiquidationStatus.APPROVED,
            LiquidationStatus.PENDING, LiquidationStatus.APPROVED,
            LiquidationStatus.REJECTED,
        ]

        self._route_reports = []
        promoters = ["Juan Pérez", "Ana García", "Carlos López", "María Gómez"]
        for i in range(1, 16):
            client_idx = (i - 1) % len(self._clients)
            client = self._clients[client_idx]
            self._route_reports.append(
                RouteReport(
                    id=i,
                    delivery_group_id=(i - 1) // 5 + 1,
                    promoter_name=promoters[i % len(promoters)],
                    client_id=client.id if client.id else i,
                    client_name=client.business_name,
                    bags_delivered=random.randint(20, 150),
                    bags_returned=random.randint(0, 5),
                    broken_bags=random.randint(0, 3),
                    payment_collected=round(
                        random.uniform(2000.0, 15000.0), 2
                    ),
                    payment_method=random.choice(payment_methods),
                    liquidation_status=LiquidationStatus.PENDING,
                    notes="",
                    delivery_timestamp=datetime.now() - timedelta(
                        hours=random.randint(1, 72)
                    ),
                    created_at=datetime.now() - timedelta(
                        hours=random.randint(73, 96)
                    ),
                )
            )
        self._next_report_id = 16
