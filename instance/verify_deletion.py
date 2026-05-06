
import os
import sys
sys.path.append('/app')

from app import app
from models import db, Grupo, AsignacionProfesorGrupo, Materia, User, Carrera

with app.app_context():
    try:
        # 1. Crear datos de prueba
        print("Creando grupo de prueba...")
        carrera = Carrera.query.first()
        if not carrera:
            print("No hay carreras en la DB.")
            sys.exit(1)
            
        admin = User.query.filter_by(rol='admin').first()
        grupo = Grupo(carrera_id=carrera.id, cuatrimestre=1, numero_grupo=9999, turno='M', creado_por=admin.id)
        db.session.add(grupo)
        db.session.flush()
        
        materia = Materia.query.first()
        profesor = User.query.filter(User.rol.like('profesor%')).first()
        
        if materia and profesor:
            print(f"Asignando materia {materia.codigo} (Carrera {materia.carrera_id}) y profesor {profesor.username} al grupo {grupo.codigo}...")
            # Asegurar que el grupo use la carrera de la materia para evitar inconsistencias
            grupo.carrera_id = materia.carrera_id
            asig = AsignacionProfesorGrupo(
                profesor_id=profesor.id,
                materia_id=materia.id,
                grupo_id=grupo.id,
                horas_semanales=4
            )
            db.session.add(asig)
            db.session.commit()
            print("Datos de prueba creados.")
        else:
            print("No hay materias o profesores suficientes para la prueba.")
            db.session.rollback()
            sys.exit(1)
            
        # 2. Simular la eliminación (la nueva lógica)
        grupo_id = grupo.id
        codigo = grupo.codigo
        print(f"Intentando eliminar el grupo {grupo_id} ({codigo})...")
        
        # Refactored logic:
        target_grupo = Grupo.query.get(grupo_id)
        
        # Eliminar asignaciones explícitamente
        asignaciones = AsignacionProfesorGrupo.query.filter_by(grupo_id=grupo_id).all()
        for asig in asignaciones:
            db.session.delete(asig)
        db.session.flush()
        
        db.session.delete(target_grupo)
        db.session.commit()
        print(">>> ELIMINACION EXITOSA: El grupo y sus asignaciones se eliminaron sin errores de integridad.")
        
        # Verificar que la asignación ya no existe
        asig_check = AsignacionProfesorGrupo.query.filter_by(grupo_id=grupo_id).first()
        if not asig_check:
            print(">>> VERIFICACION DE CASCADA: Las asignaciones fueron eliminadas correctamente.")
        else:
            print("!!! ERROR: Las asignaciones siguen existiendo.")
            
    except Exception as e:
        db.session.rollback()
        print(f"!!! FALLO EN LA ELIMINACION: {e}")
        import traceback
        traceback.print_exc()
