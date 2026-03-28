"""
GENERADOR DE HORARIOS MEJORADO - Versión con Estrategia por Etapas

Este generador soluciona los problemas de la generación masiva:
1. Valida disponibilidad REAL antes de intentar generar
2. Genera por etapas (turno por turno) para reducir complejidad
3. Selecciona UN profesor por materia-grupo (no todos los asignados)
4. Proporciona diagnóstico claro de por qué falla
"""

from models import (
    db,
    User,
    Horario,
    Carrera,
    Materia,
    HorarioAcademico,
    Grupo,
    AsignacionProfesorGrupo,
    DisponibilidadProfesor,
)
from datetime import datetime
from collections import defaultdict
import math
import random
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from ortools.sat.python import cp_model

    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    cp_model = None


class DiagnosticoGeneracion:
    """Clase para diagnosticar problemas antes de generar"""

    def __init__(self, grupos_ids, dias_semana=None):
        self.grupos_ids = grupos_ids
        self.dias_semana = dias_semana or [
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
        ]
        self.grupos = []
        self.problemas = []
        self.advertencias = []

    def ejecutar_diagnostico(self):
        """Ejecutar diagnóstico completo"""
        print("🔍 Ejecutando diagnóstico de factibilidad...")

        # Cargar grupos
        for gid in self.grupos_ids:
            grupo = Grupo.query.get(gid)
            if grupo:
                self.grupos.append(grupo)

        if not self.grupos:
            self.problemas.append("No se encontraron grupos válidos")
            return False

        # Diagnósticos
        self._verificar_materias()
        self._verificar_asignaciones()
        self._verificar_disponibilidad_por_turno()
        self._verificar_conflictos_horarios()

        return len(self.problemas) == 0

    def _verificar_materias(self):
        """Verificar que todos los grupos tengan materias"""
        for grupo in self.grupos:
            materias = [m for m in grupo.materias if m.activa]
            if not materias:
                self.problemas.append(
                    f"Grupo {grupo.codigo} no tiene materias asignadas"
                )

    def _verificar_asignaciones(self):
        """Verificar asignaciones profesor-materia-grupo"""
        for grupo in self.grupos:
            materias = [m for m in grupo.materias if m.activa]

            for materia in materias:
                # Buscar TODAS las asignaciones específicas (puede haber múltiples)
                asignaciones = AsignacionProfesorGrupo.query.filter_by(
                    grupo_id=grupo.id, materia_id=materia.id, activo=True
                ).all()

                if not asignaciones:
                    # Verificar relación M2M
                    profesores = [p for p in materia.profesores if p.activo]
                    if not profesores:
                        self.problemas.append(
                            f"Materia '{materia.nombre}' en grupo {grupo.codigo} no tiene profesor asignado"
                        )
                    else:
                        self.advertencias.append(
                            f"Materia '{materia.nombre}' en grupo {grupo.codigo} usa asignación genérica (M2M)"
                        )
                elif len(asignaciones) > 1:
                    # Múltiples profesores asignados - el sistema elegirá el mejor
                    nombres = ", ".join([a.profesor.nombre for a in asignaciones if a.profesor])
                    self.advertencias.append(
                        f"Materia '{materia.nombre}' en grupo {grupo.codigo} tiene {len(asignaciones)} profesores asignados ({nombres}). Se elegirá el de mejor disponibilidad."
                    )

    def _verificar_disponibilidad_por_turno(self):
        """Verificar disponibilidad vs requerimientos por turno"""

        grupos_matutino = [g for g in self.grupos if g.turno == "M"]
        grupos_vespertino = [g for g in self.grupos if g.turno == "V"]

        for turno, grupos_turno, nombre_turno in [
            ("matutino", grupos_matutino, "MATUTINO"),
            ("vespertino", grupos_vespertino, "VESPERTINO"),
        ]:
            if not grupos_turno:
                continue

            # Calcular horas requeridas
            horas_requeridas = 0
            for grupo in grupos_turno:
                for materia in grupo.materias:
                    if materia.activa:
                        horas_requeridas += materia.horas_semanales or 3

            # Calcular disponibilidad
            profesores_turno = set()
            for grupo in grupos_turno:
                asigs = AsignacionProfesorGrupo.query.filter_by(
                    grupo_id=grupo.id, activo=True
                ).all()
                for asig in asigs:
                    if asig.profesor:
                        profesores_turno.add(asig.profesor_id)

            horarios_turno = Horario.query.filter_by(turno=turno, activo=True).all()

            # Contar slots disponibles
            slots_disponibles = 0
            for profesor_id in profesores_turno:
                for horario in horarios_turno:
                    for dia in self.dias_semana:
                        disp = DisponibilidadProfesor.query.filter_by(
                            profesor_id=profesor_id,
                            horario_id=horario.id,
                            dia_semana=dia,
                            activo=True,
                            disponible=True,
                        ).first()
                        if disp:
                            slots_disponibles += 1

            # Comparar
            if horas_requeridas > slots_disponibles:
                deficit = horas_requeridas - slots_disponibles
                self.problemas.append(
                    f"Turno {nombre_turno}: Se requieren {horas_requeridas} horas "
                    f"pero solo hay {slots_disponibles} slots disponibles (déficit: {deficit})"
                )

    def _verificar_conflictos_horarios(self):
        """Verificar conflictos específicos de horarios"""
        # Verificar que cada grupo del mismo turno pueda tener su horario completo
        pass  # Implementación simplificada

    def get_reporte(self):
        """Obtener reporte del diagnóstico"""
        return {
            "factible": len(self.problemas) == 0,
            "problemas": self.problemas,
            "advertencias": self.advertencias,
            "grupos_analizados": len(self.grupos),
        }


