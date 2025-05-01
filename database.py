from flask import Flask
import mariadb
import os
def get_connection():
    """Establece la conexión con la base de datos MariaDB."""
    try:
        conn = mariadb.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),  # Dirección del servidor, con valor predeterminado
            port=int(os.getenv("DB_PORT", 3306)),    # Puerto, con valor predeterminado
            user=os.getenv("DB_USER", "root"),       # Usuario, con valor predeterminado
            password=os.getenv("DB_PASSWORD", "root"),  # Contraseña, con valor predeterminado
            database=os.getenv("DB_NAME", "nomina")    # Nombre de la base de datos, con valor predeterminado
        )
        return conn
    except mariadb.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None