#!/usr/bin/env python3
"""
Migración: Eliminar columna password_temporal de la tabla user
Esta columna almacenaba contraseñas temporales en texto plano, lo cual es un riesgo de seguridad.

Uso: python migrate_remove_password_temporal.py
"""
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = 'instance/sistema_academico.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Base de datos no encontrada: {DB_PATH}")
        return False

    # Crear backup antes de migrar
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(DB_PATH, backup_path)
    print(f"Backup creado: {backup_path}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Verificar si la columna existe
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'password_temporal' not in columns:
            print("La columna password_temporal ya no existe. Migración no necesaria.")
            conn.close()
            return True

        # SQLite no soporta DROP COLUMN directamente en versiones antiguas
        # Usamos la estrategia de recrear la tabla
        print("Eliminando columna password_temporal...")

        # Obtener las columnas actuales menos password_temporal
        new_columns = [col for col in columns if col != 'password_temporal']
        columns_str = ', '.join(new_columns)

        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(f"CREATE TABLE user_new AS SELECT {columns_str} FROM user")
        cursor.execute("DROP TABLE user")
        cursor.execute("ALTER TABLE user_new RENAME TO user")
        cursor.execute("COMMIT")

        print("Columna password_temporal eliminada exitosamente.")
        print(f"Se puede eliminar el backup si todo funciona: {backup_path}")

        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error en migración: {e}")
        print(f"Restaurando desde backup: {backup_path}")
        shutil.copy2(backup_path, DB_PATH)
        return False

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
