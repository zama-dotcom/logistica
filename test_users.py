#!/usr/bin/env python
"""Script para probar la creación de usuarios."""

from datamanager import DatabaseManager
from controllers.user_controller import UserController

# Inicializar conexión
DatabaseManager.initialize()

# Crear un nuevo usuario de prueba
print('=== Creando nuevo usuario ===')
result = UserController.create_user('newuser', 'password123', 'DESPACHO')
print(result['message'])

# Listar todos los usuarios
print('\n=== Usuarios en el sistema ===')
users = UserController.get_all_users()
for user in users:
    print(f'  ID: {user["id"]:2} | Usuario: {user["username"]:20} | Rol: {user["role"]}')

print('\n✅ Prueba completada')
