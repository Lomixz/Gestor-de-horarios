"""
Diagnostico y correccion de datos: profesores con carreras inexistentes.
Detecta registros huerfanos y los reasigna a carreras existentes.
"""
import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Carrera, Materia
from sqlalchemy import text

def diagnosticar_y_corregir():
    with app.app_context():
        print("=" * 80)
        print("DIAGNOSTICO Y CORRECCION DE DATOS - GESTOR DE HORARIOS")
        print("=" * 80)
        
        # 1. Listar carreras existentes
        carreras = Carrera.query.all()
        print(f"\n[INFO] CARRERAS EXISTENTES ({len(carreras)}):")
        carrera_ids = set()
        for c in carreras:
            print(f"   ID={c.id} | {c.codigo} | {c.nombre} | Activa={c.activa}")
            carrera_ids.add(c.id)
        
        if not carreras:
            print("\n[WARN] No hay carreras en la BD. No se puede reasignar nada.")
            return
        
        problemas = 0
        
        # 2. Verificar user_carreras con carrera_id inexistente
        print(f"\n[CHECK] VERIFICANDO TABLA user_carreras...")
        result = db.session.execute(text("""
            SELECT uc.user_id, uc.carrera_id, u.nombre, u.apellido, u.rol
            FROM user_carreras uc
            JOIN user u ON uc.user_id = u.id
            LEFT JOIN carrera c ON uc.carrera_id = c.id
            WHERE c.id IS NULL
        """))
        huerfanos_uc = result.fetchall()
        
        if huerfanos_uc:
            problemas += len(huerfanos_uc)
            print(f"   [WARN] {len(huerfanos_uc)} registros con carrera_id inexistente:")
            for row in huerfanos_uc:
                print(f"      User ID={row[0]} ({row[2]} {row[3]}, rol={row[4]}) -> carrera_id={row[1]} (NO EXISTE)")
            
            # Corregir: eliminar referencias huerfanas
            print(f"\n   [FIX] Eliminando {len(huerfanos_uc)} referencias huerfanas en user_carreras...")
            db.session.execute(text("""
                DELETE FROM user_carreras 
                WHERE carrera_id NOT IN (SELECT id FROM carrera)
            """))
            db.session.commit()
            print(f"   [OK] Referencias huerfanas eliminadas.")
        else:
            print("   [OK] Sin problemas.")
        
        # 3. Verificar profesor_materias con materia_id inexistente
        print(f"\n[CHECK] VERIFICANDO TABLA profesor_materias...")
        result = db.session.execute(text("""
            SELECT pm.profesor_id, pm.materia_id, u.nombre, u.apellido
            FROM profesor_materias pm
            JOIN user u ON pm.profesor_id = u.id
            LEFT JOIN materia m ON pm.materia_id = m.id
            WHERE m.id IS NULL
        """))
        huerfanos_pm = result.fetchall()
        
        if huerfanos_pm:
            problemas += len(huerfanos_pm)
            print(f"   [WARN] {len(huerfanos_pm)} registros con materia_id inexistente.")
            
            print(f"\n   [FIX] Eliminando {len(huerfanos_pm)} referencias huerfanas en profesor_materias...")
            db.session.execute(text("""
                DELETE FROM profesor_materias 
                WHERE materia_id NOT IN (SELECT id FROM materia)
            """))
            db.session.commit()
            print(f"   [OK] Referencias huerfanas eliminadas.")
        else:
            print("   [OK] Sin problemas.")
        
        # 4. Verificar materias con carrera_id inexistente
        print(f"\n[CHECK] VERIFICANDO MATERIAS CON CARRERA INEXISTENTE...")
        materias_huerfanas = Materia.query.filter(~Materia.carrera_id.in_(carrera_ids)).all() if carrera_ids else []
        if materias_huerfanas:
            problemas += len(materias_huerfanas)
            primera_carrera = carreras[0]
            print(f"   [WARN] {len(materias_huerfanas)} materias con carrera inexistente. Reasignando a '{primera_carrera.nombre}'...")
            for m in materias_huerfanas:
                print(f"      Materia {m.codigo} ({m.nombre}): carrera_id {m.carrera_id} -> {primera_carrera.id}")
                m.carrera_id = primera_carrera.id
            db.session.commit()
            print(f"   [OK] Materias reasignadas.")
        else:
            print("   [OK] Sin problemas.")
        
        # 5. Verificar profesores sin carrera asignada
        print(f"\n[CHECK] VERIFICANDO PROFESORES SIN CARRERA...")
        profesores = User.query.filter(
            User.rol.in_(['profesor_completo', 'profesor_asignatura']),
            User.activo == True
        ).all()
        
        sin_carrera = [p for p in profesores if not p.carreras]
        
        if sin_carrera:
            problemas += len(sin_carrera)
            primera_carrera = carreras[0]
            print(f"   [WARN] {len(sin_carrera)} profesores sin carrera. Asignando a '{primera_carrera.nombre}':")
            for p in sin_carrera:
                print(f"      ID={p.id} | {p.nombre} {p.apellido} -> {primera_carrera.nombre}")
                p.carreras.append(primera_carrera)
            db.session.commit()
            print(f"   [OK] Profesores reasignados.")
        else:
            print("   [OK] Todos los profesores tienen carrera.")
        
        # 6. Verificar coherencia profesor-materia-carrera
        print(f"\n[CHECK] VERIFICANDO COHERENCIA PROFESOR-MATERIA-CARRERA...")
        result = db.session.execute(text("""
            SELECT pm.profesor_id, pm.materia_id, 
                   u.nombre || ' ' || u.apellido AS profesor_nombre,
                   m.nombre AS materia_nombre,
                   m.carrera_id AS materia_carrera_id,
                   c.nombre AS carrera_materia
            FROM profesor_materias pm
            JOIN user u ON pm.profesor_id = u.id
            JOIN materia m ON pm.materia_id = m.id
            JOIN carrera c ON m.carrera_id = c.id
            WHERE m.carrera_id NOT IN (
                SELECT uc.carrera_id FROM user_carreras uc WHERE uc.user_id = pm.profesor_id
            )
        """))
        incoherencias = result.fetchall()
        
        if incoherencias:
            problemas += len(incoherencias)
            print(f"   [WARN] {len(incoherencias)} asignaciones profesor-materia incoherentes (materia de otra carrera).")
            for row in incoherencias[:10]:
                print(f"      {row[2]} -> {row[3]} (carrera: {row[5]})")
            if len(incoherencias) > 10:
                print(f"      ... y {len(incoherencias) - 10} mas")
            print(f"   [INFO] Estas asignaciones no se eliminan automaticamente (podrian ser intencionales).")
        else:
            print("   [OK] Todas las asignaciones son coherentes.")
        
        # 7. Resumen
        print(f"\n{'=' * 80}")
        if problemas == 0:
            print("[OK] NO SE ENCONTRARON PROBLEMAS. Base de datos limpia.")
        else:
            print(f"[FIX] SE CORRIGIERON {problemas} problema(s).")
        
        # Resumen final
        print(f"\n[RESUMEN] ESTADO FINAL:")
        print(f"   Carreras: {Carrera.query.count()}")
        print(f"   Materias: {Materia.query.count()}")
        profs = User.query.filter(User.rol.in_(['profesor_completo', 'profesor_asignatura'])).count()
        print(f"   Profesores: {profs}")
        sin = len([p for p in User.query.filter(User.rol.in_(['profesor_completo', 'profesor_asignatura'])).all() if not p.carreras])
        print(f"   Profesores con carrera: {profs - sin}")
        print(f"{'=' * 80}")

if __name__ == "__main__":
    diagnosticar_y_corregir()
