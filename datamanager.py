import os
import sys
import psycopg2
from psycopg2 import pool

class DatabaseManager:
    _pool = None

    @classmethod
    def initialize(cls):
        """Inicializa el pool de conexiones a la base de datos."""
        try:
            print("Intentando establecer conexion con PostgreSQL...")
            
            # Aqui configuramos la conexion limpia
            cls._pool = psycopg2.pool.SimpleConnectionPool(
                1, 10, 
                dbname="fancesa_db",
                user="postgres",
                password="1234", 
                host="localhost",
                port="5432"
            )
            print("Conexion exitosa a la base de datos.")
            
        except Exception as e:
            cls._pool = None
            print("\n" + "="*50)
            print("CRITICAL DATABASE ERROR: Error en las credenciales o configuracion.")
            print("-> El usuario o la contrasena son incorrectos.")
            print("-> O la base de datos 'fancesa_db' no existe en pgAdmin.")
            print("="*50 + "\n")
            
            # Lanzamos un error con texto limpio sin tildes para proteger el main.py
            raise RuntimeError("Database connection failed. Verifique usuario y contrasena.")

    @classmethod
    def get_connection(cls):
        if cls._pool is None:
            raise RuntimeError("El pool de conexiones no ha sido inicializado.")
        return cls._pool.getconn()

    @classmethod
    def release_connection(cls, conn):
        if cls._pool is None:
            raise RuntimeError("El pool de conexiones no ha sido inicializado.")
        cls._pool.putconn(conn)