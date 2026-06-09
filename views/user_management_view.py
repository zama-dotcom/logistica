from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QFormLayout
)
from PySide6.QtCore import Qt
from controllers.user_controller import UserController

class UserManagementView(QWidget):
    """Vista para gestionar la creación y edición de usuarios (Solo Jefe)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Usuarios")
        self._setup_ui()
        self._load_users()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Título principal
        title_label = QLabel("Panel de Administración de Usuarios")
        title_label.setObjectName("headerTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Tabs para "Crear" y "Actualizar Contraseña"
        self.tabs = QTabWidget()
        
        # --- TAB 1: CREAR USUARIO ---
        tab_create = QWidget()
        create_layout = QFormLayout(tab_create)
        
        self.create_username = QLineEdit()
        self.create_password = QLineEdit()
        self.create_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.create_role = QComboBox()
        self.create_role.addItems(["JEFE", "DESPACHO", "PROMOTOR"])
        
        self.btn_create = QPushButton("Crear Usuario")
        self.btn_create.clicked.connect(self._handle_create_user)

        create_layout.addRow("Nombre de Usuario:", self.create_username)
        create_layout.addRow("Contraseña:", self.create_password)
        create_layout.addRow("Rol / Privilegios:", self.create_role)
        create_layout.addRow("", self.btn_create)
        
        # --- TAB 2: ACTUALIZAR CONTRASEÑA ---
        tab_update = QWidget()
        update_layout = QFormLayout(tab_update)
        
        self.update_user_cb = QComboBox()
        self.update_password = QLineEdit()
        self.update_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.btn_update = QPushButton("Actualizar Contraseña")
        self.btn_update.clicked.connect(self._handle_update_password)

        update_layout.addRow("Seleccionar Usuario:", self.update_user_cb)
        update_layout.addRow("Nueva Contraseña:", self.update_password)
        update_layout.addRow("", self.btn_update)

        # Agregar tabs
        self.tabs.addTab(tab_create, "Nuevo Usuario")
        self.tabs.addTab(tab_update, "Cambiar Contraseña")
        main_layout.addWidget(self.tabs)

        # --- TABLA DE USUARIOS EXISTENTES ---
        table_label = QLabel("Usuarios Registrados en el Sistema")
        table_label.setObjectName("headerTitle")
        main_layout.addWidget(table_label)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["ID", "Nombre de Usuario", "Rol Asignado"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Solo lectura
        
        main_layout.addWidget(self.users_table)

    def _load_users(self):
        """Carga los usuarios desde la base de datos a la tabla y al combobox de actualización."""
        users = UserController.get_all_users()
        
        # Actualizar tabla
        self.users_table.setRowCount(0)
        for row, user in enumerate(users):
            self.users_table.insertRow(row)
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user["id"])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user["username"]))
            self.users_table.setItem(row, 2, QTableWidgetItem(user["role"]))
            
        # Actualizar combobox
        self.update_user_cb.clear()
        for user in users:
            self.update_user_cb.addItem(user["username"])

    def _handle_create_user(self):
        """Maneja la creación de un usuario."""
        username = self.create_username.text().strip()
        password = self.create_password.text().strip()
        role = self.create_role.currentText()
        
        if not username:
            QMessageBox.warning(self, "Error", "El nombre de usuario es obligatorio.")
            return
            
        result = UserController.create_user(username, password, role)
        
        if result["success"]:
            QMessageBox.information(self, "Éxito", result["message"])
            self.create_username.clear()
            self.create_password.clear()
            self._load_users()
        else:
            QMessageBox.critical(self, "Error", result["message"])

    def _handle_update_password(self):
        """Maneja la actualización de contraseñas."""
        username = self.update_user_cb.currentText()
        new_password = self.update_password.text().strip()
        
        if not username or not new_password:
            QMessageBox.warning(self, "Error", "Debe seleccionar un usuario e ingresar una nueva contraseña.")
            return
            
        result = UserController.update_password(username, new_password)
        
        if result["success"]:
            QMessageBox.information(self, "Éxito", result["message"])
            self.update_password.clear()
        else:
            QMessageBox.critical(self, "Error", result["message"])
