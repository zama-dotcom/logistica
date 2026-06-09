from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QMessageBox,
    QHeaderView,
    QDoubleSpinBox
)

from controllers.delivery_controller import DeliveryController
from models.client_model import Client

class ClientsView(QWidget):
    """
    Client management view.
    Allows creating new clients with a form and lists existing clients.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("clientsView")
        self._controller = DeliveryController()
        
        self._setup_ui()
        self._connect_signals()
        self._load_data()

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Left: Form to add a new client
        form_group = QGroupBox("Registrar Nuevo Cliente")
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(12)

        # Form fields
        self._id_input = QLineEdit()
        self._id_input.setPlaceholderText("ID (Opcional, se genera auto si está vacío)")
        
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Nombre de la Ferretería")
        
        self._owner_input = QLineEdit()
        self._owner_input.setPlaceholderText("Nombre del Dueño (Contacto)")
        
        self._phone_input = QLineEdit()
        self._phone_input.setPlaceholderText("Número de Teléfono")

        self._lat_input = QDoubleSpinBox()
        self._lat_input.setRange(-90.0, 90.0)
        self._lat_input.setDecimals(6)
        self._lat_input.setPrefix("Latitud: ")
        
        self._lng_input = QDoubleSpinBox()
        self._lng_input.setRange(-180.0, 180.0)
        self._lng_input.setDecimals(6)
        self._lng_input.setPrefix("Longitud: ")

        form_layout.addWidget(QLabel("ID del Cliente:"))
        form_layout.addWidget(self._id_input)
        form_layout.addWidget(QLabel("Ferretería:"))
        form_layout.addWidget(self._name_input)
        form_layout.addWidget(QLabel("Dueño:"))
        form_layout.addWidget(self._owner_input)
        form_layout.addWidget(QLabel("Teléfono:"))
        form_layout.addWidget(self._phone_input)
        form_layout.addWidget(QLabel("Coordenadas:"))
        form_layout.addWidget(self._lat_input)
        form_layout.addWidget(self._lng_input)

        self._btn_save = QPushButton("✦ Guardar Cliente")
        self._btn_save.setObjectName("accentButton")
        form_layout.addWidget(self._btn_save)
        form_layout.addStretch()

        main_layout.addWidget(form_group, 1)

        # Right: Table with existing clients
        table_group = QGroupBox("Clientes Registrados")
        table_layout = QVBoxLayout(table_group)

        self._clients_table = QTableView()
        self._clients_table.setAlternatingRowColors(True)
        self._clients_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._clients_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._clients_table.verticalHeader().setVisible(False)

        self._clients_model = QStandardItemModel()
        self._clients_model.setHorizontalHeaderLabels([
            "ID", "Ferretería", "Dueño", "Teléfono", "Latitud", "Longitud"
        ])
        self._clients_table.setModel(self._clients_model)
        
        header = self._clients_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        table_layout.addWidget(self._clients_table)
        main_layout.addWidget(table_group, 2)

    def _connect_signals(self) -> None:
        self._btn_save.clicked.connect(self._on_save_client)

    def _load_data(self) -> None:
        self._clients_model.removeRows(0, self._clients_model.rowCount())
        clients = self._controller.get_clients()
        for client in clients:
            row = [
                QStandardItem(str(client.id)),
                QStandardItem(client.business_name),
                QStandardItem(client.contact_name),
                QStandardItem(client.phone),
                QStandardItem(str(client.latitude)),
                QStandardItem(str(client.longitude))
            ]
            for item in row:
                item.setEditable(False)
            self._clients_model.appendRow(row)

    def _on_save_client(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre de la ferretería es obligatorio.")
            return

        new_id = None
        if self._id_input.text().strip():
            try:
                new_id = int(self._id_input.text().strip())
            except ValueError:
                QMessageBox.warning(self, "Error", "El ID debe ser numérico.")
                return

        new_client = Client(
            id=new_id,
            business_name=name,
            contact_name=self._owner_input.text().strip(),
            phone=self._phone_input.text().strip(),
            latitude=self._lat_input.value(),
            longitude=self._lng_input.value(),
            is_active=True
        )

        success = self._controller.add_client(new_client)
        if success:
            QMessageBox.information(self, "Éxito", f"Cliente '{name}' registrado exitosamente.")
            self._clear_form()
            self._load_data()
        else:
            QMessageBox.warning(self, "Error", "Ocurrió un error o el ID ya existe.")

    def _clear_form(self) -> None:
        self._id_input.clear()
        self._name_input.clear()
        self._owner_input.clear()
        self._phone_input.clear()
        self._lat_input.setValue(0.0)
        self._lng_input.setValue(0.0)
