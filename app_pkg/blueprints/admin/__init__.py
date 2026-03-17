"""
Admin blueprint package.

During the transition from monolithic app.py, this package will
gradually absorb admin routes. Sub-modules:
  - routes.py: dashboard, config
  - grupos.py: CRUD grupos
  - profesores.py: CRUD profesores
  - materias.py: CRUD materias
  - carreras.py: CRUD carreras
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
