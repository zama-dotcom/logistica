from datamanager import DatabaseManager
from auth_system import AuthUtility

class UserController:
    """Controlador para la gestión de usuarios del sistema."""

    @staticmethod
    def create_user(username: str, password: str, role: str) -> dict:
        """Crea un nuevo usuario en el sistema."""
        if not username or not password:
            return {"success": False, "message": "El nombre de usuario y contraseña son obligatorios."}
        
        conn = DatabaseManager.get_connection()
        if not conn:
            return {"success": False, "message": "Error de conexión a la base de datos."}

        hashed_pwd = AuthUtility.hash_password(password)
        
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, hashed_pwd, role)
            )
            conn.commit()
            return {"success": True, "message": f"Usuario '{username}' creado exitosamente como {role}."}
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": f"Error al crear usuario: {str(e)}"}
        finally:
            cur.close()
            DatabaseManager.release_connection(conn)

    @staticmethod
    def update_password(username: str, new_password: str) -> dict:
        """Actualiza la contraseña de un usuario existente."""
        conn = DatabaseManager.get_connection()
        if not conn:
            return {"success": False, "message": "Error de conexión."}

        hashed_pwd = AuthUtility.hash_password(new_password)
        
        try:
            cur = conn.cursor()
            # Verificamos si existe el usuario primero
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if not cur.fetchone():
                return {"success": False, "message": "El usuario no existe."}

            cur.execute(
                "UPDATE users SET password_hash = %s WHERE username = %s",
                (hashed_pwd, username)
            )
            conn.commit()
            return {"success": True, "message": f"Contraseña actualizada para '{username}'."}
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": f"Error al actualizar: {str(e)}"}
        finally:
            cur.close()
            DatabaseManager.release_connection(conn)

    @staticmethod
    def get_all_users() -> list:
        """Obtiene la lista de todos los usuarios registrados."""
        conn = DatabaseManager.get_connection()
        if not conn:
            return []

        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, username, role FROM users ORDER BY id ASC")
            rows = cur.fetchall()
            return [{"id": row[0], "username": row[1], "role": row[2]} for row in rows]
        except Exception as e:
            print(f"Error al listar usuarios: {e}")
            return []
        finally:
            cur.close()
            DatabaseManager.release_connection(conn)
