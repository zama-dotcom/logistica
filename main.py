

from __future__ import annotations

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
# ----------------------------------------------------

from PySide6.QtWidgets import QApplication, QDialog

from views.main_view import MainWindow
from views.login_view import LoginView
from auth_system import AuthUtility


def load_stylesheet(app: QApplication) -> None:
    """Load the global QSS theme from styles.qss."""
    qss_path = os.path.join(os.path.dirname(__file__), "styles.qss")
    if os.path.exists(qss_path):
        try:
            # Intentar UTF-8 primero, luego latin-1 como fallback
            try:
                with open(qss_path, "r", encoding="utf-8") as qss_file:
                    stylesheet = qss_file.read()
            except UnicodeDecodeError:
                print("[WARNING] UTF-8 decoding failed, trying latin-1...")
                with open(qss_path, "r", encoding="latin-1") as qss_file:
                    stylesheet = qss_file.read()
            app.setStyleSheet(stylesheet)
            print(f"[INFO] QSS stylesheet loaded from: {qss_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load QSS stylesheet: {e}")
    else:
        print(f"[WARNING] QSS file not found: {qss_path}")


def main() -> None:
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Logística y Despacho")
    app.setOrganizationName("LogisticsApp")

    # Load global stylesheet
    load_stylesheet(app)

    # Initialize Database Connection Pool
    from datamanager import DatabaseManager
    try:
        DatabaseManager.initialize()
    except Exception as e:
        # Usamos Exception genérica aquí por si psycopg2 lanza un OperationalError
        print(f"[ERROR] Database initialization failed: {e}")
        print("[ERROR] Cannot proceed without database connection.")
        sys.exit(1)

    # Check if there are any users in the DB
    try:
        has_users = AuthUtility.has_users()
    except Exception as e:
        print(f"[ERROR] Failed to check users: {e}")
        sys.exit(1)
    
    if not has_users:
        # Bypass login for first-time setup as JEFE
        window = MainWindow(user_role="JEFE")
        window.show()
        sys.exit(app.exec())
    else:
        # Show Login View First
        login = LoginView()
        if login.exec() == QDialog.DialogCode.Accepted:
            user_role = login.user_role
            
            # Create and show main window with the authenticated role
            window = MainWindow(user_role=user_role)
            window.show()
            sys.exit(app.exec())
        else:
            # User cancelled login
            sys.exit(0)


if __name__ == "__main__":
    # Ensure it is run as the main script from console
    main()