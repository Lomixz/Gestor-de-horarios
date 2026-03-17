"""Pytest fixtures for testing the Gestor de Horarios."""
import os
import pytest
from datetime import time

# Set test environment before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'memory://'


@pytest.fixture(scope='session')
def app():
    """Create Flask app for testing."""
    from flask import Flask
    from models import db, User, Horario, Carrera, Materia, Grupo, Role
    from models import AsignacionProfesorGrupo, DisponibilidadProfesor, HorarioAcademico

    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'

    db.init_app(app)

    with app.app_context():
        db.create_all()

    yield app


@pytest.fixture(autouse=True)
def db_session(app):
    """Provide a clean database session for each test."""
    from models import db
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        # Clean all tables
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture
def seed_data(app, db_session):
    """Seed base test data: admin, roles, time slots, career, subjects, groups."""
    from models import db, User, Horario, Carrera, Materia, Grupo, Role
    from models import AsignacionProfesorGrupo, DisponibilidadProfesor

    with app.app_context():
        # Create roles
        admin_role = Role(nombre='admin', descripcion='Administrador')
        prof_role = Role(nombre='profesor_completo', descripcion='Profesor TC')
        db.session.add_all([admin_role, prof_role])
        db.session.flush()

        # Create admin user
        admin = User(
            username='admin',
            email='admin@test.com',
            password='Admin123!',
            nombre='Admin',
            apellido='Test',
            rol='admin',
        )
        admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.flush()

        # Create time slots (7am-1pm, 6 slots of 1 hour)
        horarios = []
        for h in range(7, 13):
            horario = Horario(
                hora_inicio=time(h, 0),
                hora_fin=time(h + 1, 0),
                turno='matutino',
            )
            db.session.add(horario)
            horarios.append(horario)
        db.session.flush()

        # Create career
        carrera = Carrera(
            nombre='Ingeniería en Software',
            codigo='ISW',
        )
        db.session.add(carrera)
        db.session.flush()

        # Create subjects (3 subjects, 2 hours/week each)
        materias = []
        for i, (nombre, codigo) in enumerate([
            ('Programación I', 'PROG1'),
            ('Bases de Datos', 'BD1'),
            ('Redes', 'RED1'),
        ]):
            materia = Materia(
                nombre=nombre,
                codigo=codigo,
                horas_semana=2,
                cuatrimestre=1,
                carrera_id=carrera.id,
            )
            db.session.add(materia)
            materias.append(materia)
        db.session.flush()

        # Create professors (2 professors)
        profesores = []
        for i, (nombre, apellido) in enumerate([
            ('Juan', 'García'),
            ('María', 'López'),
        ]):
            prof = User(
                username=f'prof{i+1}',
                email=f'prof{i+1}@test.com',
                password='Prof123!',
                nombre=nombre,
                apellido=apellido,
                rol='profesor_completo',
                tipo_profesor='Tiempo Completo',
            )
            prof.roles.append(prof_role)
            # Assign subjects
            prof.materias.extend(materias[:2] if i == 0 else materias[1:])
            db.session.add(prof)
            profesores.append(prof)
        db.session.flush()

        # Create group
        grupo = Grupo(
            codigo='ISW1A',
            nombre='Grupo A',
            cuatrimestre=1,
            turno='matutino',
            carrera_id=carrera.id,
        )
        grupo.materias.extend(materias)
        db.session.add(grupo)
        db.session.flush()

        # Create professor-group-subject assignments
        # Prof1 teaches PROG1 and BD1 in ISW1A
        for materia in materias[:2]:
            asig = AsignacionProfesorGrupo(
                profesor_id=profesores[0].id,
                materia_id=materia.id,
                grupo_id=grupo.id,
                horas_semana=materia.horas_semana,
            )
            db.session.add(asig)

        # Prof2 teaches RED1 in ISW1A
        asig = AsignacionProfesorGrupo(
            profesor_id=profesores[1].id,
            materia_id=materias[2].id,
            grupo_id=grupo.id,
            horas_semana=materias[2].horas_semana,
        )
        db.session.add(asig)
        db.session.flush()

        # Set availability for both professors (all slots Mon-Fri)
        dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
        for prof in profesores:
            for horario in horarios:
                for dia in dias:
                    disp = DisponibilidadProfesor(
                        profesor_id=prof.id,
                        horario_id=horario.id,
                        dia_semana=dia,
                        disponible=True,
                        creado_por=admin.id,
                    )
                    db.session.add(disp)

        db.session.commit()

        return {
            'admin': admin,
            'profesores': profesores,
            'horarios': horarios,
            'carrera': carrera,
            'materias': materias,
            'grupo': grupo,
        }
