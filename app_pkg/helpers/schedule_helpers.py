"""
Schedule processing helpers.

Contains functions for processing and organizing academic schedule data.
Extracted from app.py lines 365-565.
"""
import re
from datetime import datetime
from markupsafe import escape


def procesar_horarios(agrupar_por='profesor', carrera_id=None, incluir_ids=False):
    """
    Función centralizada para obtener y procesar los horarios académicos.

    :param agrupar_por: 'profesor' o 'grupo'. Define cómo se agruparán los datos.
    :param carrera_id: Opcional. Si se provee un ID, filtra los horarios para esa carrera.
    :param incluir_ids: Si True, incluye los IDs de los horarios para acciones
    :return: Un diccionario con los horarios organizados.
    """
    from models import HorarioAcademico, Materia, Grupo

    # 1. Consulta base a la base de datos
    query = HorarioAcademico.query.filter_by(activo=True)

    # 2. Si se especifica una carrera_id, filtramos los resultados
    if carrera_id:
        query = query.join(Materia).filter(Materia.carrera_id == carrera_id)

    asignaciones = query.all()

    # 3. Ordenamos los resultados en Python
    asignaciones.sort(key=lambda h: (h.get_dia_orden(), h.horario.hora_inicio))

    # 4. Diccionario para almacenar el resultado final
    datos_organizados = {}

    # Mapeo de días para asegurar formato correcto
    dias_map = {
        'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miércoles',
        'jueves': 'Jueves', 'viernes': 'Viernes'
    }

    # 5. Iteramos sobre cada asignación para construir el diccionario
    for a in asignaciones:
        if not all([a.profesor, a.materia, a.horario]):
            continue

        clave_agrupacion = None
        info_clase_html = ""

        # Lógica para agrupar por PROFESOR
        if agrupar_por == 'profesor':
            clave_agrupacion = a.profesor.get_nombre_completo()
            # Obtener código del grupo para mostrar junto con la materia
            grupo_codigo = a.grupo if a.grupo else ""
            # Obtener la hora de inicio como entero para la cuadrícula
            hora_inicio_int = a.horario.hora_inicio.hour if a.horario.hora_inicio else 7

            if incluir_ids:
                info_clase_html = {
                    'id': a.id,
                    'html': f"{escape(a.materia.nombre)}<br><small class='text-muted'>{escape(a.materia.codigo)}</small><br>{a.get_hora_inicio_str()} - {a.get_hora_fin_str()}",
                    'grupo': grupo_codigo,
                    'hora_inicio': hora_inicio_int,
                    'hora_texto': f"{a.get_hora_inicio_str()} - {a.get_hora_fin_str()}"
                }
            else:
                info_clase_html = (
                    f"{escape(a.materia.nombre)}<br>"
                    f"<small class='text-muted'>{escape(a.materia.codigo)}</small><br>"
                    f"<span class='badge bg-primary bg-opacity-25 text-primary' style='font-size:0.65rem;'>Grupo: {escape(grupo_codigo)}</span><br>"
                    f"{a.get_hora_inicio_str()} - {a.get_hora_fin_str()}"
                )

        # Lógica para agrupar por GRUPO
        elif agrupar_por == 'grupo':
            # CORREGIDO: Usar el campo 'grupo' del HorarioAcademico en lugar de materia.grupos
            grupo_codigo = a.grupo

            if grupo_codigo:
                # Buscar el objeto Grupo por su código para filtrar por carrera si es necesario
                grupo = Grupo.query.filter_by(codigo=grupo_codigo).first()

                if grupo and (carrera_id is None or grupo.carrera_id == carrera_id):
                    clave_agrupacion = grupo_codigo
                    # Obtener la hora de inicio como entero para la cuadrícula
                    hora_inicio_int = a.horario.hora_inicio.hour if a.horario.hora_inicio else 7
                    if incluir_ids:
                        info_clase_html = {
                            'id': a.id,
                            'grupo_id': grupo.id,
                            'hora_inicio': hora_inicio_int,
                            'materia': a.materia.nombre,
                            'profesor': a.profesor.get_nombre_completo(),
                            'hora_texto': f"{a.get_hora_inicio_str()} - {a.get_hora_fin_str()}",
                            'html': f"{escape(a.materia.nombre)}<br>Prof: {escape(a.profesor.get_nombre_completo())}<br>{a.get_hora_inicio_str()} - {a.get_hora_fin_str()}"
                        }
                    else:
                        info_clase_html = (
                            f"{escape(a.materia.nombre)}<br>"
                            f"Prof: {escape(a.profesor.get_nombre_completo())}<br>"
                            f"{a.get_hora_inicio_str()} - {a.get_hora_fin_str()}"
                        )

        # Si encontramos una clave válida, la agregamos al diccionario
        if clave_agrupacion:
            if clave_agrupacion not in datos_organizados:
                datos_organizados[clave_agrupacion] = {d: [] for d in dias_map.values()}

            dia_correcto = dias_map.get(a.dia_semana.lower())
            if dia_correcto:
                datos_organizados[clave_agrupacion][dia_correcto].append(info_clase_html)

    # 6. Ordenamos el diccionario final si es por grupo para una mejor presentación
    if agrupar_por == 'grupo':
        def natural_keys(text):
            return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]

        datos_ordenados = {k: datos_organizados[k] for k in sorted(datos_organizados.keys(), key=natural_keys)}
        return datos_ordenados

    return datos_organizados


