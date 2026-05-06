
import os
import sys
sys.path.append('/app')

from app import app
from models import db, User, Role

with app.app_context():
    try:
        users = User.query.all()
        for u in users:
            print(f"User: {u.username}, Rol: {u.rol}, Roles M2M: {[r.nombre for r in u.roles]}")
    except Exception as e:
        print(f"Error: {e}")