class GeneradorHorariosMejorado:
    """
    Generador de horarios mejorado con:
    - Selección inteligente de profesor (uno por materia-grupo)
    - Generación por etapas
    - Mejor manejo de restricciones
    """

    def __init__(
        self,
        grupos_ids,
        periodo_academico="2025-1",
        version_nombre=None,
        creado_por=None,
        dias_semana=None,
        tiempo_limite=60,  # OPTIMIZADO: Reducido de 300s a 60s
    ):
        if not ORTOOLS_AVAILABLE:
            raise ImportError("OR-Tools no está disponible")

        self.grupos_ids = grupos_ids
        self.periodo_academico = periodo_academico
        self.version_nombre = version_nombre
        
        # Si no se proporciona creado_por, buscar un administrador del sistema
        if creado_por is None:
            admin = User.query.filter(User.roles.any(nombre='admin')).first()
            if admin:
                self.creado_por = admin.id
            else:
                # Fallback al primer usuario si no hay admin
                user = User.query.first()
                self.creado_por = user.id if user else 1
        else:
            self.creado_por = creado_por
            
        self.dias_semana = dias_semana or [
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
        ]
        self.tiempo_limite = tiempo_limite

        self.grupos = []
        self.materias_por_grupo = {}
        self.profesor_por_materia_grupo = {}  # (grupo_id, materia_id) -> profesor_id (UNO solo)
        self.horarios_por_turno = {}
        self.disponibilidades = {}
        
        # OPTIMIZACIÓN: Cachés para evitar consultas repetidas
        self._cache_horarios_existentes = {}  # profesor_id -> [(horario_id, dia_semana)]
        self._cache_capacidad_profesor = {}  # (profesor_id, turno) -> capacidad

        self._materias_sin_profesor = []  # Materias omitidas por falta de profesor
        self._profesores_asignacion_directa = set()  # IDs de profesores con AsignacionProfesorGrupo

        self.model = None
        self.solver = None
        self.variables = {}

        self.horarios_generados = []
        self.estadisticas = {}

    def cargar_grupos(self):
        """Cargar y validar grupos"""
        print("📂 Cargando grupos...")

        for gid in self.grupos_ids:
            grupo = Grupo.query.get(gid)
            if grupo and grupo.activo:
                self.grupos.append(grupo)
                print(
                    f"   ✓ {grupo.codigo} ({grupo.get_carrera_nombre()}, {grupo.get_turno_display()})"
                )

        if not self.grupos:
            raise ValueError("No se encontraron grupos válidos")

        return len(self.grupos)

    def seleccionar_profesores(self):
        """
        CRÍTICO: Seleccionar UN profesor por cada materia-grupo.
        Esto evita el problema de múltiples asignaciones.

        MEJORADO: Ahora verifica que el profesor tenga suficiente disponibilidad
        para las horas requeridas de la materia, y tiene fallback inteligente.
        """
        print("👨‍🏫 Seleccionando profesores...")
        logger.info(f"Seleccionando profesores para {len(self.grupos)} grupos")

        materias_sin_profesor = []
        materias_con_advertencia = []

        for grupo in self.grupos:
            materias = [m for m in grupo.materias if m.activa]
            self.materias_por_grupo[grupo.id] = materias
            turno_str = "matutino" if grupo.turno == "M" else "vespertino"

            for materia in materias:
                horas_requeridas = materia.horas_semanales or 3

                # Buscar TODAS las asignaciones específicas (puede haber múltiples profesores asignados)
                asignaciones = AsignacionProfesorGrupo.query.filter_by(
                    grupo_id=grupo.id, materia_id=materia.id, activo=True
                ).all()

                profesor_seleccionado = None
                disponibilidad_seleccionada = 0
                usar_fallback = False

                # PRIORIDAD 1: Buscar entre TODOS los profesores asignados específicamente
                if asignaciones:
                    # Obtener profesores activos de las asignaciones
                    profesores_asignados = [
                        a.profesor for a in asignaciones
                        if a.profesor and a.profesor.activo
                    ]

                    if profesores_asignados:
                        # Evaluar disponibilidad de cada profesor asignado
                        candidatos_asignados = []
                        for profesor in profesores_asignados:
                            disp_count = self._contar_capacidad_restante(profesor.id, turno_str)
                            candidatos_asignados.append((profesor, disp_count))

                        # Ordenar por disponibilidad (mayor primero)
                        candidatos_asignados.sort(key=lambda x: x[1], reverse=True)

                        # Seleccionar el mejor profesor asignado con suficiente disponibilidad
                        for profesor, disp in candidatos_asignados:
                            if disp >= horas_requeridas:
                                profesor_seleccionado = profesor
                                disponibilidad_seleccionada = disp
                                break

                        # Si ninguno tiene suficiente, usar el de mayor disponibilidad
                        # Para asignaciones directas, SIEMPRE usar el profesor asignado
                        # (la asignación explícita tiene prioridad sobre la disponibilidad)
                        if not profesor_seleccionado:
                            mejor_candidato = candidatos_asignados[0]
                            profesor_seleccionado = mejor_candidato[0]
                            disponibilidad_seleccionada = mejor_candidato[1]
                            if disponibilidad_seleccionada > 0:
                                msg = (f"{grupo.codigo}/{materia.codigo}: Prof. asignado {profesor_seleccionado.nombre} "
                                       f"tiene {disponibilidad_seleccionada}h disponibles (Requeridas: {horas_requeridas}h). "
                                       "Se usará de todos modos.")
                            else:
                                # Profesor asignado sin disponibilidad registrada en este turno
                                # Se asumirá disponibilidad completa (la asignación explícita lo autoriza)
                                msg = (f"{grupo.codigo}/{materia.codigo}: Prof. asignado {profesor_seleccionado.nombre} "
                                       f"sin disponibilidad en turno {turno_str}. "
                                       "Se asumirá disponibilidad completa por asignación directa.")
                            materias_con_advertencia.append(msg)
                            logger.warning(msg)

                        # Marcar como asignación directa para override de disponibilidad
                        if profesor_seleccionado:
                            self._profesores_asignacion_directa.add(profesor_seleccionado.id)

                # PRIORIDAD 2: Fallback a relación M2M si no hay asignación específica o ningún asignado tiene disponibilidad
                if profesor_seleccionado is None:
                    profesores = [p for p in materia.profesores if p.activo]

                    if profesores:
                        # Ordenar por disponibilidad y seleccionar el mejor
                        candidatos = []
                        for profesor in profesores:
                            disp_count = self._contar_capacidad_restante(profesor.id, turno_str)
                            candidatos.append((profesor, disp_count))

                        candidatos.sort(key=lambda x: x[1], reverse=True)

                        for profesor, disp in candidatos:
                            if disp >= horas_requeridas:
                                profesor_seleccionado = profesor
                                disponibilidad_seleccionada = disp
                                if usar_fallback:
                                    logger.info(f"  Usando profesor alternativo: {profesor.nombre}")
                                break

                        # Si ninguno cumple completamente, usar el de mayor disponibilidad
                        if not profesor_seleccionado and candidatos and candidatos[0][1] > 0:
                            profesor_seleccionado, disponibilidad_seleccionada = candidatos[0]
                            msg = (f"{grupo.codigo}/{materia.codigo}: Prof. {profesor_seleccionado.nombre} "
                                   f"tiene {disponibilidad_seleccionada}h disponibles (Requeridas: {horas_requeridas}h). "
                                   "Se intentará completar, pero podría fallar.")
                            materias_con_advertencia.append(msg)
                            logger.warning(msg)

                if profesor_seleccionado:
                    self.profesor_por_materia_grupo[(grupo.id, materia.id)] = profesor_seleccionado

                    if disponibilidad_seleccionada >= horas_requeridas:
                        print(
                            f"   ✓ {grupo.codigo}/{materia.codigo}: {profesor_seleccionado.nombre} {profesor_seleccionado.apellido} ({disponibilidad_seleccionada}h disp.)"
                        )
                    else:
                        print(
                            f"   ⚠️ {grupo.codigo}/{materia.codigo}: {profesor_seleccionado.nombre} {profesor_seleccionado.apellido} ({disponibilidad_seleccionada}h disp. < {horas_requeridas}h req.)"
                        )
                else:
                    msg = f"{grupo.codigo}/{materia.codigo} ({materia.nombre})"
                    materias_sin_profesor.append(msg)
                    logger.error(f"SIN PROFESOR DISPONIBLE: {msg}")
                    print(
                        f"   ❌ {grupo.codigo}/{materia.codigo}: SIN PROFESOR DISPONIBLE"
                    )

        # Mostrar advertencias
        if materias_con_advertencia:
            print(f"\n   ⚠️ ADVERTENCIAS de disponibilidad:")
            for adv in materias_con_advertencia:
                print(f"      - {adv}")

        # Materias sin profesor: remover del grupo en lugar de fallar todo
        if materias_sin_profesor:
            logger.warning(f"Materias sin profesor asignado: {len(materias_sin_profesor)}")
            print(f"\n   ⚠️ Se omitirán {len(materias_sin_profesor)} materias sin profesor asignado")
            self._materias_sin_profesor = materias_sin_profesor

            # Remover materias sin profesor de materias_por_grupo para que no se intenten agendar
            for grupo in self.grupos:
                materias_originales = self.materias_por_grupo.get(grupo.id, [])
                self.materias_por_grupo[grupo.id] = [
                    m for m in materias_originales
                    if (grupo.id, m.id) in self.profesor_por_materia_grupo
                ]
                removidas = len(materias_originales) - len(self.materias_por_grupo[grupo.id])
                if removidas:
                    print(f"      {grupo.codigo}: {removidas} materias omitidas, {len(self.materias_por_grupo[grupo.id])} restantes")

            # Si un grupo se queda sin materias, fallar
            for grupo in self.grupos:
                if not self.materias_por_grupo.get(grupo.id):
                    raise ValueError(
                        f"Grupo {grupo.codigo}: Todas las materias carecen de profesor asignado.\n   - "
                        + "\n   - ".join(m for m in materias_sin_profesor if m.startswith(grupo.codigo))
                    )

        # Invalidar caché de capacidad para profesores con asignación directa
        # (la capacidad se recalculará con el override de disponibilidad completa)
        for prof_id in self._profesores_asignacion_directa:
            keys_to_remove = [k for k in self._cache_capacidad_profesor if k[0] == prof_id]
            for k in keys_to_remove:
                del self._cache_capacidad_profesor[k]

    def _contar_capacidad_restante(self, profesor_id, turno):
        """
        Calcula la capacidad REAL restante de un profesor en un turno.
        Capacidad = (Slots Disponibles) - (Slots Ocupados en otros grupos)

        IMPORTANTE: Si el profesor NO tiene disponibilidad explícita registrada,
        se asume disponibilidad COMPLETA en todos los horarios del turno.
        Esto permite que profesores sin disponibilidad registrada sean considerados.

        OPTIMIZADO: Usa caché para evitar consultas repetidas
        """
        # Verificar caché primero
        cache_key = (profesor_id, turno)
        if cache_key in self._cache_capacidad_profesor:
            return self._cache_capacidad_profesor[cache_key]

        # 1. Obtener horarios del turno (usar caché del objeto si existe)
        if turno not in self.horarios_por_turno:
            horarios_turno = Horario.query.filter_by(turno=turno, activo=True).all()
            self.horarios_por_turno[turno] = horarios_turno
        else:
            horarios_turno = self.horarios_por_turno.get(turno, [])

        horarios_ids = [h.id for h in horarios_turno]

        if not horarios_ids:
            self._cache_capacidad_profesor[cache_key] = 0
            return 0

        # 2. Verificar si el profesor tiene ALGUNA disponibilidad registrada
        tiene_disponibilidad_registrada = DisponibilidadProfesor.query.filter(
            DisponibilidadProfesor.profesor_id == profesor_id,
            DisponibilidadProfesor.activo == True
        ).first() is not None

        if tiene_disponibilidad_registrada:
            # Contar slots disponibles con query optimizada (COUNT en BD)
            slots_totales = DisponibilidadProfesor.query.filter(
                DisponibilidadProfesor.profesor_id == profesor_id,
                DisponibilidadProfesor.horario_id.in_(horarios_ids),
                DisponibilidadProfesor.dia_semana.in_(self.dias_semana),
                DisponibilidadProfesor.activo == True,
                DisponibilidadProfesor.disponible == True,
            ).count()

            # Si el profesor tiene asignación directa pero 0 slots disponibles en este turno,
            # asumir disponibilidad completa (la asignación explícita lo autoriza)
            if slots_totales == 0 and profesor_id in self._profesores_asignacion_directa:
                slots_totales = len(horarios_ids) * len(self.dias_semana)
                logger.info(f"Profesor ID {profesor_id} con asignación directa, "
                           f"asumiendo disponibilidad completa: {slots_totales} slots en turno {turno}")
        else:
            # Professor has no explicit availability registered
            from models import ConfiguracionSistema
            require_explicit = ConfiguracionSistema.get_config(
                'require_explicit_availability', False
            )
            if require_explicit:
                # Strict mode: no availability = 0 capacity
                slots_totales = 0
                logger.warning(f"Profesor ID {profesor_id} sin disponibilidad registrada. "
                               f"Modo estricto activo: capacidad = 0")
            else:
                # Legacy mode: assume full availability
                slots_totales = len(horarios_ids) * len(self.dias_semana)
                logger.info(f"Profesor ID {profesor_id} sin disponibilidad explícita. "
                           f"Asumiendo disponibilidad completa: {slots_totales} slots en turno {turno}")

        # 3. Contar slots ocupados (HorarioAcademico)
        # Excluyendo los grupos actuales (porque los estamos regenerando)
        grupos_codigos_actuales = [g.codigo.upper() for g in self.grupos]

        slots_ocupados = HorarioAcademico.query.filter(
            HorarioAcademico.profesor_id == profesor_id,
            HorarioAcademico.activo == True,
            HorarioAcademico.horario_id.in_(horarios_ids),
            HorarioAcademico.dia_semana.in_(self.dias_semana),
            ~HorarioAcademico.grupo.in_(grupos_codigos_actuales)
        ).count()

        capacidad = max(0, slots_totales - slots_ocupados)

        # Guardar en caché
        self._cache_capacidad_profesor[cache_key] = capacidad
        return capacidad

    def _calcular_slots_efectivos(self, grupo, materias, horarios_turno, detalle=False):
        """
        Calcula cuántos slots tiene disponibilidad AL MENOS UN profesor del grupo.
        Esto indica la capacidad máxima real del grupo.
        
        Args:
            detalle: Si True, retorna también los slots sin cobertura
        """
        slots_efectivos = 0
        slots_sin_cobertura = []
        
        for horario in horarios_turno:
            for dia in self.dias_semana:
                # Verificar si al menos un profesor tiene disponibilidad en este slot
                hay_profesor_disponible = False
                
                for materia in materias:
                    profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))
                    if not profesor:
                        continue
                    
                    disp = DisponibilidadProfesor.query.filter_by(
                        profesor_id=profesor.id,
                        horario_id=horario.id,
                        dia_semana=dia,
                        activo=True,
                        disponible=True
                    ).first()
                    
                    if disp:
                        hay_profesor_disponible = True
                        break
                
                if hay_profesor_disponible:
                    slots_efectivos += 1
                else:
                    slots_sin_cobertura.append(f"{dia} {horario.hora_inicio.strftime('%H:%M')}")
        
        if detalle:
            return slots_efectivos, slots_sin_cobertura
        return slots_efectivos

    def cargar_horarios(self):
        """Cargar horarios por turno"""
        print("⏰ Cargando horarios...")

        turnos = set(g.turno for g in self.grupos)

        for turno in turnos:
            turno_str = "matutino" if turno == "M" else "vespertino"
            horarios = (
                Horario.query.filter_by(turno=turno_str, activo=True)
                .order_by(Horario.orden)
                .all()
            )
            self.horarios_por_turno[turno] = horarios
            print(f"   ✓ {turno_str.capitalize()}: {len(horarios)} horarios")

    def cargar_disponibilidades(self):
        """
        Cargar disponibilidades de profesores seleccionados.

        Behavior depends on the 'require_explicit_availability' system config:
        - If True: professors WITHOUT explicit availability are flagged as errors
          and will NOT be assumed available. Generation will fail for their groups.
        - If False (default): professors without availability are assumed fully
          available (legacy behavior for backwards compatibility).
        """
        from models import ConfiguracionSistema

        print("📅 Cargando disponibilidades...")

        require_explicit = ConfiguracionSistema.get_config(
            'require_explicit_availability', False
        )

        profesores_ids = set(p.id for p in self.profesor_por_materia_grupo.values())
        profesores_sin_disponibilidad = []

        # Obtener todos los horarios disponibles (para crear disponibilidad virtual)
        todos_los_horarios = {}
        for turno, horarios in self.horarios_por_turno.items():
            for horario in horarios:
                todos_los_horarios[horario.id] = horario

        for profesor_id in profesores_ids:
            disponibilidades_profesor = DisponibilidadProfesor.query.filter(
                DisponibilidadProfesor.profesor_id == profesor_id,
                DisponibilidadProfesor.activo == True,
            ).all()

            disponibilidad_dict = {}
            for dia in self.dias_semana:
                disponibilidad_dict[dia] = {}

            slots_disponibles = 0

            if disponibilidades_profesor:
                for disp in disponibilidades_profesor:
                    if disp.dia_semana in disponibilidad_dict:
                        disponibilidad_dict[disp.dia_semana][disp.horario_id] = disp.disponible
                        if disp.disponible:
                            slots_disponibles += 1

                # Si el profesor tiene asignación directa, verificar disponibilidad
                # por turno. Si no tiene slots en un turno donde está asignado,
                # asumir disponibilidad completa para ese turno.
                if profesor_id in self._profesores_asignacion_directa:
                    for turno, horarios_turno in self.horarios_por_turno.items():
                        horarios_turno_ids = {h.id for h in horarios_turno}
                        slots_turno = sum(
                            1 for dia in self.dias_semana
                            for hid in horarios_turno_ids
                            if disponibilidad_dict.get(dia, {}).get(hid, False)
                        )
                        if slots_turno == 0:
                            profesor = User.query.get(profesor_id)
                            nombre_profesor = f"{profesor.nombre} {profesor.apellido}" if profesor else f"ID:{profesor_id}"
                            turno_label = "matutino" if turno == "M" else "vespertino"
                            logger.warning(f"Profesor {nombre_profesor} con asignación directa pero sin "
                                           f"slots en turno {turno_label}. Asumiendo disponibilidad completa.")
                            for dia in self.dias_semana:
                                for horario in horarios_turno:
                                    disponibilidad_dict[dia][horario.id] = True
                                    slots_disponibles += 1
            else:
                profesor = User.query.get(profesor_id)
                nombre_profesor = f"{profesor.nombre} {profesor.apellido}" if profesor else f"ID:{profesor_id}"
                profesores_sin_disponibilidad.append((profesor_id, nombre_profesor))

                if require_explicit:
                    # Strict mode: leave availability empty (all slots unavailable)
                    logger.warning(f"Profesor {nombre_profesor} sin disponibilidad registrada "
                                   f"(modo estricto activo - NO se asumirá disponible)")
                else:
                    # Legacy mode: assume full availability
                    for dia in self.dias_semana:
                        for horario_id in todos_los_horarios.keys():
                            disponibilidad_dict[dia][horario_id] = True
                            slots_disponibles += 1

            self.disponibilidades[profesor_id] = disponibilidad_dict

            profesor = User.query.get(profesor_id)
            nombre_profesor = f"{profesor.nombre} {profesor.apellido}" if profesor else f"ID:{profesor_id}"
            logger.debug(f"  Profesor {nombre_profesor}: {slots_disponibles} slots disponibles")

        if profesores_sin_disponibilidad:
            mode_label = "BLOQUEADOS" if require_explicit else "disponibilidad completa asumida"
            print(f"   ⚠️ {len(profesores_sin_disponibilidad)} profesores sin disponibilidad explícita "
                  f"({mode_label}):")
            for _, nombre in profesores_sin_disponibilidad[:5]:
                print(f"      - {nombre}")
            if len(profesores_sin_disponibilidad) > 5:
                print(f"      ... y {len(profesores_sin_disponibilidad) - 5} más")

        print(f"   ✓ Disponibilidades cargadas para {len(profesores_ids)} profesores")

    def crear_modelo(self):
        """Crear modelo CP-SAT"""
        print("🔧 Creando modelo OR-Tools...")

        self.model = cp_model.CpModel()
        self.variables = {}

        total_vars = 0

        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]

            for materia in materias:
                profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))
                if not profesor:
                    continue

                for horario in horarios:
                    for dia_idx, dia in enumerate(self.dias_semana):
                        var_name = f"G{grupo.id}_M{materia.id}_H{horario.id}_D{dia_idx}"
                        self.variables[(grupo.id, materia.id, horario.id, dia_idx)] = (
                            self.model.NewBoolVar(var_name)
                        )
                        total_vars += 1

        print(f"   ✓ {total_vars} variables creadas")

    def agregar_restricciones(self):
        """Agregar restricciones al modelo"""
        print("🔒 Agregando restricciones...")

        # 1. Horas requeridas por materia
        self._restriccion_horas_materia()

        # 2. No conflicto de profesor (un profesor no puede dar dos clases simultáneas)
        self._restriccion_no_conflicto_profesor()

        # 3. Disponibilidad de profesor
        self._restriccion_disponibilidad()

        # 4. CRÍTICO: Respetar horarios existentes (GENERACIÓN SECUENCIAL)
        # Llama a la versión mejorada que no filtra por materia
        self._restriccion_horarios_existentes()

        # 5. No conflicto de grupo
        self._restriccion_no_conflicto_grupo()

        # 6. Máximo 3 horas seguidas de misma materia por día
        self._restriccion_max_horas_consecutivas()

        # 7. NUEVO: Forzar horas consecutivas (sin huecos)
        self._restriccion_horas_consecutivas()

        # 8. Máximo 8 horas por día por profesor
        self._restriccion_max_horas_dia_profesor()

        # 9. NUEVO: Máximo 2 horas muertas por profesor por día
        self._restriccion_max_horas_muertas_profesor()

        # 10. NUEVO: Máximo horas semanales según tipo de profesor
        # Tiempo Completo: 40h/semana, Asignatura: 20h/semana
        self._restriccion_max_horas_semana_profesor()

        print("   ✓ Todas las restricciones agregadas")

    def _restriccion_horas_materia(self):
        """Cada materia debe tener exactamente sus horas requeridas"""
        print("   📐 Configurando horas por materia...")
        
        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]

            for materia in materias:
                horas = materia.horas_semanales or 3

                asignaciones = []
                for horario in horarios:
                    for dia_idx in range(len(self.dias_semana)):
                        var = self.variables.get(
                            (grupo.id, materia.id, horario.id, dia_idx)
                        )
                        if var is not None:
                            asignaciones.append(var)

                if asignaciones:
                    # IMPORTANTE: Esta restricción fuerza exactamente 'horas' bloques para esta materia
                    self.model.Add(sum(asignaciones) == horas)
                    logger.debug(f"  {grupo.codigo}/{materia.codigo}: {horas}h con {len(asignaciones)} variables posibles")
                else:
                    logger.warning(f"  ⚠️ {grupo.codigo}/{materia.codigo}: Sin variables de asignación disponibles")


    def _restriccion_no_conflicto_profesor(self):
        """Un profesor no puede dar dos clases al mismo tiempo"""
        # Agrupar variables por profesor, horario y día
        profesor_slots = defaultdict(list)

        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]

            for materia in materias:
                profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))
                if not profesor:
                    continue

                for horario in horarios:
                    for dia_idx in range(len(self.dias_semana)):
                        var = self.variables.get(
                            (grupo.id, materia.id, horario.id, dia_idx)
                        )
                        if var is not None:
                            profesor_slots[(profesor.id, horario.id, dia_idx)].append(
                                var
                            )

        # Agregar restricciones
        for (profesor_id, horario_id, dia_idx), vars_list in profesor_slots.items():
            if len(vars_list) > 1:
                self.model.Add(sum(vars_list) <= 1)

    def _restriccion_disponibilidad(self):
        """Profesor solo puede dar clases cuando está disponible"""
        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]

            for materia in materias:
                profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))
                if not profesor:
                    continue

                disp_profesor = self.disponibilidades.get(profesor.id, {})

                for horario in horarios:
                    for dia_idx, dia in enumerate(self.dias_semana):
                        disponible = disp_profesor.get(dia, {}).get(horario.id, False)

                        if not disponible:
                            var = self.variables.get(
                                (grupo.id, materia.id, horario.id, dia_idx)
                            )
                            if var is not None:
                                self.model.Add(var == 0)

    def _restriccion_horarios_existentes(self):
        """
        CRÍTICO para generación secuencial: Respetar horarios ya asignados a profesores.
        Si un profesor ya tiene una clase en cierto horario/día, no puede tener otra.

        OPTIMIZADO: Prefetch ALL existing schedules for all relevant professors
        in a single query instead of N+1 queries per professor.
        """
        print("📋 Verificando horarios ya existentes...")
        logger.info("Verificando conflictos con horarios existentes...")

        restricciones_aplicadas = 0
        profesores_con_conflictos = set()

        # Collect all unique professors in this generation
        profesores_unicos = set()
        for grupo in self.grupos:
            for materia in self.materias_por_grupo.get(grupo.id, []):
                profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))
                if profesor:
                    profesores_unicos.add(profesor.id)

        if not profesores_unicos:
            print("   ✓ No hay horarios previos que bloquear")
            return

        grupos_codigos_actuales = [g.codigo.upper() for g in self.grupos]

        # OPTIMIZED: Single query to fetch ALL existing schedules for all professors
        horarios_existentes = HorarioAcademico.query.filter(
            HorarioAcademico.profesor_id.in_(profesores_unicos),
            HorarioAcademico.activo == True,
            ~HorarioAcademico.grupo.in_(grupos_codigos_actuales),
        ).all()

        # Index by professor_id for fast lookup
        horarios_por_profesor = defaultdict(list)
        for ha in horarios_existentes:
            horarios_por_profesor[ha.profesor_id].append(ha)

        for profesor_id, horarios_prof in horarios_por_profesor.items():
            profesores_con_conflictos.add(profesor_id)

            for ha in horarios_prof:
                try:
                    dia_idx = self.dias_semana.index(ha.dia_semana)
                except ValueError:
                    continue

                # Block this slot for ALL subjects this professor teaches in current groups
                for grupo in self.grupos:
                    for materia in self.materias_por_grupo.get(grupo.id, []):
                        profesor = self.profesor_por_materia_grupo.get(
                            (grupo.id, materia.id)
                        )
                        if profesor and profesor.id == profesor_id:
                            var = self.variables.get(
                                (grupo.id, materia.id, ha.horario_id, dia_idx)
                            )
                            if var is not None:
                                self.model.Add(var == 0)
                                restricciones_aplicadas += 1

        if restricciones_aplicadas > 0:
            msg = f"{restricciones_aplicadas} slots bloqueados por horarios existentes ({len(profesores_con_conflictos)} profesores con conflictos)"
            print(f"   ✓ {msg}")
            logger.info(msg)
        else:
            print("   ✓ No hay horarios previos que bloquear")

    def _restriccion_no_conflicto_grupo(self):
        """Un grupo no puede tener dos materias al mismo tiempo"""
        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]

            for horario in horarios:
                for dia_idx in range(len(self.dias_semana)):
                    asignaciones = []

                    for materia in materias:
                        var = self.variables.get(
                            (grupo.id, materia.id, horario.id, dia_idx)
                        )
                        if var is not None:
                            asignaciones.append(var)

                    if asignaciones:
                        self.model.Add(sum(asignaciones) <= 1)

    def _restriccion_max_horas_consecutivas(self):
        """Máximo de horas por día según horas_semanales de la materia"""
        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]

            for materia in materias:
                horas_semanales = materia.horas_semanales or 3
                # Máximo por día: min(3, horas_semanales) para evitar todo en un día
                # Pero si tiene pocas horas, permitir que estén todas el mismo día
                max_por_dia = min(3, horas_semanales)

                for dia_idx in range(len(self.dias_semana)):
                    asignaciones = []

                    for horario in horarios:
                        var = self.variables.get(
                            (grupo.id, materia.id, horario.id, dia_idx)
                        )
                        if var is not None:
                            asignaciones.append(var)

                    if asignaciones:
                        self.model.Add(sum(asignaciones) <= max_por_dia)

    def _restriccion_horas_consecutivas(self):
        """
        FUERZA que las horas de una materia sean CONSECUTIVAS cuando se asignan el mismo día.
        Evita patrón: Inglés 08:00, otra materia 09:00-10:00, Inglés 11:00

        Estrategia: Para CUALQUIER par de horas (i, j) donde j > i+1, si ambas están
        asignadas, TODAS las horas intermedias también deben estarlo.
        """
        print("   🔗 Configurando restricción de horas consecutivas...")

        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            # Ordenar horarios por hora de inicio para saber cuáles son consecutivos
            horarios = sorted(self.horarios_por_turno[grupo.turno],
                             key=lambda h: h.hora_inicio)

            for materia in materias:
                for dia_idx in range(len(self.dias_semana)):
                    # Obtener todas las variables para esta materia en este día, ordenadas por hora
                    vars_dia = []
                    for horario in horarios:
                        var = self.variables.get((grupo.id, materia.id, horario.id, dia_idx))
                        if var is not None:
                            vars_dia.append(var)

                    n = len(vars_dia)
                    if n < 2:
                        continue

                    # Para CADA par de horas (i, j) donde hay huecos entre ellas,
                    # si ambas están asignadas, todas las intermedias también
                    for i in range(n):
                        for j in range(i + 2, n):  # j > i+1 significa hay hueco
                            # Si hora[i]=1 y hora[j]=1, entonces todas las horas intermedias deben ser 1
                            # Restricción: hora[i] + hora[j] <= 1 + sum(horas_intermedias)
                            # Si i=1, j=1 y intermedias=0, da 2 <= 1, VIOLACIÓN
                            horas_intermedias = vars_dia[i+1:j]
                            if horas_intermedias:
                                self.model.Add(
                                    vars_dia[i] + vars_dia[j] <= 1 + sum(horas_intermedias)
                                )

    def _restriccion_max_horas_dia_profesor(self):
        """Máximo 8 horas por día por profesor"""
        profesor_dia = defaultdict(list)

        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]

            for materia in materias:
                profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))
                if not profesor:
                    continue

                for horario in horarios:
                    for dia_idx in range(len(self.dias_semana)):
                        var = self.variables.get(
                            (grupo.id, materia.id, horario.id, dia_idx)
                        )
                        if var is not None:
                            profesor_dia[(profesor.id, dia_idx)].append(var)

        for (profesor_id, dia_idx), vars_list in profesor_dia.items():
            self.model.Add(sum(vars_list) <= 8)

    def _restriccion_max_horas_semana_profesor(self):
        """
        Máximo de horas semanales según tipo de profesor.
        Usa los límites configurados desde el panel de administración.
        """
        from models import ConfiguracionSistema

        print("   📅 Configurando restricción de horas semanales por profesor...")

        # Obtener límites desde la configuración del sistema
        limite_tiempo_completo = ConfiguracionSistema.get_config('horas_tiempo_completo', 40)
        limite_asignatura = ConfiguracionSistema.get_config('horas_asignatura', 20)
        limite_absoluto = ConfiguracionSistema.get_config('horas_limite_absoluto', 50)

        print(f"      Límites configurados: TC={limite_tiempo_completo}h, PA={limite_asignatura}h, Abs={limite_absoluto}h")

        # Recolectar todas las variables por profesor (todas las horas de toda la semana)
        profesor_semana = defaultdict(list)
        profesores_info = {}  # Para guardar info del profesor

        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]

            for materia in materias:
                profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))
                if not profesor:
                    continue

                # Guardar info del profesor
                if profesor.id not in profesores_info:
                    profesores_info[profesor.id] = profesor

                for horario in horarios:
                    for dia_idx in range(len(self.dias_semana)):
                        var = self.variables.get(
                            (grupo.id, materia.id, horario.id, dia_idx)
                        )
                        if var is not None:
                            profesor_semana[profesor.id].append(var)

        # Aplicar restricción según tipo de profesor
        for profesor_id, vars_list in profesor_semana.items():
            profesor = profesores_info.get(profesor_id)
            if not profesor:
                continue

            # Determinar máximo semanal según tipo de profesor (desde configuración)
            if profesor.rol == 'profesor_completo':
                max_horas_semana = limite_tiempo_completo
            elif profesor.rol == 'profesor_asignatura':
                max_horas_semana = limite_asignatura
            else:
                # Por defecto, usar límite de asignatura
                max_horas_semana = limite_asignatura

            # Aplicar límite absoluto
            max_horas_semana = min(max_horas_semana, limite_absoluto)

            # Agregar restricción
            if vars_list:
                self.model.Add(sum(vars_list) <= max_horas_semana)
                logger.debug(f"   Profesor {profesor.nombre}: máx {max_horas_semana}h/semana ({profesor.rol})")

    def _restriccion_max_horas_muertas_profesor(self):
        """
        Máximo 2 horas muertas (huecos) por profesor por día.

        Ejemplo: Si un profesor tiene clases a las 08:00, 09:00, 12:00, 13:00
        tiene 2 horas muertas (10:00 y 11:00). Esto es el máximo permitido.

        Estrategia: Contar huecos = (última hora - primera hora + 1) - horas_trabajadas
        Si huecos > 2, es inválido.
        """
        print("   ⏰ Configurando restricción de horas muertas por profesor...")

        # Recolectar variables por (profesor, día, horario_idx)
        profesor_dia_horarios = defaultdict(dict)

        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios_ordenados = sorted(self.horarios_por_turno[grupo.turno],
                                        key=lambda h: h.hora_inicio)

            for materia in materias:
                profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))
                if not profesor:
                    continue

                for idx, horario in enumerate(horarios_ordenados):
                    for dia_idx in range(len(self.dias_semana)):
                        var = self.variables.get((grupo.id, materia.id, horario.id, dia_idx))
                        if var is not None:
                            key = (profesor.id, dia_idx)
                            if idx not in profesor_dia_horarios[key]:
                                profesor_dia_horarios[key][idx] = []
                            profesor_dia_horarios[key][idx].append(var)

        # Para cada (profesor, día), crear restricción de huecos
        # Garantiza: entre cualquier par de clases, máximo 2 slots vacíos.
        # Corrige el bug original que no contaba slots sin variables (siempre vacíos).
        for (profesor_id, dia_idx), horarios_dict in profesor_dia_horarios.items():
            if len(horarios_dict) < 2:
                continue

            indices = sorted(horarios_dict.keys())

            # Crear variable auxiliar para cada slot: 1 si tiene al menos una clase
            slot_ocupado = {}
            for idx in indices:
                vars_en_slot = horarios_dict[idx]
                ocupado = self.model.NewBoolVar(f'ocup_p{profesor_id}_d{dia_idx}_h{idx}')
                self.model.Add(sum(vars_en_slot) >= 1).OnlyEnforceIf(ocupado)
                self.model.Add(sum(vars_en_slot) == 0).OnlyEnforceIf(ocupado.Not())
                slot_ocupado[idx] = ocupado

            ordered_indices = sorted(slot_ocupado.keys())

            # Para cada par (i, j) de slots donde el profesor PUEDE tener clase:
            # Si ambos están ocupados, los huecos entre ellos deben ser <= 2.
            # Los huecos incluyen tanto slots con variables vacías como slots sin
            # variables (donde no puede haber clase → siempre vacíos).
            for i_pos in range(len(ordered_indices)):
                for j_pos in range(i_pos + 1, len(ordered_indices)):
                    idx_i = ordered_indices[i_pos]
                    idx_j = ordered_indices[j_pos]

                    # Total de slots intermedios en el rango real (incluyendo sin variables)
                    total_intermedios = idx_j - idx_i - 1

                    if total_intermedios <= 2:
                        continue  # Máximo 2 huecos posibles, restricción siempre cumplida

                    # Slots intermedios CON variables (podrían estar ocupados)
                    intermedios_con_var = [
                        slot_ocupado[idx] for idx in ordered_indices
                        if idx_i < idx < idx_j
                    ]
                    # Slots intermedios SIN variables = siempre vacíos (huecos fijos)
                    huecos_fijos = total_intermedios - len(intermedios_con_var)

                    # Restricción: huecos_fijos + intermedios_vacios <= 2
                    # => intermedios_vacios <= 2 - huecos_fijos
                    # => len(intermedios_con_var) - sum(intermedios_con_var) <= 2 - huecos_fijos
                    # => sum(intermedios_con_var) >= len(intermedios_con_var) - 2 + huecos_fijos
                    min_ocupados = len(intermedios_con_var) - 2 + huecos_fijos

                    if min_ocupados > 0 and intermedios_con_var:
                        self.model.Add(
                            sum(intermedios_con_var) >= min_ocupados
                        ).OnlyEnforceIf([slot_ocupado[idx_i], slot_ocupado[idx_j]])

    def agregar_funcion_objetivo(self):
        """Función objetivo para equilibrar horarios"""
        print("🎯 Configurando función objetivo...")

        penalizaciones = []

        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]

            # Penalizar horarios muy tempranos o muy tardíos
            for idx, horario in enumerate(horarios):
                for materia in materias:
                    for dia_idx in range(len(self.dias_semana)):
                        var = self.variables.get(
                            (grupo.id, materia.id, horario.id, dia_idx)
                        )
                        if var is not None:
                            if idx == 0:  # Primera hora
                                penalizaciones.append(var * 2)
                            elif idx == len(horarios) - 1:  # Última hora
                                penalizaciones.append(var * 2)

        if penalizaciones:
            self.model.Minimize(sum(penalizaciones))

    def agregar_funcion_objetivo_mejorada(self):
        """
        Función objetivo OPTIMIZADA para convergencia rápida:
        1. Penalizar horarios extremos (suave)
        2. Favorecer distribución de materias en diferentes días
        
        OPTIMIZADO: Eliminadas variables auxiliares innecesarias que ralentizaban el solver
        """
        obj_terms = []

        for grupo in self.grupos:
            materias = self.materias_por_grupo[grupo.id]
            horarios = self.horarios_por_turno[grupo.turno]
            
            # --- 1. Penalizar horarios tempranos/tardíos extremos (suave) ---
            for idx, horario in enumerate(horarios):
                peso = 0
                if idx == 0: peso = 5  # Reducido de 10 a 5
                elif idx == len(horarios) - 1: peso = 5
                
                if peso > 0:
                    for materia in materias:
                        for dia_idx in range(len(self.dias_semana)):
                            var = self.variables.get((grupo.id, materia.id, horario.id, dia_idx))
                            if var is not None:
                                obj_terms.append(var * peso)

            # --- 2. Penalizar mismo slot repetido (sin variables auxiliares) ---
            # Enfoque simplificado: usar directamente la suma de variables
            for materia in materias:
                for horario in horarios:
                    vars_dias = []
                    for dia_idx in range(len(self.dias_semana)):
                        var = self.variables.get((grupo.id, materia.id, horario.id, dia_idx))
                        if var is not None:
                            vars_dias.append(var)
                    
                    # Penalizar directamente la suma (sin crear IntVar auxiliar)
                    if len(vars_dias) > 1:
                        for v in vars_dias:
                            obj_terms.append(v * 10)

        if obj_terms:
            self.model.Minimize(sum(obj_terms))

    def resolver(self):
        """Resolver el modelo"""
        print(f"🧠 Resolviendo modelo (tiempo límite: {self.tiempo_limite}s)...")

        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = self.tiempo_limite
        self.solver.parameters.num_search_workers = 8

        status = self.solver.Solve(self.model)

        if status == cp_model.OPTIMAL:
            print("   ✅ Solución ÓPTIMA encontrada")
            return True
        elif status == cp_model.FEASIBLE:
            print("   ✅ Solución FACTIBLE encontrada")
            return True
        else:
            print(f"   ❌ No se encontró solución. Estado: {status}")
            return False

    def guardar_horarios(self):
        """Guardar horarios generados en la base de datos.

        Usa SAVEPOINT para atomicidad: si la inserción falla,
        los horarios previos NO se eliminan.
        """
        print("💾 Guardando horarios...")
        logger.info(f"Guardando horarios para {len(self.grupos)} grupos")
        print(f"   📝 Usando creado_por: {self.creado_por}")

        try:
            # SAVEPOINT: si falla la inserción, el rollback restaura los datos previos
            nested = db.session.begin_nested()

            try:
                # Eliminar horarios anteriores SOLO de estos grupos específicos
                for grupo in self.grupos:
                    grupo_codigo_normalizado = grupo.codigo.upper()
                    deleted_count = HorarioAcademico.query.filter(
                        HorarioAcademico.grupo == grupo_codigo_normalizado
                    ).delete(synchronize_session=False)
                    if deleted_count > 0:
                        print(f"   🗑️ Eliminados {deleted_count} horarios previos de {grupo_codigo_normalizado}")

                # Guardar nuevos horarios
                horarios_por_grupo = defaultdict(list)
                grupos_map = {g.id: g for g in self.grupos}

                for (grupo_id, materia_id, horario_id, dia_idx), var in self.variables.items():
                    if self.solver.Value(var) == 1:
                        profesor = self.profesor_por_materia_grupo.get((grupo_id, materia_id))
                        if not profesor:
                            logger.warning(f"No se encontró profesor para grupo_id={grupo_id}, materia_id={materia_id}")
                            continue

                        dia = self.dias_semana[dia_idx]

                        grupo_obj = grupos_map.get(grupo_id)
                        if not grupo_obj:
                            logger.error(f"Grupo {grupo_id} no encontrado en grupos_map")
                            continue
                        grupo_codigo = grupo_obj.codigo

                        horario_academico = HorarioAcademico(
                            profesor_id=profesor.id,
                            materia_id=materia_id,
                            horario_id=horario_id,
                            dia_semana=dia,
                            grupo=grupo_codigo.upper(),
                            periodo_academico=self.periodo_academico,
                            version_nombre=self.version_nombre,
                            creado_por=self.creado_por,
                        )

                        db.session.add(horario_academico)
                        horarios_por_grupo[grupo_id].append(horario_academico)

                nested.commit()
            except Exception as e:
                nested.rollback()
                raise

            db.session.commit()
            logger.info("Cambios guardados exitosamente")

            self.horarios_generados = [
                h for horarios in horarios_por_grupo.values() for h in horarios
            ]

            # Estadísticas
            print("\n📊 RESUMEN:")
            for grupo in self.grupos:
                count = len(horarios_por_grupo[grupo.id])
                print(f"   {grupo.codigo}: {count} horarios")

            print(f"\n   TOTAL: {len(self.horarios_generados)} horarios generados")

            return self.horarios_generados

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al guardar horarios: {e}")
            raise

    def validar_recursos_antes_generar(self):
        """
        Valida que cada materia tenga al menos un profesor con disponibilidad suficiente
        ANTES de intentar generar horarios. Esto evita que el solver falle después de mucho tiempo.
        """
        print("🔍 Validando recursos antes de generar...")

        errores = []
        advertencias = []

        for grupo in self.grupos:
            materias = self.materias_por_grupo.get(grupo.id, [])
            turno_str = "matutino" if grupo.turno == "M" else "vespertino"
            horarios_turno = self.horarios_por_turno.get(grupo.turno, [])
            bloques_disponibles = len(horarios_turno) * len(self.dias_semana)

            horas_totales_grupo = 0

            for materia in materias:
                horas_req = materia.horas_semanales or 3
                horas_totales_grupo += horas_req

                profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))

                if not profesor:
                    errores.append(
                        f"Grupo {grupo.codigo}, Materia {materia.codigo}: Sin profesor asignado"
                    )
                    continue

                # Verificar disponibilidad del profesor en el turno correcto
                # Usar la capacidad restante REAL
                disp = self._contar_capacidad_restante(profesor.id, turno_str)

                if disp == 0:
                    errores.append(
                        f"Grupo {grupo.codigo}, {materia.codigo}: "
                        f"Profesor {profesor.nombre} {profesor.apellido} no tiene NINGUNA hora disponible en turno {turno_str}"
                    )
                elif disp < horas_req:
                    advertencias.append(
                        f"Grupo {grupo.codigo}, {materia.codigo}: "
                        f"Profesor {profesor.nombre} tiene {disp}h disponibles, se requieren {horas_req}h"
                    )

            # Verificar que hay suficientes bloques para todas las materias del grupo
            if horas_totales_grupo > bloques_disponibles:
                errores.append(
                    f"Grupo {grupo.codigo}: Requiere {horas_totales_grupo}h pero solo hay "
                    f"{bloques_disponibles} bloques disponibles ({len(horarios_turno)} horarios x {len(self.dias_semana)} días)"
                )
            
            # NUEVA VALIDACIÓN: Calcular slots efectivamente disponibles (donde AL MENOS UN profesor puede dar clase)
            slots_efectivos, slots_sin_cobertura = self._calcular_slots_efectivos(grupo, materias, horarios_turno, detalle=True)
            if horas_totales_grupo > slots_efectivos:
                # Agrupar slots sin cobertura por hora para mensaje más claro
                horas_problema = {}
                for slot in slots_sin_cobertura:
                    dia, hora = slot.rsplit(' ', 1)
                    if hora not in horas_problema:
                        horas_problema[hora] = []
                    horas_problema[hora].append(dia)
                
                detalle_horarios = []
                for hora, dias in sorted(horas_problema.items()):
                    if len(dias) == 5:  # Todos los días
                        detalle_horarios.append(f"{hora} (todos los días)")
                    else:
                        detalle_horarios.append(f"{hora} ({', '.join(dias)})")
                
                errores.append(
                    f"Grupo {grupo.codigo}: Requiere {horas_totales_grupo}h pero solo hay "
                    f"{slots_efectivos} slots con disponibilidad de profesores. "
                    f"Slots sin cobertura: {'; '.join(detalle_horarios)}"
                )

        # Mostrar resultados
        if advertencias:
            print(f"\n   ⚠️ ADVERTENCIAS ({len(advertencias)}):")
            for adv in advertencias:
                print(f"      - {adv}")

        if errores:
            print(f"\n   ❌ ERRORES CRÍTICOS ({len(errores)}):")
            for err in errores:
                print(f"      - {err}")
            return False, errores

        print("   ✅ Validación de recursos completada")
        return True, advertencias

    def generar(self):
        """Proceso principal de generación"""
        print("=" * 80)
        print("🚀 GENERADOR DE HORARIOS MEJORADO")
        print("=" * 80)

        try:
            self.cargar_grupos()
            self.seleccionar_profesores()
            self.cargar_horarios()
            self.cargar_disponibilidades()

            # NUEVO: Validación previa de recursos
            validacion_ok, mensajes = self.validar_recursos_antes_generar()
            if not validacion_ok:
                return {
                    "exito": False,
                    "mensaje": "❌ Validación fallida: "
                    + "; ".join(mensajes[:3])
                    + ("..." if len(mensajes) > 3 else ""),
                    "grupos_procesados": 0,
                    "horarios_generados": 0,
                    "errores_validacion": mensajes,
                }

            self.crear_modelo()
            self.agregar_restricciones()
            self.agregar_funcion_objetivo_mejorada()

            if self.resolver():
                self.guardar_horarios()
                materias_omitidas = getattr(self, '_materias_sin_profesor', [])
                msg = f"✅ Horarios generados exitosamente para {len(self.grupos)} grupos"
                if materias_omitidas:
                    msg += f" (⚠️ {len(materias_omitidas)} materias omitidas por falta de profesor)"
                return {
                    "exito": True,
                    "mensaje": msg,
                    "grupos_procesados": len(self.grupos),
                    "horarios_generados": len(self.horarios_generados),
                    "materias_omitidas": materias_omitidas,
                }
            else:
                # Generar diagnóstico detallado del fallo
                diagnostico = self._generar_diagnostico_fallo()
                return {
                    "exito": False,
                    "mensaje": diagnostico['mensaje'],
                    "grupos_procesados": 0,
                    "horarios_generados": 0,
                    "errores_validacion": diagnostico['problemas'],
                }

        except Exception as e:
            db.session.rollback()
            import traceback

            traceback.print_exc()
            return {
                "exito": False,
                "mensaje": f"❌ Error: {str(e)}",
                "grupos_procesados": 0,
                "horarios_generados": 0,
            }

    def _generar_diagnostico_fallo(self):
        """
        Genera un diagnóstico detallado cuando no se encuentra solución.
        Analiza cada grupo-materia para identificar problemas específicos.
        """
        problemas = []
        
        for grupo in self.grupos:
            materias = self.materias_por_grupo.get(grupo.id, [])
            horarios = self.horarios_por_turno.get(grupo.turno, [])
            
            for materia in materias:
                profesor = self.profesor_por_materia_grupo.get((grupo.id, materia.id))
                horas_req = materia.horas_semanales or 3
                
                if not profesor:
                    problemas.append(f"{grupo.codigo}/{materia.codigo}: Sin profesor asignado")
                    continue
                
                # Contar slots disponibles para este profesor
                disp_profesor = self.disponibilidades.get(profesor.id, {})
                slots_disponibles = 0
                
                for dia in self.dias_semana:
                    for horario in horarios:
                        if disp_profesor.get(dia, {}).get(horario.id, False):
                            slots_disponibles += 1
                
                if slots_disponibles < horas_req:
                    problemas.append(
                        f"{grupo.codigo}/{materia.codigo}: {profesor.nombre} {profesor.apellido} "
                        f"solo tiene {slots_disponibles}h disponibles (necesita {horas_req}h)"
                    )
        
        # Generar mensaje resumido
        if problemas:
            mensaje = "❌ " + "; ".join(problemas[:3])
            if len(problemas) > 3:
                mensaje += f" ... y {len(problemas) - 3} más"
        else:
            mensaje = "❌ No se encontró solución factible. Posible conflicto de horarios entre profesores compartidos."
        
        return {
            'mensaje': mensaje,
            'problemas': problemas
        }


