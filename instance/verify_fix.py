
import os
import sys
# Asegurar que el root del app esté en el path
sys.path.append('/app')

from app import app
from models import db, User

with app.app_context():
    try:
        u = User.query.filter_by(username='edurnetjhaquelin.luna').first()
        if u:
            print(f"User: {u.username}")
            print(f"is_jefe: {u.is_jefe_carrera()}")
            print(f"carreras_ids: {u.get_carreras_jefe_ids()}")
            print(f"has_carreras: {bool(u.get_carreras_jefe_ids())}")
            
            if u.get_carreras_jefe_ids():
                print(">>> VERIFICACION EXITOSA: El usuario ahora tendra acceso.")
            else:
                print(">>> FALLO: El usuario sigue sin carreras.")
        else:
            print("Usuario no encontrado.")
    except Exception as e:
        print(f"Error: {e}")
