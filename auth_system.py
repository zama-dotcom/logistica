from PySide6.QtCore import QCryptographicHash
from datamanager import DatabaseManager

class AuthUtility:
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashes a password using SHA-256 via QCryptographicHash.
        """
        hash_obj = QCryptographicHash(QCryptographicHash.Algorithm.Sha256)
        hash_obj.addData(password.encode('utf-8'))
        return hash_obj.result().toHex().data().decode('utf-8')

    @staticmethod
    def has_users() -> bool:
        """Retorna True si hay al menos un usuario en la base de datos."""
        try:
            conn = DatabaseManager.get_connection()
            try:
                cur = conn.cursor()
                cur.execute("SELECT count(*) FROM users")
                count = cur.fetchone()[0]
                return count > 0
            finally:
                DatabaseManager.release_connection(conn)
        except Exception as e:
            print(f"[DEBUG] Error checking users: {e}")
            raise  # Re-raise para que main.py lo atrape

class LoginController:
    def __init__(self):
        # Ensure the DatabaseManager is initialized before calling login
        pass

    def login(self, username: str, password: str):
        """
        Verifies credentials against the database.
        Returns the user's role if successful, or None if failed.
        """
        conn = DatabaseManager.get_connection()
        if conn is None:
            return None
            
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            
            # 1. Obtenemos el hash almacenado para ese usuario
            cur.execute("SELECT password_hash, role FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            
            if result:
                stored_hash, role = result
                # 2. Hasheamos el password que el usuario acaba de escribir
                input_hash = AuthUtility.hash_password(password)
                
                # 3. Comparamos los hashes
                if input_hash == stored_hash:
                    return role  # Retorna 'BOSS', 'DISPATCH', etc.
            
            return None # Login fallido

        except Exception as e:
            print(f"Error en login: {e}")
            return None
        finally:
            DatabaseManager.release_connection(conn)
