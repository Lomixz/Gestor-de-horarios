
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
            
            # Verificar si el check en app.py pasaría
            if u.get_carreras_jefe_ids():
                print(">>> VERIFICACIÓN EXITOSA: El usuario ahora tendrá acceso a la sección de grupos.")
            else:
                print(">>> FALLO: El usuario sigue sin carreras asignadas según el nuevo chequeo.")
        else:
            print("Usuario no encontrado.")
            
    except Exception as e:
        print(f"Error: {e}")