def procesar_horarios_formato_fda(carrera_id=None):
    """
    Obtiene los datos de horarios con todos los detalles necesarios
    para generar el formato de Carga Horaria (FDA).
    """
    from models import HorarioAcademico, Materia

    query = HorarioAcademico.query.filter_by(activo=True)

    if carrera_id:
        query = query.join(Materia).filter(Materia.carrera_id == carrera_id)

    asignaciones = query.all()

    horarios_por_profesor = {}

    dias_map = {'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miércoles', 'jueves': 'Jueves', 'viernes': 'Viernes', 'sabado': 'Sábado'}

    for a in asignaciones:
        if not all([a.profesor, a.materia, a.horario, a.materia.carrera]):
            continue

        profesor_nombre = a.profesor.get_nombre_completo()

        if profesor_nombre not in horarios_por_profesor:
            info_profesor = {
                'id': a.profesor.id,
                'nombre_completo': a.profesor.get_nombre_completo(),
                'es_tc': getattr(a.profesor, 'rol', '') == 'profesor_completo'
            }
            horarios_por_profesor[profesor_nombre] = {
                'info': info_profesor,
                'clases': []
            }

        duracion_horas = (a.horario.hora_fin.hour - a.horario.hora_inicio.hour) + (a.horario.hora_fin.minute - a.horario.hora_inicio.minute) / 60.0

        # CORREGIDO: Usar el campo 'grupo' del HorarioAcademico directamente
        grupo_codigo = a.grupo if a.grupo else "N/A"

        dia_correcto = dias_map.get(a.dia_semana.lower())
        if not dia_correcto:
            continue

        detalle_clase = {
            'clave': a.materia.codigo, 'asignatura': a.materia.nombre, 'grupo': grupo_codigo,
            'dia_raw': a.dia_semana.lower(), 'hora_inicio': a.get_hora_inicio_str(),
            'hora_fin': a.get_hora_fin_str(), 'horas_totales': duracion_horas,
            'carrera': a.materia.carrera.codigo
        }
        horarios_por_profesor[profesor_nombre]['clases'].append(detalle_clase)

    for data in horarios_por_profesor.values():
        data['clases'].sort(key=lambda c: (['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'].index(c['dia_raw']), c['hora_inicio']))

    return horarios_por_profesor


def obtener_periodo_actual():
    """
    Calcula el periodo académico automáticamente basado en el mes actual.

    Periodos:
    - Enero-Abril: Meses 1-4 → "ENERO - ABRIL"
    - Mayo-Agosto: Meses 5-8 → "MAYO - AGOSTO"
    - Septiembre-Diciembre: Meses 9-12 → "SEPTIEMBRE - DICIEMBRE"

    Returns:
        tuple: (periodo_texto, año_texto)
    """
    ahora = datetime.now()
    mes = ahora.month
    año = ahora.year

    if 1 <= mes <= 4:
        return "ENERO - ABRIL", str(año)
    elif 5 <= mes <= 8:
        return "MAYO - AGOSTO", str(año)
    else:  # 9 <= mes <= 12
        return "SEPTIEMBRE - DICIEMBRE", f"{año} - {año + 1}"
