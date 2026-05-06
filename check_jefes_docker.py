
import os
from app import app
from models import db, User, Role

with app.app_context():
    try:
        jefes = User.query.filter(db.or_(User.rol == 'jefe_carrera', User.roles.any(Role.nombre == 'jefe_carrera'))).all()
        print(f"Total Jefes de Carrera encontrados: {len(jefes)}")
        
        for u in jefes:
            print(f"Usuario: {u.username}")
            print(f"  - Rol (legacy): {u.rol}")
            print(f"  - Roles (M2M): {[r.nombre for r in u.roles]}")
            print(f"  - Carreras (M2M): {len(u.carreras)}")
            print(f"  - Carrera ID (legacy): {u.carrera_id}")
            if not u.carreras and u.carrera_id:
                print(f"  !!! POSIBLE ERROR: Tiene carrera_id pero carreras M2M está vacío. Será bloqueado en varias rutas.")
        
    except Exception as e:
        print(f"Error: {e}")
