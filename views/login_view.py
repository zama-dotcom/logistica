from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from auth_system import LoginController

class LoginView(QDialog):
    """
    Vista de inicio de sesión que requiere autenticación antes de
    permitir el acceso al sistema.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inicio de Sesión - Logística")
        self.setFixedSize(350, 250)
        
        # Atributo para almacenar el rol del usuario autenticado
        self.user_role = None
        
        # Inicializar el controlador
        self._auth_controller = LoginController()
        
        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz gráfica del login."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Encabezado (aplica color rojo desde styles.qss por el objectName)
        title_label = QLabel("Ingreso al Sistema")
        title_label.setObjectName("headerTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(15)

        # Campo de Usuario
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Nombre de usuario")
        layout.addWidget(self.user_input)

        # Campo de Contraseña
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        layout.addSpacing(20)

        # Botones
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Ingresar")
        self.login_btn.clicked.connect(self._handle_login)
        button_layout.addWidget(self.login_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("redButton") # Estilo rojo para cancelar
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _handle_login(self):
        """Valida las credenciales ingresadas."""
        username = self.user_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Debe ingresar usuario y contraseña.")
            return

        # Intentar autenticar
        role = self._auth_controller.login(username, password)

        if role:
            # Guardar el rol y aceptar el diálogo
            self.user_role = role
            QMessageBox.information(self, "Bienvenido", "Inicio de sesión exitoso.")
            self.accept()
        else:
            # Mostrar mensaje de error
            QMessageBox.critical(self, "Error de Acceso", "Credenciales incorrectas o usuario no encontrado.")
