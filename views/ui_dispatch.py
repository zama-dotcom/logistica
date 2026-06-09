
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from controllers.delivery_controller import DeliveryController
from controllers.logistics_engine import (
    calculate_route_distances,
    create_delivery_group,
    get_total_bags,
    optimize_route,
    select_orders_for_truck,
)
from models.client_model import Client
from models.employee_model import Employee
from models.order_model import Order
from models.truck_model import Truck


class DispatchView(QWidget):
    """
    Main dispatch panel for managing deliveries.

    Sections:
    1. Group creation (driver + helper + truck)
    2. Smart loading with capacity visualization
    3. Optimized route table
    4. Route report dashboard
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dispatchView")

        # Controller
        self._controller = DeliveryController()

        # State
        self._selected_orders: list[Order] = []
        self._optimized_route: list[Client] = []
        self._selected_truck: Optional[Truck] = None
        self._selected_driver: Optional[Employee] = None
        self._selected_helper: Optional[Employee] = None

        self._setup_ui()
        self._connect_signals()
        self._populate_combos()

    # ──────────────────────────────────────────────────────────────
    #  UI Setup
    # ──────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """Build the complete dispatch view layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header = QLabel("Módulo de Despacho")
        header.setObjectName("headerLabel")
        main_layout.addWidget(header)

        subtitle = QLabel(
            "Gestione grupos de entrega, carga inteligente y rutas optimizadas"
        )
        subtitle.setObjectName("subtitleLabel")
        main_layout.addWidget(subtitle)

        # Separator
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(separator)

        # Tab widget for main sections
        self._tab_widget = QTabWidget()
        main_layout.addWidget(self._tab_widget, 1)

        # Tab 1: Dispatch Operations
        operations_tab = QWidget()
        self._tab_widget.addTab(operations_tab, "🚚 Despacho y Carga")
        self._setup_operations_tab(operations_tab)

        # Tab 2: Route Reports
        reports_tab = QWidget()
        self._tab_widget.addTab(reports_tab, "📋 Reportes de Ruta")
        self._setup_reports_tab(reports_tab)

    def _setup_operations_tab(self, container: QWidget) -> None:
        """Build the dispatch operations tab."""
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(12)

        # Top section: Group creation + Capacity
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(top_splitter)

        # Left: Group creation form
        group_panel = self._create_group_panel()
        top_splitter.addWidget(group_panel)

        # Right: Capacity visualization
        capacity_panel = self._create_capacity_panel()
        top_splitter.addWidget(capacity_panel)

        top_splitter.setSizes([450, 350])

        # Bottom section: Route table + Available clients
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(bottom_splitter, 1)

        # Left: Optimized route table
        route_panel = self._create_route_panel()
        bottom_splitter.addWidget(route_panel)

        # Right: Available clients list
        clients_panel = self._create_available_clients_panel()
        bottom_splitter.addWidget(clients_panel)

        bottom_splitter.setSizes([600, 300])

    def _create_group_panel(self) -> QGroupBox:
        """Create the delivery group assignment form."""
        group_box = QGroupBox("Crear Grupo de Entrega")
        layout = QVBoxLayout(group_box)
        layout.setSpacing(10)

        # Driver selection
        driver_label = QLabel("Conductor:")
        driver_label.setObjectName("subtitleLabel")
        layout.addWidget(driver_label)

        self._driver_combo = QComboBox()
        self._driver_combo.setPlaceholderText("Seleccione un conductor...")
        layout.addWidget(self._driver_combo)

        # Helper selection
        helper_label = QLabel("Ayudante:")
        helper_label.setObjectName("subtitleLabel")
        layout.addWidget(helper_label)

        self._helper_combo = QComboBox()
        self._helper_combo.setPlaceholderText("Seleccione un ayudante...")
        layout.addWidget(self._helper_combo)

        # Truck selection
        truck_label = QLabel("Camión:")
        truck_label.setObjectName("subtitleLabel")
        layout.addWidget(truck_label)

        self._truck_combo = QComboBox()
        self._truck_combo.setPlaceholderText("Seleccione un camión...")
        layout.addWidget(self._truck_combo)

        # Action buttons row
        buttons_layout = QHBoxLayout()

        self._btn_create_group = QPushButton("✦ Crear Grupo")
        buttons_layout.addWidget(self._btn_create_group)

        self._btn_smart_load = QPushButton("📦 Carga Inteligente")
        self._btn_smart_load.setObjectName("accentButton")
        self._btn_smart_load.setEnabled(False)
        buttons_layout.addWidget(self._btn_smart_load)

        layout.addLayout(buttons_layout)

        # Optimize route button
        self._btn_optimize_route = QPushButton("🗺 Optimizar Ruta")
        self._btn_optimize_route.setObjectName("accentButton")
        self._btn_optimize_route.setEnabled(False)
        layout.addWidget(self._btn_optimize_route)

        # Confirm & dispatch
        self._btn_dispatch = QPushButton("🚀 Confirmar y Despachar")
        self._btn_dispatch.setEnabled(False)
        layout.addWidget(self._btn_dispatch)

        layout.addStretch()
        return group_box

    def _create_capacity_panel(self) -> QGroupBox:
        """Create the truck capacity visualization panel."""
        group_box = QGroupBox("Capacidad del Camión")
        layout = QVBoxLayout(group_box)
        layout.setSpacing(12)

        # Capacity info
        self._capacity_label = QLabel("0 / 0 bolsas cargadas")
        self._capacity_label.setObjectName("capacityLabel")
        self._capacity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._capacity_label)

        # Progress bar
        self._capacity_bar = QProgressBar()
        self._capacity_bar.setObjectName("capacityBar")
        self._capacity_bar.setMinimum(0)
        self._capacity_bar.setMaximum(100)
        self._capacity_bar.setValue(0)
        self._capacity_bar.setFormat("%v%")
        layout.addWidget(self._capacity_bar)

        # Stats cards
        stats_layout = QHBoxLayout()

        # Orders loaded card
        orders_card = QFrame()
        orders_card.setObjectName("statsCard")
        orders_card_layout = QVBoxLayout(orders_card)
        self._orders_count_label = QLabel("0")
        self._orders_count_label.setObjectName("statsValue")
        self._orders_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orders_card_layout.addWidget(self._orders_count_label)
        orders_title = QLabel("PEDIDOS CARGADOS")
        orders_title.setObjectName("statsTitle")
        orders_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orders_card_layout.addWidget(orders_title)
        stats_layout.addWidget(orders_card)

        # Remaining capacity card
        remaining_card = QFrame()
        remaining_card.setObjectName("statsCard")
        remaining_card_layout = QVBoxLayout(remaining_card)
        self._remaining_label = QLabel("0")
        self._remaining_label.setObjectName("statsValue")
        self._remaining_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remaining_card_layout.addWidget(self._remaining_label)
        remaining_title = QLabel("BOLSAS RESTANTES")
        remaining_title.setObjectName("statsTitle")
        remaining_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remaining_card_layout.addWidget(remaining_title)
        stats_layout.addWidget(remaining_card)

        layout.addLayout(stats_layout)

        # Group status
        self._group_status_label = QLabel("Sin grupo creado")
        self._group_status_label.setObjectName("subtitleLabel")
        self._group_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._group_status_label)

        layout.addStretch()
        return group_box

    def _create_route_panel(self) -> QGroupBox:
        """Create the optimized route display table."""
        group_box = QGroupBox("Ruta Optimizada (Vecino más Cercano)")
        layout = QVBoxLayout(group_box)

        # Route table
        self._route_table = QTableView()
        self._route_table.setAlternatingRowColors(True)
        self._route_table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        self._route_table.setSelectionMode(
            QTableView.SelectionMode.SingleSelection
        )
        self._route_table.verticalHeader().setVisible(False)

        self._route_model = QStandardItemModel()
        self._route_model.setHorizontalHeaderLabels([
            "#", "Cliente", "Dirección", "Bolsas", "Distancia (km)"
        ])
        self._route_table.setModel(self._route_model)

        # Set column resize modes
        header = self._route_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 40)
        header.resizeSection(3, 80)
        header.resizeSection(4, 120)

        layout.addWidget(self._route_table, 1)

        # Remove button
        self._btn_remove_client = QPushButton("✕ Quitar Cliente Seleccionado")
        self._btn_remove_client.setObjectName("dangerButton")
        self._btn_remove_client.setEnabled(False)
        layout.addWidget(self._btn_remove_client)

        return group_box

    def _create_available_clients_panel(self) -> QGroupBox:
        """Create the available clients sidebar list."""
        group_box = QGroupBox("Clientes Disponibles")
        layout = QVBoxLayout(group_box)

        info_label = QLabel(
            "Seleccione un cliente y agréguelo a la ruta actual"
        )
        info_label.setObjectName("subtitleLabel")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self._available_clients_list = QListWidget()
        layout.addWidget(self._available_clients_list, 1)

        self._btn_add_client = QPushButton("+ Agregar a la Ruta")
        self._btn_add_client.setObjectName("secondaryButton")
        self._btn_add_client.setEnabled(False)
        layout.addWidget(self._btn_add_client)

        return group_box

    def _setup_reports_tab(self, container: QWidget) -> None:
        """Build the route reports dashboard tab."""
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(12)

        # Section header
        section_label = QLabel("Reportes de Entrega")
        section_label.setObjectName("sectionLabel")
        layout.addWidget(section_label)

        description = QLabel(
            "Información reportada por los ayudantes: pagos recibidos, "
            "bolsas rotas (merma) y observaciones por cliente."
        )
        description.setObjectName("subtitleLabel")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Reports table
        self._reports_table = QTableView()
        self._reports_table.setAlternatingRowColors(True)
        self._reports_table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        self._reports_table.verticalHeader().setVisible(False)

        self._reports_model = QStandardItemModel()
        self._reports_model.setHorizontalHeaderLabels([
            "ID", "Grupo", "Cliente", "Bolsas\nEntregadas",
            "Merma", "Pago\nRecibido", "Método", "Estado"
        ])
        self._reports_table.setModel(self._reports_model)

        # Column sizing
        rh = self._reports_table.horizontalHeader()
        rh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        rh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        rh.resizeSection(0, 40)
        rh.resizeSection(1, 60)
        for col in range(3, 8):
            rh.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._reports_table, 1)

        # Load reports data
        self._load_reports_data()

    # ──────────────────────────────────────────────────────────────
    #  Data Population
    # ──────────────────────────────────────────────────────────────

    def _populate_combos(self) -> None:
        """Fill combo boxes with available drivers, helpers, and trucks."""
        # Drivers
        self._driver_combo.clear()
        drivers = self._controller.get_drivers(available_only=True)
        for driver in drivers:
            self._driver_combo.addItem(
                f"{driver.full_name} — {driver.phone}",
                userData=driver,
            )

        # Helpers
        self._helper_combo.clear()
        helpers = self._controller.get_helpers(available_only=True)
        for helper in helpers:
            self._helper_combo.addItem(
                f"{helper.full_name} — {helper.phone}",
                userData=helper,
            )

        # Trucks
        self._truck_combo.clear()
        trucks = self._controller.get_trucks(available_only=True)
        for truck in trucks:
            self._truck_combo.addItem(
                f"{truck.plate_number} — {truck.capacity_label} "
                f"({truck.brand} {truck.model_year})",
                userData=truck,
            )

        # Populate available clients list
        self._refresh_available_clients()

    def _refresh_available_clients(self) -> None:
        """Refresh the available clients sidebar."""
        self._available_clients_list.clear()
        clients = self._controller.get_clients(active_only=True)

        # Filter out clients already in the route
        route_client_ids = {c.id for c in self._optimized_route}
        for client in clients:
            if client.id not in route_client_ids:
                item = QListWidgetItem(
                    f"🏪 {client.business_name} — {client.zone}"
                )
                item.setData(Qt.ItemDataRole.UserRole, client)
                self._available_clients_list.addItem(item)

    def _update_capacity_display(self) -> None:
        """Update the capacity progress bar and labels."""
        if self._selected_truck is None:
            self._capacity_label.setText("0 / 0 bolsas cargadas")
            self._capacity_bar.setMaximum(100)
            self._capacity_bar.setValue(0)
            self._orders_count_label.setText("0")
            self._remaining_label.setText("0")
            return

        capacity = self._selected_truck.capacity
        loaded = get_total_bags(self._selected_orders)
        percent = int((loaded / capacity) * 100) if capacity > 0 else 0

        self._capacity_label.setText(
            f"{loaded} / {capacity} bolsas cargadas"
        )
        self._capacity_bar.setMaximum(100)
        self._capacity_bar.setValue(min(percent, 100))
        self._capacity_bar.setFormat(f"{percent}%")

        self._orders_count_label.setText(str(len(self._selected_orders)))
        self._remaining_label.setText(str(max(0, capacity - loaded)))

    def _update_route_table(self) -> None:
        """Refresh the route table with optimized route data."""
        self._route_model.removeRows(0, self._route_model.rowCount())

        if not self._optimized_route:
            return

        distances = calculate_route_distances(self._optimized_route)

        # Build a map of client_id -> total bags from selected orders
        client_bags: dict[int, int] = {}
        for order in self._selected_orders:
            cid = order.client_id
            client_bags[cid] = client_bags.get(cid, 0) + order.quantity_bags

        for idx, (client, dist_info) in enumerate(
            zip(self._optimized_route, distances), start=1
        ):
            row = [
                QStandardItem(str(idx)),
                QStandardItem(client.business_name),
                QStandardItem(client.address),
                QStandardItem(str(client_bags.get(client.id, 0))),
                QStandardItem(str(dist_info["distance_km"])),
            ]
            # Center-align number columns
            row[0].setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            row[3].setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            row[4].setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Make rows read-only
            for item in row:
                item.setEditable(False)

            # Store client reference
            row[0].setData(client, Qt.ItemDataRole.UserRole)

            self._route_model.appendRow(row)

    def _load_reports_data(self) -> None:
        """Load route reports into the reports table."""
        self._reports_model.removeRows(0, self._reports_model.rowCount())

        reports = self._controller.get_route_reports()
        for report in reports:
            row = [
                QStandardItem(str(report.id)),
                QStandardItem(str(report.delivery_group_id)),
                QStandardItem(report.client_name),
                QStandardItem(str(report.bags_delivered)),
                QStandardItem(str(report.broken_bags)),
                QStandardItem(f"Q {report.payment_collected:,.2f}"),
                QStandardItem(report.payment_method_display),
                QStandardItem(report.liquidation_status_display),
            ]

            for item in row:
                item.setEditable(False)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Left-align client name
            row[2].setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

            self._reports_model.appendRow(row)

    # ──────────────────────────────────────────────────────────────
    #  Signal Connections
    # ──────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """Connect UI signals to handler slots."""
        self._btn_create_group.clicked.connect(self._on_create_group)
        self._btn_smart_load.clicked.connect(self._on_smart_load)
        self._btn_optimize_route.clicked.connect(self._on_optimize_route)
        self._btn_dispatch.clicked.connect(self._on_dispatch)
        self._btn_remove_client.clicked.connect(self._on_remove_client)
        self._btn_add_client.clicked.connect(self._on_add_client)

        self._route_table.selectionModel().selectionChanged.connect(
            self._on_route_selection_changed
        )
        self._available_clients_list.currentItemChanged.connect(
            self._on_available_client_changed
        )
        self._truck_combo.currentIndexChanged.connect(
            self._on_truck_changed
        )

    # ──────────────────────────────────────────────────────────────
    #  Event Handlers
    # ──────────────────────────────────────────────────────────────

    def _on_truck_changed(self, index: int) -> None:
        """Handle truck selection change."""
        if index >= 0:
            self._selected_truck = self._truck_combo.currentData()
            self._update_capacity_display()

    def _on_create_group(self) -> None:
        """Handle 'Create Group' button click."""
        driver_idx = self._driver_combo.currentIndex()
        helper_idx = self._helper_combo.currentIndex()
        truck_idx = self._truck_combo.currentIndex()

        if driver_idx < 0 or helper_idx < 0 or truck_idx < 0:
            QMessageBox.warning(
                self,
                "Campos Incompletos",
                "Debe seleccionar un conductor, un ayudante y un camión "
                "para crear el grupo de entrega.",
            )
            return

        self._selected_driver = self._driver_combo.currentData()
        self._selected_helper = self._helper_combo.currentData()
        self._selected_truck = self._truck_combo.currentData()

        if self._selected_driver is None or self._selected_helper is None:
            return
        if self._selected_truck is None:
            return

        # Update UI state
        self._group_status_label.setText(
            f"✓ Grupo: {self._selected_driver.full_name} + "
            f"{self._selected_helper.full_name} → "
            f"{self._selected_truck.plate_number}"
        )
        self._btn_smart_load.setEnabled(True)
        self._btn_create_group.setEnabled(False)
        self._driver_combo.setEnabled(False)
        self._helper_combo.setEnabled(False)
        self._truck_combo.setEnabled(False)

        self._update_capacity_display()

        QMessageBox.information(
            self,
            "Grupo Creado",
            f"Grupo de entrega creado exitosamente.\n\n"
            f"Conductor: {self._selected_driver.full_name}\n"
            f"Ayudante: {self._selected_helper.full_name}\n"
            f"Camión: {self._selected_truck.plate_number} "
            f"({self._selected_truck.capacity} bolsas)\n\n"
            f"Ahora puede ejecutar la Carga Inteligente.",
        )

    def _on_smart_load(self) -> None:
        """Handle 'Smart Loading' button — runs knapsack algorithm."""
        if self._selected_truck is None:
            return

        pending_orders = self._controller.get_pending_orders()
        clients = self._controller.get_clients()

        if not pending_orders:
            QMessageBox.information(
                self,
                "Sin Pedidos",
                "No hay pedidos pendientes para cargar.",
            )
            return

        # Run knapsack algorithm
        self._selected_orders = select_orders_for_truck(
            orders=pending_orders,
            truck_capacity=self._selected_truck.capacity,
            clients=clients,
            lookahead_days=5,
        )

        if not self._selected_orders:
            QMessageBox.information(
                self,
                "Sin Resultados",
                "El algoritmo no encontró pedidos que se ajusten "
                "a la capacidad del camión.",
            )
            return

        self._update_capacity_display()
        self._btn_optimize_route.setEnabled(True)

        total = get_total_bags(self._selected_orders)
        QMessageBox.information(
            self,
            "Carga Inteligente Completada",
            f"Se seleccionaron {len(self._selected_orders)} pedidos "
            f"con un total de {total} bolsas.\n\n"
            f"Capacidad utilizada: {total}/{self._selected_truck.capacity} "
            f"({int(total / self._selected_truck.capacity * 100)}%)\n\n"
            f"Ahora puede Optimizar la Ruta.",
        )

    def _on_optimize_route(self) -> None:
        """Handle 'Optimize Route' button — runs nearest neighbor."""
        if not self._selected_orders:
            return

        # Get unique clients from selected orders
        client_map: dict[int, Client] = {
            c.id: c
            for c in self._controller.get_clients()
            if c.id is not None
        }

        unique_client_ids = list(
            dict.fromkeys(o.client_id for o in self._selected_orders)
        )
        clients_to_visit = [
            client_map[cid]
            for cid in unique_client_ids
            if cid in client_map
        ]

        # Run nearest neighbor
        self._optimized_route = optimize_route(clients_to_visit)
        self._update_route_table()
        self._refresh_available_clients()
        self._btn_dispatch.setEnabled(True)
        self._btn_remove_client.setEnabled(False)

        QMessageBox.information(
            self,
            "Ruta Optimizada",
            f"La ruta ha sido optimizada con {len(self._optimized_route)} "
            f"paradas usando el algoritmo de Vecino más Cercano.\n\n"
            f"Puede reordenar manualmente quitando y agregando clientes.",
        )

    def _on_dispatch(self) -> None:
        """Handle 'Confirm & Dispatch' button."""
        if (
            self._selected_driver is None
            or self._selected_helper is None
            or self._selected_truck is None
        ):
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar Despacho",
            f"¿Está seguro de despachar este grupo?\n\n"
            f"Conductor: {self._selected_driver.full_name}\n"
            f"Ayudante: {self._selected_helper.full_name}\n"
            f"Camión: {self._selected_truck.plate_number}\n"
            f"Pedidos: {len(self._selected_orders)}\n"
            f"Paradas: {len(self._optimized_route)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            group = create_delivery_group(
                driver=self._selected_driver,
                helper=self._selected_helper,
                truck=self._selected_truck,
                selected_orders=self._selected_orders,
                optimized_route=self._optimized_route,
            )
            self._controller.add_delivery_group(group)

            QMessageBox.information(
                self,
                "Despacho Exitoso",
                f"El grupo #{group.id} ha sido despachado exitosamente.\n\n"
                f"Total bolsas: {group.total_bags_loaded}\n"
                f"Estado: {group.status_display}",
            )

            # Reset form
            self._reset_form()

        except ValueError as exc:
            QMessageBox.critical(
                self,
                "Error de Validación",
                str(exc),
            )

    def _on_remove_client(self) -> None:
        """Remove the selected client from the optimized route."""
        selection = self._route_table.selectionModel().selectedRows()
        if not selection:
            return

        row_idx = selection[0].row()
        item = self._route_model.item(row_idx, 0)
        if item is None:
            return

        client: Client = item.data(Qt.ItemDataRole.UserRole)
        if client is None:
            return

        # Remove from route
        self._optimized_route = [
            c for c in self._optimized_route if c.id != client.id
        ]

        # Remove associated orders
        self._selected_orders = [
            o for o in self._selected_orders if o.client_id != client.id
        ]

        self._update_route_table()
        self._update_capacity_display()
        self._refresh_available_clients()

    def _on_add_client(self) -> None:
        """Add a client from the available list to the route."""
        current_item = self._available_clients_list.currentItem()
        if current_item is None:
            return

        client: Client = current_item.data(Qt.ItemDataRole.UserRole)
        if client is None:
            return

        # Check if client has pending orders
        pending = [
            o
            for o in self._controller.get_pending_orders()
            if o.client_id == client.id
        ]

        if not pending:
            QMessageBox.warning(
                self,
                "Sin Pedidos",
                f"El cliente '{client.business_name}' no tiene "
                f"pedidos pendientes para agregar.",
            )
            return

        # Check capacity
        if self._selected_truck is not None:
            current_load = get_total_bags(self._selected_orders)
            new_bags = sum(o.quantity_bags for o in pending)
            if current_load + new_bags > self._selected_truck.capacity:
                QMessageBox.warning(
                    self,
                    "Capacidad Excedida",
                    f"Agregar este cliente ({new_bags} bolsas) "
                    f"excedería la capacidad del camión.\n"
                    f"Carga actual: {current_load} / "
                    f"{self._selected_truck.capacity}",
                )
                return

        # Add orders and re-optimize route
        self._selected_orders.extend(pending)
        self._optimized_route.append(client)

        # Re-optimize with new client
        self._optimized_route = optimize_route(self._optimized_route)

        self._update_route_table()
        self._update_capacity_display()
        self._refresh_available_clients()

    def _on_route_selection_changed(self) -> None:
        """Enable/disable remove button based on selection."""
        has_selection = bool(
            self._route_table.selectionModel().selectedRows()
        )
        self._btn_remove_client.setEnabled(has_selection)

    def _on_available_client_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        """Enable/disable add button based on selection."""
        self._btn_add_client.setEnabled(current is not None)

    # ──────────────────────────────────────────────────────────────
    #  Utilities
    # ──────────────────────────────────────────────────────────────

    def _reset_form(self) -> None:
        """Reset the entire dispatch form to initial state."""
        self._selected_orders = []
        self._optimized_route = []
        self._selected_truck = None
        self._selected_driver = None
        self._selected_helper = None

        self._driver_combo.setEnabled(True)
        self._helper_combo.setEnabled(True)
        self._truck_combo.setEnabled(True)
        self._btn_create_group.setEnabled(True)
        self._btn_smart_load.setEnabled(False)
        self._btn_optimize_route.setEnabled(False)
        self._btn_dispatch.setEnabled(False)
        self._btn_remove_client.setEnabled(False)

        self._group_status_label.setText("Sin grupo creado")
        self._route_model.removeRows(0, self._route_model.rowCount())
        self._update_capacity_display()

        # Refresh combos with newly available resources
        self._populate_combos()
