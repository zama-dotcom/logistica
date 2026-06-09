

from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMdiArea,
    QMdiSubWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from views.ui_dispatch import DispatchView
from views.ui_boss import BossView
from views.user_management_view import UserManagementView

class MainWindow(QMainWindow):
    """Main MDI window with menu-driven navigation."""

    def __init__(self, user_role: str = None) -> None:
        super().__init__()
        self.user_role = user_role
        self.setWindowTitle(f"Sistema de Logística y Despacho - Rol: {user_role}")
        self.setGeometry(100, 100, 1400, 900)
        self.showMaximized()

        # Track sub-windows
        self._dispatch_window: Optional[QMdiSubWindow] = None
        self._boss_window: Optional[QMdiSubWindow] = None
        self._user_management_window: Optional[QMdiSubWindow] = None

        # MDI Area as central widget
        self._mdi_area = QMdiArea()
        self.setCentralWidget(self._mdi_area)

        # Build menu bar
        self._create_menu_bar()

        # Status bar
        self.statusBar().showMessage(
            f"Sistema de Logística y Despacho — Usuario: {user_role} — Listo"
        )
        
        # Open appropriate window based on user role
        self._open_role_specific_window()

    def _create_menu_bar(self) -> None:
        """Create the application menu bar with all module entries."""
        menubar = self.menuBar()

        # ── Menu: Archivo ──
        file_menu = menubar.addMenu("Archivo")

        login_action = file_menu.addAction("Iniciar Sesión")
        login_action.triggered.connect(
            lambda: self._show_info("Iniciar Sesión")
        )

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Salir")
        exit_action.triggered.connect(self._close_app)

        # ── Role-based Menu Configuration ──
        # Roles que pueden acceder a Pedidos y Logística
        if self.user_role in ("JEFE", "DESPACHO"):
            # ── Menu: Pedidos ──
            orders_menu = menubar.addMenu("Pedidos")

            manage_orders_action = orders_menu.addAction("Gestionar Pedidos")
            manage_orders_action.triggered.connect(
                lambda: self._show_info("Gestionar Pedidos")
            )

            manage_clients_action = orders_menu.addAction("Gestionar Clientes")
            manage_clients_action.triggered.connect(
                lambda: self._show_info("Gestionar Clientes")
            )

        # Logística accesible para JEFE y DESPACHO
        if self.user_role in ("JEFE", "DESPACHO"):
            # ── Menu: Logística ──
            logistics_menu = menubar.addMenu("Logística")

            dispatch_action = logistics_menu.addAction("Despacho")
            dispatch_action.triggered.connect(self._open_dispatch_window)

            if self.user_role == "JEFE":
                boss_action = logistics_menu.addAction("Panel del Jefe")
                boss_action.triggered.connect(self._open_boss_window)

            # ── Menu: Dashboard ──
            dashboard_menu = menubar.addMenu("Dashboard")
            dashboard_action = dashboard_menu.addAction("Panel General")
            dashboard_action.triggered.connect(
                lambda: self._show_info("Panel General")
            )

        # PROMOTOR solo ve Pedidos
        if self.user_role == "PROMOTOR":
            orders_menu = menubar.addMenu("Pedidos")
            manage_orders_action = orders_menu.addAction("Ver Pedidos")
            manage_orders_action.triggered.connect(
                lambda: self._show_info("Ver Pedidos")
            )

        # Solo JEFE tiene acceso a Configuración
        if self.user_role == "JEFE":
            # ── Menu: Configuración ──
            config_menu = menubar.addMenu("Configuración")
            
            user_mgmt_action = config_menu.addAction("Gestión de Usuarios")
            user_mgmt_action.triggered.connect(self._open_user_management_window)
            
            config_action = config_menu.addAction("Preferencias")
            config_action.triggered.connect(
                lambda: self._show_info("Preferencias")
            )

        # ── Menu: Ayuda ──
        help_menu = menubar.addMenu("Ayuda")

        about_action = help_menu.addAction("Acerca de")
        about_action.triggered.connect(self._show_about)

    def _open_role_specific_window(self) -> None:
        """Automatically open the appropriate window based on user role."""
        if self.user_role == "DESPACHO":
            # Dispatch users see the dispatch window directly
            self._open_dispatch_window()
        elif self.user_role == "JEFE":
            # Boss users see the boss panel
            self._open_boss_window()
        # PROMOTOR and other roles will just see the menu without auto-opening


    #  Window Management
    

    def _open_mdi_window(
        self,
        widget: QWidget,
        title: str,
        tracker_attr: str,
    ) -> QMdiSubWindow:
        """
        Open a widget in an MDI sub-window, or activate if already open.

        Args:
            widget: The QWidget to display.
            title: Window title.
            tracker_attr: Attribute name on self to track the window reference.

        Returns:
            The MDI sub-window.
        """
        existing = getattr(self, tracker_attr, None)
        if existing is not None:
            try:
                if existing in self._mdi_area.subWindowList():
                    self._mdi_area.setActiveSubWindow(existing)
                    existing.showMaximized()
                    return existing
                else:
                    setattr(self, tracker_attr, None)
            except RuntimeError:
                setattr(self, tracker_attr, None)

        sub_window = self._mdi_area.addSubWindow(widget)
        sub_window.setWindowTitle(title)
        sub_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        sub_window.destroyed.connect(
            lambda: setattr(self, tracker_attr, None)
        )
        setattr(self, tracker_attr, sub_window)
        sub_window.showMaximized()
        return sub_window

    def _open_dispatch_window(self) -> None:
        """Open the Dispatch (Despacho) module."""
        dispatch_view = DispatchView()

        self._open_mdi_window(
            dispatch_view,
            "Módulo de Despacho",
            "_dispatch_window",
        )
        self.statusBar().showMessage("Módulo de Despacho abierto")

    def _open_boss_window(self) -> None:
        """Open the Boss (Jefe) module."""
        boss_view = BossView()
        self._open_mdi_window(
            boss_view,
            "Panel del Jefe",
            "_boss_window",
        )
        self.statusBar().showMessage("Panel del Jefe abierto")

    def _open_user_management_window(self) -> None:
        """Open the User Management module."""
        user_mgmt_view = UserManagementView()
        self._open_mdi_window(
            user_mgmt_view,
            "Gestión de Usuarios",
            "_user_management_window",
        )
        self.statusBar().showMessage("Gestión de Usuarios abierta")

    # ──────────────────────────────────────────────────────────────
    #  Utility Actions
    

    def _show_info(self, action_name: str) -> None:
        """Show a placeholder info message for unimplemented features."""
        QMessageBox.information(
            self,
            "Información",
            f"Ha seleccionado: {action_name}\n\n"
            f"Funcionalidad en desarrollo.",
        )

    def _show_about(self) -> None:
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "Acerca de",
            "<h2>Sistema de Logística y Despacho</h2>"
            "<p>Versión 1.0.0</p>"
            "<p>Sistema de gestión logística para despacho de productos, "
            "optimización de rutas y control financiero.</p>"
            "<p><b>Tecnologías:</b> Python, PySide6, PostgreSQL</p>",
        )

    def _close_app(self) -> None:
        """Prompt and close the application."""
        reply = QMessageBox.question(
            self,
            "Confirmar Salida",
            "¿Está seguro que desea salir del sistema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