def generar_horarios_por_etapas(
    grupos_ids,
    periodo_academico="2025-1",
    version_nombre=None,
    creado_por=None,
    dias_semana=None,
):
    """
    Función principal que genera horarios por etapas (turno por turno).

    Esta es la estrategia recomendada para conjuntos grandes de grupos.
    """
    print("=" * 80)
    print("🎯 GENERACIÓN POR ETAPAS")
    print("=" * 80)

    # Separar grupos por turno
    grupos_matutino = []
    grupos_vespertino = []

    for gid in grupos_ids:
        grupo = Grupo.query.get(gid)
        if grupo:
            if grupo.turno == "M":
                grupos_matutino.append(gid)
            else:
                grupos_vespertino.append(gid)

    resultados = {
        "exito": True,
        "mensaje": "",
        "grupos_procesados": 0,
        "horarios_generados": 0,
        "detalles": [],
    }

    # Etapa 1: Grupos matutinos
    if grupos_matutino:
        print(f"\n📌 ETAPA 1: Generando {len(grupos_matutino)} grupos MATUTINOS...")

        generador = GeneradorHorariosMejorado(
            grupos_ids=grupos_matutino,
            periodo_academico=periodo_academico,
            version_nombre=f"{version_nombre} - Matutino"
            if version_nombre
            else "Matutino",
            creado_por=creado_por,
            dias_semana=dias_semana,
            tiempo_limite=300,
        )

        resultado_mat = generador.generar()
        resultados["detalles"].append(("Matutino", resultado_mat))

        if resultado_mat["exito"]:
            resultados["grupos_procesados"] += resultado_mat["grupos_procesados"]
            resultados["horarios_generados"] += resultado_mat["horarios_generados"]
        else:
            resultados["exito"] = False
            resultados["mensaje"] += f"Matutino: {resultado_mat['mensaje']}. "

    # Etapa 2: Grupos vespertinos
    if grupos_vespertino:
        print(f"\n📌 ETAPA 2: Generando {len(grupos_vespertino)} grupos VESPERTINOS...")

        generador = GeneradorHorariosMejorado(
            grupos_ids=grupos_vespertino,
            periodo_academico=periodo_academico,
            version_nombre=f"{version_nombre} - Vespertino"
            if version_nombre
            else "Vespertino",
            creado_por=creado_por,
            dias_semana=dias_semana,
            tiempo_limite=300,
        )

        resultado_vesp = generador.generar()
        resultados["detalles"].append(("Vespertino", resultado_vesp))

        if resultado_vesp["exito"]:
            resultados["grupos_procesados"] += resultado_vesp["grupos_procesados"]
            resultados["horarios_generados"] += resultado_vesp["horarios_generados"]
        else:
            resultados["exito"] = False
            resultados["mensaje"] += f"Vespertino: {resultado_vesp['mensaje']}. "

    if resultados["exito"]:
        resultados["mensaje"] = (
            f"✅ Horarios generados: {resultados['grupos_procesados']} grupos, {resultados['horarios_generados']} horarios"
        )

    return resultados


