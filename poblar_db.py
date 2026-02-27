"""
Script para poblar la base de datos del Gestor de Horarios.

Acciones:
1. Elimina todas las carreras excepto 'Ingeniería en Sistemas' y 'Administración de Empresas'
2. Elimina materias, grupos, asignaciones y disponibilidad de carreras eliminadas
3. Agrega las carreras 'Robótica' y 'Aduanas'
4. Agrega materias respectivas para las 4 carreras
5. Agrega profesores de ejemplo
6. Agrega grupos SIN asignar materias (para que el usuario lo haga manualmente)
"""

import os
import sys

# Configurar el path
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, basedir)

from app import app
from models import (
    db, Carrera, Materia, User, Grupo, Role,
    AsignacionProfesorGrupo, grupo_materias, profesor_materias,
    user_carreras
)


def limpiar_y_poblar():
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("ERROR: No se encontró el usuario admin. Ejecuta la app primero.")
            return
        
        admin_id = admin.id
        
        # =============================================
        # 1. IDENTIFICAR CARRERAS A CONSERVAR Y ELIMINAR
        # =============================================
        print("\n=== PASO 1: Identificando carreras ===")
        
        todas_carreras = Carrera.query.all()
        carreras_conservar_codigos = ['ING-SIS', 'ADM']  # Sistemas y Administración
        
        carreras_eliminar = []
        carreras_conservar = []
        
        for c in todas_carreras:
            if c.codigo in carreras_conservar_codigos:
                carreras_conservar.append(c)
                print(f"  ✓ Conservar: {c.nombre} ({c.codigo})")
            else:
                carreras_eliminar.append(c)
                print(f"  ✗ Eliminar: {c.nombre} ({c.codigo})")
        
        # =============================================
        # 2. ELIMINAR DATOS ASOCIADOS A CARRERAS QUE SE VAN
        # =============================================
        print("\n=== PASO 2: Eliminando datos de carreras a remover ===")
        
        for carrera in carreras_eliminar:
            carrera_id = carrera.id
            
            # Obtener materias de la carrera
            materias = Materia.query.filter_by(carrera_id=carrera_id).all()
            materia_ids = [m.id for m in materias]
            
            if materia_ids:
                # Eliminar asignaciones profesor-grupo de esas materias
                AsignacionProfesorGrupo.query.filter(
                    AsignacionProfesorGrupo.materia_id.in_(materia_ids)
                ).delete(synchronize_session=False)
                
                # Eliminar relaciones grupo_materias
                db.session.execute(
                    grupo_materias.delete().where(
                        grupo_materias.c.materia_id.in_(materia_ids)
                    )
                )
                
                # Eliminar relaciones profesor_materias  
                db.session.execute(
                    profesor_materias.delete().where(
                        profesor_materias.c.materia_id.in_(materia_ids)
                    )
                )
                
                # Eliminar las materias
                for m in materias:
                    db.session.delete(m)
                print(f"  Eliminadas {len(materias)} materias de {carrera.nombre}")
            
            # Eliminar grupos de la carrera
            grupos = Grupo.query.filter_by(carrera_id=carrera_id).all()
            for g in grupos:
                # Eliminar asignaciones del grupo
                AsignacionProfesorGrupo.query.filter_by(grupo_id=g.id).delete()
                db.session.delete(g)
            if grupos:
                print(f"  Eliminados {len(grupos)} grupos de {carrera.nombre}")
            
            # Eliminar la carrera
            db.session.delete(carrera)
            print(f"  Carrera '{carrera.nombre}' eliminada")
        
        db.session.commit()
        print("  Limpieza completada.")
        
        # =============================================
        # 3. AGREGAR NUEVAS CARRERAS
        # =============================================
        print("\n=== PASO 3: Agregando nuevas carreras ===")
        
        # Verificar si ya existen
        robotica = Carrera.query.filter_by(codigo='ROB').first()
        if not robotica:
            robotica = Carrera(
                nombre='Ingeniería en Robótica',
                codigo='ROB',
                descripcion='Carrera de ingeniería en robótica y automatización',
                facultad='Facultad de Ingeniería',
                creada_por=admin_id
            )
            db.session.add(robotica)
            print("  ✓ Carrera 'Ingeniería en Robótica' (ROB) creada")
        else:
            print("  → Carrera 'Robótica' ya existe")
        
        aduanas = Carrera.query.filter_by(codigo='ADU').first()
        if not aduanas:
            aduanas = Carrera(
                nombre='Comercio Internacional y Aduanas',
                codigo='ADU',
                descripcion='Carrera de comercio internacional y gestión aduanera',
                facultad='Facultad de Ciencias Económicas',
                creada_por=admin_id
            )
            db.session.add(aduanas)
            print("  ✓ Carrera 'Comercio Internacional y Aduanas' (ADU) creada")
        else:
            print("  → Carrera 'Aduanas' ya existe")
        
        db.session.commit()
        
        # Refrescar referencias
        ing_sis = Carrera.query.filter_by(codigo='ING-SIS').first()
        adm = Carrera.query.filter_by(codigo='ADM').first()
        robotica = Carrera.query.filter_by(codigo='ROB').first()
        aduanas = Carrera.query.filter_by(codigo='ADU').first()
        
        # =============================================
        # 4. AGREGAR MATERIAS
        # =============================================
        print("\n=== PASO 4: Agregando materias ===")
        
        def crear_materia(nombre, codigo, cuatri, carrera_id, creditos, horas, desc):
            """Helper para crear materia solo si no existe"""
            existente = Materia.query.filter_by(codigo=codigo).first()
            if not existente:
                m = Materia(nombre, codigo, cuatri, carrera_id, creditos, horas, desc, admin_id)
                db.session.add(m)
                return True
            return False
        
        # --- MATERIAS DE INGENIERÍA EN SISTEMAS ---
        materias_sistemas = [
            # Cuatrimestre 1
            ('Introducción a la Programación', 'SIS-101', 1, 4, 5, 'Fundamentos de programación'),
            ('Matemáticas Discretas', 'SIS-102', 1, 3, 4, 'Lógica y matemáticas para computación'),
            ('Fundamentos de TI', 'SIS-103', 1, 3, 3, 'Introducción a tecnologías de información'),
            ('Álgebra Lineal', 'SIS-104', 1, 4, 4, 'Vectores, matrices y sistemas lineales'),
            ('Comunicación Oral y Escrita', 'SIS-105', 1, 2, 3, 'Habilidades de comunicación'),
            # Cuatrimestre 2
            ('Programación Orientada a Objetos', 'SIS-201', 2, 4, 5, 'POO con Java'),
            ('Cálculo Diferencial', 'SIS-202', 2, 4, 4, 'Límites, derivadas, integrales'),
            ('Arquitectura de Computadoras', 'SIS-203', 2, 3, 4, 'Hardware y organización de sistemas'),
            ('Sistemas Operativos', 'SIS-204', 2, 3, 4, 'Gestión de procesos y memoria'),
            ('Inglés Técnico I', 'SIS-205', 2, 2, 3, 'Inglés para tecnología'),
            # Cuatrimestre 3
            ('Estructuras de Datos', 'SIS-301', 3, 4, 5, 'Listas, árboles, grafos'),
            ('Cálculo Integral', 'SIS-302', 3, 4, 4, 'Integrales y series'),
            ('Redes de Computadoras', 'SIS-303', 3, 3, 4, 'Protocolos y topologías de red'),
            ('Base de Datos I', 'SIS-304', 3, 4, 5, 'Diseño y SQL'),
            ('Inglés Técnico II', 'SIS-305', 3, 2, 3, 'Inglés intermedio para TI'),
            # Cuatrimestre 4
            ('Algoritmos Avanzados', 'SIS-401', 4, 4, 5, 'Complejidad y optimización'),
            ('Probabilidad y Estadística', 'SIS-402', 4, 3, 4, 'Estadística para ingeniería'),
            ('Base de Datos II', 'SIS-403', 4, 4, 5, 'NoSQL y optimización'),
            ('Desarrollo Web', 'SIS-404', 4, 4, 5, 'Frontend y backend web'),
            ('Metodologías Ágiles', 'SIS-405', 4, 3, 3, 'Scrum, Kanban, XP'),
            # Cuatrimestre 5
            ('Ingeniería de Software', 'SIS-501', 5, 4, 5, 'Ciclo de vida del software'),
            ('Inteligencia Artificial', 'SIS-502', 5, 4, 5, 'Fundamentos de IA'),
            ('Seguridad Informática', 'SIS-503', 5, 3, 4, 'Ciberseguridad'),
            ('Desarrollo Móvil', 'SIS-504', 5, 4, 5, 'Apps Android e iOS'),
            ('Gestión de Proyectos de TI', 'SIS-505', 5, 3, 3, 'PMI y gestión de proyectos'),
        ]
        
        count = 0
        if ing_sis:
            for nombre, codigo, cuatri, creditos, horas, desc in materias_sistemas:
                if crear_materia(nombre, codigo, cuatri, ing_sis.id, creditos, horas, desc):
                    count += 1
            print(f"  Sistemas: {count} materias nuevas creadas")
        
        # --- MATERIAS DE ADMINISTRACIÓN DE EMPRESAS ---
        materias_admin = [
            # Cuatrimestre 1
            ('Introducción a la Administración', 'ADM-101', 1, 3, 4, 'Teoría administrativa'),
            ('Contabilidad Básica', 'ADM-102', 1, 3, 4, 'Principios contables'),
            ('Matemáticas Financieras', 'ADM-103', 1, 4, 4, 'Interés, anualidades, amortización'),
            ('Microeconomía', 'ADM-104', 1, 3, 4, 'Oferta, demanda, mercados'),
            ('Comunicación Empresarial', 'ADM-105', 1, 2, 3, 'Comunicación organizacional'),
            # Cuatrimestre 2
            ('Macroeconomía', 'ADM-201', 2, 3, 4, 'Economía nacional e internacional'),
            ('Contabilidad de Costos', 'ADM-202', 2, 3, 4, 'Sistemas de costeo'),
            ('Derecho Empresarial', 'ADM-203', 2, 3, 3, 'Marco legal de empresas'),
            ('Estadística Empresarial', 'ADM-204', 2, 4, 4, 'Estadística aplicada'),
            ('Comportamiento Organizacional', 'ADM-205', 2, 3, 3, 'Cultura y clima organizacional'),
            # Cuatrimestre 3
            ('Gestión de Recursos Humanos', 'ADM-301', 3, 3, 4, 'Selección, capacitación, evaluación'),
            ('Marketing', 'ADM-302', 3, 3, 4, 'Mercadotecnia y ventas'),
            ('Finanzas Corporativas', 'ADM-303', 3, 4, 5, 'Inversión y financiamiento'),
            ('Logística y Cadena de Suministro', 'ADM-304', 3, 3, 4, 'Operaciones y logística'),
            ('Inglés de Negocios I', 'ADM-305', 3, 2, 3, 'Inglés para negocios'),
            # Cuatrimestre 4
            ('Planeación Estratégica', 'ADM-401', 4, 3, 4, 'Diseño de estrategias'),
            ('Investigación de Mercados', 'ADM-402', 4, 3, 4, 'Análisis de mercado'),
            ('Gestión de la Calidad', 'ADM-403', 4, 3, 4, 'ISO, Six Sigma'),
            ('Emprendimiento', 'ADM-404', 4, 3, 4, 'Creación de negocios'),
            ('Inglés de Negocios II', 'ADM-405', 4, 2, 3, 'Inglés avanzado'),
            # Cuatrimestre 5
            ('Liderazgo y Negociación', 'ADM-501', 5, 3, 3, 'Habilidades directivas'),
            ('Comercio Internacional', 'ADM-502', 5, 3, 4, 'Exportación e importación'),
            ('Gestión de Proyectos', 'ADM-503', 5, 3, 4, 'Planificación y ejecución'),
            ('Ética Empresarial', 'ADM-504', 5, 2, 3, 'Responsabilidad social'),
            ('Seminario de Titulación', 'ADM-505', 5, 4, 5, 'Proyecto final'),
        ]
        
        count = 0
        if adm:
            for nombre, codigo, cuatri, creditos, horas, desc in materias_admin:
                if crear_materia(nombre, codigo, cuatri, adm.id, creditos, horas, desc):
                    count += 1
            print(f"  Administración: {count} materias nuevas creadas")
        
        # --- MATERIAS DE ROBÓTICA ---
        materias_robotica = [
            # Cuatrimestre 1
            ('Fundamentos de Robótica', 'ROB-101', 1, 4, 5, 'Introducción a la robótica'),
            ('Física Mecánica', 'ROB-102', 1, 4, 5, 'Mecánica clásica para ingeniería'),
            ('Programación en C/C++', 'ROB-103', 1, 4, 5, 'Programación para sistemas embebidos'),
            ('Cálculo I', 'ROB-104', 1, 4, 4, 'Cálculo diferencial'),
            ('Dibujo Técnico y CAD', 'ROB-105', 1, 3, 4, 'Diseño asistido por computadora'),
            # Cuatrimestre 2
            ('Circuitos Eléctricos', 'ROB-201', 2, 4, 5, 'Análisis de circuitos'),
            ('Electrónica Analógica', 'ROB-202', 2, 4, 5, 'Componentes y circuitos analógicos'),
            ('Cálculo II', 'ROB-203', 2, 4, 4, 'Cálculo integral y vectorial'),
            ('Programación de Micros', 'ROB-204', 2, 4, 5, 'Arduino, PIC, ARM'),
            ('Álgebra Lineal Aplicada', 'ROB-205', 2, 3, 4, 'Transformaciones y matrices'),
            # Cuatrimestre 3
            ('Electrónica Digital', 'ROB-301', 3, 4, 5, 'Lógica digital y FPGAs'),
            ('Mecanismos y Máquinas', 'ROB-302', 3, 4, 5, 'Cinemática y dinámica'),
            ('Sensores y Actuadores', 'ROB-303', 3, 4, 5, 'Transductores para robótica'),
            ('Control Automático', 'ROB-304', 3, 4, 5, 'Teoría de control'),
            ('Ecuaciones Diferenciales', 'ROB-305', 3, 3, 4, 'EDO para ingeniería'),
            # Cuatrimestre 4
            ('Diseño Mecatrónico', 'ROB-401', 4, 4, 5, 'Integración mecánica-electrónica'),
            ('Visión por Computadora', 'ROB-402', 4, 4, 5, 'Procesamiento de imágenes'),
            ('Robótica Móvil', 'ROB-403', 4, 4, 5, 'Robots autónomos y navegación'),
            ('Inteligencia Artificial', 'ROB-404', 4, 4, 5, 'IA aplicada a robótica'),
            ('Manufactura y Materiales', 'ROB-405', 4, 3, 4, 'Impresión 3D, CNC, materiales'),
            # Cuatrimestre 5
            ('Robótica Industrial', 'ROB-501', 5, 4, 5, 'Brazos robóticos industriales'),
            ('Sistemas Embebidos Avanzados', 'ROB-502', 5, 4, 5, 'RTOS y SoC'),
            ('Drones y Vehículos Autónomos', 'ROB-503', 5, 4, 5, 'UAV y conducción autónoma'),
            ('IoT y Automatización', 'ROB-504', 5, 3, 4, 'Internet de las cosas'),
            ('Proyecto Integrador', 'ROB-505', 5, 5, 6, 'Proyecto final de robótica'),
        ]
        
        count = 0
        if robotica:
            for nombre, codigo, cuatri, creditos, horas, desc in materias_robotica:
                if crear_materia(nombre, codigo, cuatri, robotica.id, creditos, horas, desc):
                    count += 1
            print(f"  Robótica: {count} materias nuevas creadas")
        
        # --- MATERIAS DE ADUANAS ---
        materias_aduanas = [
            # Cuatrimestre 1
            ('Fundamentos de Comercio Ext.', 'ADU-101', 1, 3, 4, 'Introducción al comercio exterior'),
            ('Derecho Aduanero I', 'ADU-102', 1, 3, 4, 'Marco legal aduanero'),
            ('Economía Internacional', 'ADU-103', 1, 3, 4, 'Globalización y mercados'),
            ('Contabilidad General', 'ADU-104', 1, 3, 4, 'Fundamentos contables'),
            ('Inglés Comercial I', 'ADU-105', 1, 2, 3, 'Inglés para comercio'),
            # Cuatrimestre 2
            ('Clasificación Arancelaria', 'ADU-201', 2, 4, 5, 'Sistema armonizado'),
            ('Derecho Aduanero II', 'ADU-202', 2, 3, 4, 'Procedimientos aduaneros'),
            ('Logística Internacional', 'ADU-203', 2, 3, 4, 'Transporte y distribución'),
            ('Matemáticas Financieras', 'ADU-204', 2, 3, 4, 'Costos y financiamiento'),
            ('Inglés Comercial II', 'ADU-205', 2, 2, 3, 'Inglés intermedio'),
            # Cuatrimestre 3
            ('Operaciones Aduaneras', 'ADU-301', 3, 4, 5, 'Despacho aduanero'),
            ('Tratados de Libre Comercio', 'ADU-302', 3, 3, 4, 'TMEC, acuerdos comerciales'),
            ('Seguros y Fianzas', 'ADU-303', 3, 3, 4, 'Gestión de riesgos'),
            ('Informática Aduanera', 'ADU-304', 3, 3, 4, 'Sistemas electrónicos aduaneros'),
            ('Francés Comercial', 'ADU-305', 3, 2, 3, 'Francés para negocios'),
            # Cuatrimestre 4
            ('Auditoría Aduanera', 'ADU-401', 4, 3, 4, 'Revisión y cumplimiento'),
            ('Comercio Electrónico', 'ADU-402', 4, 3, 4, 'E-commerce internacional'),
            ('Negociación Internacional', 'ADU-403', 4, 3, 4, 'Técnicas de negociación'),
            ('Envase Embalaje y Transporte', 'ADU-404', 4, 3, 4, 'Logística de mercancías'),
            ('Régimen Fiscal del Comercio', 'ADU-405', 4, 3, 4, 'Impuestos en comercio ext.'),
            # Cuatrimestre 5
            ('Agencia Aduanal', 'ADU-501', 5, 4, 5, 'Operación de agencia'),
            ('Gestión de Calidad Aduanera', 'ADU-502', 5, 3, 4, 'Certificaciones y normas'),
            ('Comercio con Asia-Pacífico', 'ADU-503', 5, 3, 4, 'Mercados emergentes'),
            ('Proyecto de Importación', 'ADU-504', 5, 4, 5, 'Proyecto integrador'),
            ('Ética y Responsabilidad', 'ADU-505', 5, 2, 3, 'Ética profesional'),
        ]
        
        count = 0
        if aduanas:
            for nombre, codigo, cuatri, creditos, horas, desc in materias_aduanas:
                if crear_materia(nombre, codigo, cuatri, aduanas.id, creditos, horas, desc):
                    count += 1
            print(f"  Aduanas: {count} materias nuevas creadas")
        
        db.session.commit()
        
        # =============================================
        # 5. AGREGAR PROFESORES
        # =============================================
        print("\n=== PASO 5: Agregando profesores ===")
        
        profesores_data = [
            # Sistemas
            ('jlopez', 'jlopez@uni.edu', 'Prof123!', 'Juan Carlos', 'López Ramírez', 'profesor_completo', [ing_sis]),
            ('mgarcia', 'mgarcia@uni.edu', 'Prof123!', 'María Elena', 'García Torres', 'profesor_completo', [ing_sis]),
            ('rcastillo', 'rcastillo@uni.edu', 'Prof123!', 'Roberto', 'Castillo Vega', 'profesor_asignatura', [ing_sis]),
            ('ahernandez', 'ahernandez@uni.edu', 'Prof123!', 'Ana Lucía', 'Hernández Díaz', 'profesor_completo', [ing_sis]),
            ('fmendoza', 'fmendoza@uni.edu', 'Prof123!', 'Fernando', 'Mendoza Silva', 'profesor_asignatura', [ing_sis]),
            # Administración
            ('prios', 'prios@uni.edu', 'Prof123!', 'Patricia', 'Ríos Morales', 'profesor_completo', [adm]),
            ('cnarvaez', 'cnarvaez@uni.edu', 'Prof123!', 'Carlos', 'Narváez Fuentes', 'profesor_completo', [adm]),
            ('lgomez', 'lgomez@uni.edu', 'Prof123!', 'Laura', 'Gómez Aguilar', 'profesor_asignatura', [adm]),
            ('dortega', 'dortega@uni.edu', 'Prof123!', 'Diego', 'Ortega Paredes', 'profesor_completo', [adm]),
            ('smolinaa', 'smolinaa@uni.edu', 'Prof123!', 'Sandra', 'Molina Arellano', 'profesor_asignatura', [adm]),
            # Robótica
            ('evargas', 'evargas@uni.edu', 'Prof123!', 'Eduardo', 'Vargas Rojas', 'profesor_completo', [robotica]),
            ('irodriguez', 'irodriguez@uni.edu', 'Prof123!', 'Ivana', 'Rodríguez Luna', 'profesor_completo', [robotica]),
            ('omedina', 'omedina@uni.edu', 'Prof123!', 'Óscar', 'Medina Contreras', 'profesor_asignatura', [robotica]),
            ('nfigueroa', 'nfigueroa@uni.edu', 'Prof123!', 'Natalia', 'Figueroa Peña', 'profesor_completo', [robotica]),
            ('gsalazar', 'gsalazar@uni.edu', 'Prof123!', 'Gerardo', 'Salazar Ibarra', 'profesor_asignatura', [robotica]),
            # Aduanas
            ('vcervantes', 'vcervantes@uni.edu', 'Prof123!', 'Verónica', 'Cervantes Lara', 'profesor_completo', [aduanas]),
            ('jnavarro', 'jnavarro@uni.edu', 'Prof123!', 'Javier', 'Navarro Escobar', 'profesor_completo', [aduanas]),
            ('mmontes', 'mmontes@uni.edu', 'Prof123!', 'Mónica', 'Montes Guerrero', 'profesor_asignatura', [aduanas]),
            ('racosta', 'racosta@uni.edu', 'Prof123!', 'Rafael', 'Acosta Sandoval', 'profesor_completo', [aduanas]),
            ('tdelgado', 'tdelgado@uni.edu', 'Prof123!', 'Teresa', 'Delgado Olvera', 'profesor_asignatura', [aduanas]),
            # Jefes de carrera
            ('jefe_sis', 'jefe.sis@uni.edu', 'Jefe123!', 'Andrés', 'Villanueva Cruz', 'jefe_carrera', [ing_sis]),
            ('jefe_adm', 'jefe.adm@uni.edu', 'Jefe123!', 'Beatriz', 'Espinoza Reyes', 'jefe_carrera', [adm]),
            ('jefe_rob', 'jefe.rob@uni.edu', 'Jefe123!', 'Héctor', 'Aguirre Domínguez', 'jefe_carrera', [robotica]),
            ('jefe_adu', 'jefe.adu@uni.edu', 'Jefe123!', 'Claudia', 'Soto Bermúdez', 'jefe_carrera', [aduanas]),
        ]
        
        count_new = 0
        for username, email, pwd, nombre, apellido, rol, carreras_list in profesores_data:
            existente = User.query.filter_by(username=username).first()
            if not existente:
                u = User(
                    username=username,
                    email=email,
                    password=pwd,
                    nombre=nombre,
                    apellido=apellido,
                    rol=rol,
                    carreras=carreras_list
                )
                # Para jefes de carrera, asignar carrera_id
                if rol == 'jefe_carrera' and carreras_list:
                    u.carrera_id = carreras_list[0].id
                db.session.add(u)
                db.session.flush()
                # Sincronizar rol con tabla de roles
                u.sync_legacy_role()
                count_new += 1
            else:
                print(f"  → Profesor '{username}' ya existe, omitiendo")
        
        db.session.commit()
        print(f"  {count_new} profesores nuevos creados")
        
        # =============================================
        # 6. AGREGAR GRUPOS (SIN ASIGNAR MATERIAS)
        # =============================================
        print("\n=== PASO 6: Agregando grupos (sin materias asignadas) ===")
        
        grupos_data = [
            # Sistemas - Cuatrimestres 1-5, Matutino y Vespertino
            (1, 'M', ing_sis.id, 1), (1, 'V', ing_sis.id, 1),
            (1, 'M', ing_sis.id, 2), (1, 'V', ing_sis.id, 2),
            (1, 'M', ing_sis.id, 3), (1, 'V', ing_sis.id, 3),
            (1, 'M', ing_sis.id, 4),
            (1, 'M', ing_sis.id, 5),
            # Administración
            (1, 'M', adm.id, 1), (1, 'V', adm.id, 1),
            (1, 'M', adm.id, 2), (1, 'V', adm.id, 2),
            (1, 'M', adm.id, 3),
            (1, 'M', adm.id, 4),
            (1, 'M', adm.id, 5),
            # Robótica
            (1, 'M', robotica.id, 1), (1, 'V', robotica.id, 1),
            (1, 'M', robotica.id, 2),
            (1, 'M', robotica.id, 3),
            (1, 'M', robotica.id, 4),
            (1, 'M', robotica.id, 5),
            # Aduanas
            (1, 'M', aduanas.id, 1), (1, 'V', aduanas.id, 1),
            (1, 'M', aduanas.id, 2),
            (1, 'M', aduanas.id, 3),
            (1, 'M', aduanas.id, 4),
            (1, 'M', aduanas.id, 5),
        ]
        
        count_grupos = 0
        for num, turno, carrera_id, cuatri in grupos_data:
            # Generar código para verificar si existe
            carrera = Carrera.query.get(carrera_id)
            codigo_esperado = f"{cuatri}{turno}{carrera.codigo}{num}"
            
            existente = Grupo.query.filter_by(codigo=codigo_esperado).first()
            if not existente:
                g = Grupo(
                    numero_grupo=num,
                    turno=turno,
                    carrera_id=carrera_id,
                    cuatrimestre=cuatri,
                    creado_por=admin_id
                )
                db.session.add(g)
                count_grupos += 1
        
        db.session.commit()
        print(f"  {count_grupos} grupos nuevos creados (SIN materias asignadas)")
        
        # =============================================
        # RESUMEN FINAL
        # =============================================
        print("\n" + "=" * 50)
        print("RESUMEN FINAL")
        print("=" * 50)
        print(f"  Carreras: {Carrera.query.count()}")
        for c in Carrera.query.all():
            materias_count = Materia.query.filter_by(carrera_id=c.id).count()
            grupos_count = Grupo.query.filter_by(carrera_id=c.id).count()
            print(f"    • {c.nombre} ({c.codigo}): {materias_count} materias, {grupos_count} grupos")
        print(f"  Profesores: {User.query.filter(User.rol.in_(['profesor_completo', 'profesor_asignatura'])).count()}")
        print(f"  Jefes de carrera: {User.query.filter_by(rol='jefe_carrera').count()}")
        print(f"  Grupos totales: {Grupo.query.count()}")
        print(f"  Materias totales: {Materia.query.count()}")
        print("\n  ⚠️ Las materias NO fueron asignadas a los grupos.")
        print("  Asígnalas manualmente desde la interfaz de administración.")
        print("\n✅ Base de datos poblada exitosamente!")


if __name__ == '__main__':
    print("=" * 50)
    print("SCRIPT DE POBLACIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    resp = input("\n¿Deseas continuar? Esto eliminará carreras no deseadas. (s/n): ")
    if resp.lower() == 's':
        limpiar_y_poblar()
    else:
        print("Operación cancelada.")
