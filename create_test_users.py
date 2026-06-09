from auth_system import AuthUtility
from datamanager import DatabaseManager

def create_user(username, password, role):
    """Crea un usuario en la base de datos con su contraseña encriptada."""
    # Obtenemos la conexión desde el DatabaseManager (que ya tiene los datos correctos)
    conn = DatabaseManager.get_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos.")
        return

    cur = conn.cursor()
    
    hashed_pwd = AuthUtility.hash_password(password)
    
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, hashed_pwd, role)
        )
        conn.commit()
        print(f"Usuario {username} creado exitosamente como {role}.")
    except Exception as e:
        print(f"Error al crear usuario: {e}")
        conn.rollback()
    finally:
        cur.close()
        DatabaseManager.release_connection(conn)

if __name__ == "__main__":
    print("Inicializando conexión a la base de datos...")
    DatabaseManager.initialize()
    
    # USO: Ejecuta esto en tu terminal para crear tus primeros usuarios
    # Nota: Usamos 'JEFE' y 'DESPACHO' porque son los valores definidos en la restricción CHECK de la tabla users
    create_user("jefe_admin", "1234", "JEFE")
    create_user("despacho_1", "1234", "DESPACHO")
