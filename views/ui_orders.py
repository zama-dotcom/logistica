from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QTableView,
    QHeaderView,
    QLabel
)

from controllers.delivery_controller import DeliveryController

class OrdersView(QWidget):
    """
    Order management view.
    Shows pending orders and realized/executed orders.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ordersView")
        self._controller = DeliveryController()
        
        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        header = QLabel("Gestión de Pedidos")
        header.setObjectName("headerLabel")
        main_layout.addWidget(header)

        self._tab_widget = QTabWidget()
        main_layout.addWidget(self._tab_widget, 1)

        # Tab 1: Pedidos Pendientes
        pending_tab = QWidget()
        pending_layout = QVBoxLayout(pending_tab)
        
        self._pending_table = QTableView()
        self._pending_table.setAlternatingRowColors(True)
        self._pending_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._pending_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._pending_table.verticalHeader().setVisible(False)
        
        self._pending_model = QStandardItemModel()
        self._pending_model.setHorizontalHeaderLabels([
            "ID", "Ferretería", "Bolsas", "Fecha Programada", "Precio Unitario"
        ])
        self._pending_table.setModel(self._pending_model)
        
        header_p = self._pending_table.horizontalHeader()
        header_p.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        pending_layout.addWidget(self._pending_table)
        self._tab_widget.addTab(pending_tab, "⏳ Pedidos Pendientes")

        # Tab 2: Pedidos Realizados
        realized_tab = QWidget()
        realized_layout = QVBoxLayout(realized_tab)

        self._realized_table = QTableView()
        self._realized_table.setAlternatingRowColors(True)
        self._realized_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._realized_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._realized_table.verticalHeader().setVisible(False)
        
        self._realized_model = QStandardItemModel()
        self._realized_model.setHorizontalHeaderLabels([
            "Ferretería", "Bolsas Entregadas", "Monto Recaudado", "Grupo de Entrega", "Chofer"
        ])
        self._realized_table.setModel(self._realized_model)
        
        header_r = self._realized_table.horizontalHeader()
        header_r.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_r.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_r.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        realized_layout.addWidget(self._realized_table)
        self._tab_widget.addTab(realized_tab, "✅ Pedidos Realizados")

    def _load_data(self) -> None:
        # Load pending orders
        self._pending_model.removeRows(0, self._pending_model.rowCount())
        pending_orders = self._controller.get_pending_orders()
        for order in pending_orders:
            row = [
                QStandardItem(str(order.id)),
                QStandardItem(order.client_name),
                QStandardItem(str(order.quantity_bags)),
                QStandardItem(str(order.scheduled_date)),
                QStandardItem(f"Q {order.unit_price:,.2f}")
            ]
            for item in row:
                item.setEditable(False)
            self._pending_model.appendRow(row)

        # Load realized orders
        self._realized_model.removeRows(0, self._realized_model.rowCount())
        realized_orders = self._controller.get_realized_orders_info()
        for info in realized_orders:
            row = [
                QStandardItem(info['client_name']),
                QStandardItem(str(info['bags_delivered'])),
                QStandardItem(f"Q {info['payment_collected']:,.2f}"),
                QStandardItem(f"Grupo #{info['group_id']}"),
                QStandardItem(info['driver_name'])
            ]
            for item in row:
                item.setEditable(False)
            self._realized_model.appendRow(row)