def diagnosticar_y_generar(
    grupos_ids,
    periodo_academico="2025-1",
    version_nombre=None,
    creado_por=None,
    dias_semana=None,
):
    """
    Función que primero diagnostica y luego genera si es factible.
    """
    # Paso 1: Diagnóstico
    diagnostico = DiagnosticoGeneracion(grupos_ids, dias_semana)
    factible = diagnostico.ejecutar_diagnostico()
    reporte = diagnostico.get_reporte()

    if not factible:
        return {
            "exito": False,
            "mensaje": "No es posible generar horarios",
            "problemas": reporte["problemas"],
            "advertencias": reporte["advertencias"],
            "grupos_procesados": 0,
            "horarios_generados": 0,
        }

    # Paso 2: Generar por etapas
    resultado = generar_horarios_por_etapas(
        grupos_ids=grupos_ids,
        periodo_academico=periodo_academico,
        version_nombre=version_nombre,
        creado_por=creado_por,
        dias_semana=dias_semana,
    )

    resultado["advertencias"] = reporte["advertencias"]
    return resultado


def generar_horarios_secuencial(
    grupos_ids,
    periodo_academico="2025-1",
    version_nombre=None,
    creado_por=None,
    dias_semana=None,
):
    """
    ESTRATEGIA RECOMENDADA: Genera horarios GRUPO POR GRUPO.

    Esta estrategia es la más robusta porque:
    1. Cada grupo se genera de forma independiente
    2. Los horarios de profesores ya asignados se respetan
    3. Mayor probabilidad de éxito

    MEJORADO: Ahora refresca la sesión de BD después de cada grupo para
    asegurar que los horarios generados previamente sean visibles.

    Args:
        grupos_ids: Lista de IDs de grupos a generar
        periodo_academico: Período académico
        version_nombre: Nombre de la versión
        creado_por: ID del usuario
        dias_semana: Días de la semana

    Returns:
        dict: Resultado de la generación
    """
    from models import Grupo, HorarioAcademico

    print("=" * 80)
    print("🚀 GENERACIÓN SECUENCIAL (GRUPO POR GRUPO)")
    print("=" * 80)
    print(f"Total grupos a procesar: {len(grupos_ids)}")

    dias = dias_semana or ["lunes", "martes", "miercoles", "jueves", "viernes"]

    resultados = {
        "exito": True,
        "mensaje": "",
        "grupos_procesados": 0,
        "grupos_fallidos": 0,
        "horarios_generados": 0,
        "detalles": [],
    }

    # Ordenar grupos: primero los que tienen menos conflictos potenciales
    # (menos profesores compartidos con otros grupos)
    grupos_ordenados = _ordenar_grupos_por_complejidad(grupos_ids)

    for i, grupo_id in enumerate(grupos_ordenados, 1):
        grupo = Grupo.query.get(grupo_id)
        if not grupo:
            continue

        print(f"\n📌 [{i}/{len(grupos_ordenados)}] Generando grupo {grupo.codigo}...")

        try:
            # IMPORTANTE: Refrescar la sesión para ver horarios generados en iteraciones anteriores
            db.session.expire_all()

            generador = GeneradorHorariosMejorado(
                grupos_ids=[grupo_id],
                periodo_academico=periodo_academico,
                version_nombre=f"{version_nombre or 'Secuencial'} - {grupo.codigo}",
                creado_por=creado_por,
                dias_semana=dias,
                tiempo_limite=30,  # OPTIMIZADO: Reducido de 120s a 30s
            )

            resultado = generador.generar()

            if resultado["exito"]:
                # Asegurar que los cambios se persistan antes del siguiente grupo
                db.session.commit()

                resultados["grupos_procesados"] += 1
                resultados["horarios_generados"] += resultado["horarios_generados"]
                resultados["detalles"].append(
                    {
                        "grupo": grupo.codigo,
                        "exito": True,
                        "horarios": resultado["horarios_generados"],
                    }
                )
                print(
                    f"   ✅ {grupo.codigo}: {resultado['horarios_generados']} horarios"
                )
            else:
                resultados["grupos_fallidos"] += 1
                resultados["detalles"].append(
                    {
                        "grupo": grupo.codigo,
                        "exito": False,
                        "error": resultado["mensaje"],
                    }
                )
                print(f"   ❌ {grupo.codigo}: {resultado['mensaje']}")

        except Exception as e:
            db.session.rollback()
            resultados["grupos_fallidos"] += 1
            resultados["detalles"].append(
                {"grupo": grupo.codigo, "exito": False, "error": str(e)}
            )
            print(f"   ❌ {grupo.codigo}: Error - {str(e)}")
            import traceback

            traceback.print_exc()

    # Resumen final
    if resultados["grupos_procesados"] > 0:
        if resultados["grupos_fallidos"] == 0:
            resultados["mensaje"] = (
                f"✅ Generación exitosa: {resultados['grupos_procesados']} grupos, "
                f"{resultados['horarios_generados']} horarios"
            )
        else:
            resultados["exito"] = False
            resultados["mensaje"] = (
                f"⚠️ Generación parcial: {resultados['grupos_procesados']} exitosos, "
                f"{resultados['grupos_fallidos']} fallidos"
            )
    else:
        resultados["exito"] = False
        resultados["mensaje"] = "❌ No se pudo generar ningún horario"

    print("\n" + "=" * 80)
    print(f"📊 RESULTADO FINAL: {resultados['mensaje']}")
    print("=" * 80)

    return resultados


def _ordenar_grupos_por_complejidad(grupos_ids):
    """
    Ordena los grupos para procesarlos de menor a mayor complejidad.
    Los grupos con menos profesores compartidos van primero.
    """
    from models import Grupo, AsignacionProfesorGrupo

    # Contar cuántos grupos comparte cada profesor
    profesor_grupos = defaultdict(set)

    for gid in grupos_ids:
        asigs = AsignacionProfesorGrupo.query.filter_by(grupo_id=gid, activo=True).all()
        for asig in asigs:
            if asig.profesor_id:
                profesor_grupos[asig.profesor_id].add(gid)

    # Calcular complejidad de cada grupo
    # (suma de cuántos grupos comparte cada profesor del grupo)
    complejidad = {}

    for gid in grupos_ids:
        asigs = AsignacionProfesorGrupo.query.filter_by(grupo_id=gid, activo=True).all()
        score = 0
        for asig in asigs:
            if asig.profesor_id:
                score += (
                    len(profesor_grupos[asig.profesor_id]) - 1
                )  # -1 porque el grupo actual no cuenta
        complejidad[gid] = score

    # Ordenar de menor a mayor complejidad
    return sorted(grupos_ids, key=lambda x: complejidad.get(x, 0))
