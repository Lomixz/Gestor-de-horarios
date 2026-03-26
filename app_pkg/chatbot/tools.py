"""Tool definitions and role-based permissions for the chatbot."""

# Tool definitions in a format compatible with all LLM providers
TOOLS = {
    'get_schedule_group': {
        'name': 'get_schedule_group',
        'description': 'Obtiene el horario completo de un grupo académico dado su código (ej: 10MSC1). Devuelve una tabla con materias, profesores, días y horas.',
        'parameters': {
            'type': 'object',
            'properties': {
                'grupo_codigo': {
                    'type': 'string',
                    'description': 'Código del grupo (ej: 1MSI1, 10MSC1)'
                }
            },
            'required': ['grupo_codigo']
        }
    },
    'get_schedule_professor': {
        'name': 'get_schedule_professor',
        'description': 'Obtiene el horario completo de un profesor dado su nombre (o parte de él). Devuelve una tabla con materias, grupos, días y horas.',
        'parameters': {
            'type': 'object',
            'properties': {
                'nombre_profesor': {
                    'type': 'string',
                    'description': 'Nombre completo o parcial del profesor'
                }
            },
            'required': ['nombre_profesor']
        }
    },
    'get_my_schedule': {
        'name': 'get_my_schedule',
        'description': 'Obtiene el horario del profesor actualmente autenticado.',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    'list_groups': {
        'name': 'list_groups',
        'description': 'Lista todos los grupos académicos. Opcionalmente se puede filtrar por carrera.',
        'parameters': {
            'type': 'object',
            'properties': {
                'carrera': {
                    'type': 'string',
                    'description': 'Nombre o código de la carrera para filtrar (opcional)'
                }
            }
        }
    },
    'list_professors': {
        'name': 'list_professors',
        'description': 'Lista todos los profesores registrados. Opcionalmente se puede filtrar por carrera.',
        'parameters': {
            'type': 'object',
            'properties': {
                'carrera': {
                    'type': 'string',
                    'description': 'Nombre o código de la carrera para filtrar (opcional)'
                }
            }
        }
    },
    'list_subjects': {
        'name': 'list_subjects',
        'description': 'Lista todas las materias registradas. Opcionalmente se puede filtrar por carrera.',
        'parameters': {
            'type': 'object',
            'properties': {
                'carrera': {
                    'type': 'string',
                    'description': 'Nombre o código de la carrera para filtrar (opcional)'
                }
            }
        }
    },
    'get_stats': {
        'name': 'get_stats',
        'description': 'Obtiene estadísticas generales del sistema: número de usuarios, carreras, grupos, materias, horarios generados.',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    'add_user': {
        'name': 'add_user',
        'description': 'Crea un nuevo usuario en el sistema. IMPORTANTE: Antes de ejecutar, debes pedir TODOS los campos obligatorios: username, password, nombre, apellido, email, rol. Para profesores y jefe_carrera también pedir las carreras.',
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'description': 'Nombre de usuario único para login'},
                'password': {'type': 'string', 'description': 'Contraseña del usuario. Si el admin no proporciona una, genera una segura temporal.'},
                'nombre': {'type': 'string', 'description': 'Nombre del usuario'},
                'apellido': {'type': 'string', 'description': 'Apellido del usuario'},
                'email': {'type': 'string', 'description': 'Email del usuario (único)'},
                'rol': {
                    'type': 'string',
                    'description': 'Rol del usuario',
                    'enum': ['admin', 'jefe_carrera', 'profesor_completo', 'profesor_asignatura']
                },
                'telefono': {'type': 'string', 'description': 'Teléfono del usuario (opcional)'},
                'tipo_profesor': {'type': 'string', 'description': 'Tipo de profesor (opcional, para profesores): "completo" o "asignatura"'},
                'carreras': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Lista de códigos de carrera (requerido para profesores y jefe_carrera). Ej: ["ING-SIS", "ING-MEC"]'
                }
            },
            'required': ['username', 'password', 'nombre', 'apellido', 'email', 'rol']
        }
    },
    'create_backup': {
        'name': 'create_backup',
        'description': 'Genera un backup de la base de datos del sistema.',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    'generate_schedules': {
        'name': 'generate_schedules',
        'description': 'Genera horarios académicos. Puede generar para un grupo específico, una carrera completa, o todos los grupos. IMPORTANTE: Antes de ejecutar, DEBES preguntar al usuario cómo quiere nombrar esta versión de horarios.',
        'parameters': {
            'type': 'object',
            'properties': {
                'grupo_codigo': {
                    'type': 'string',
                    'description': 'Código de un grupo específico para generar su horario (ej: "10MSC1", "1MSI1"). Si se proporciona, solo genera para ese grupo.'
                },
                'carrera': {
                    'type': 'string',
                    'description': 'Código de la carrera para generar horarios de todos sus grupos (opcional, si no se especifica genera para todas)'
                },
                'version_nombre': {
                    'type': 'string',
                    'description': 'Nombre descriptivo para esta versión de horarios (ej: "Horarios Enero 2026", "Versión Final"). OBLIGATORIO: si el usuario no lo ha proporcionado, pregúntale antes de ejecutar.'
                }
            },
            'required': ['version_nombre']
        }
    },
    'get_professor_availability': {
        'name': 'get_professor_availability',
        'description': 'Consulta la disponibilidad de un profesor: muestra tanto la disponibilidad configurada como las horas libres reales (sin clase asignada).',
        'parameters': {
            'type': 'object',
            'properties': {
                'nombre_profesor': {
                    'type': 'string',
                    'description': 'Nombre completo o parcial del profesor'
                }
            },
            'required': ['nombre_profesor']
        }
    },
    'set_availability': {
        'name': 'set_availability',
        'description': 'Configura la disponibilidad del profesor para un día y turno específicos.',
        'parameters': {
            'type': 'object',
            'properties': {
                'dia': {
                    'type': 'string',
                    'description': 'Día de la semana',
                    'enum': ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
                },
                'horario_nombre': {
                    'type': 'string',
                    'description': 'Nombre del horario (ej: "1ra Hora", "2da Hora")'
                },
                'disponible': {
                    'type': 'boolean',
                    'description': 'True si está disponible, False si no'
                }
            },
            'required': ['dia', 'horario_nombre', 'disponible']
        }
    },
    'get_my_subjects': {
        'name': 'get_my_subjects',
        'description': 'Obtiene las materias asignadas al profesor actualmente autenticado.',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    'get_my_groups': {
        'name': 'get_my_groups',
        'description': 'Obtiene los grupos asignados al profesor actualmente autenticado.',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    # --- New tools ---
    'export_schedule_excel': {
        'name': 'export_schedule_excel',
        'description': 'Exporta el horario de un grupo o profesor en formato Excel.',
        'parameters': {
            'type': 'object',
            'properties': {
                'tipo': {
                    'type': 'string',
                    'description': 'Tipo de horario a exportar',
                    'enum': ['grupo', 'profesor']
                },
                'identificador': {
                    'type': 'string',
                    'description': 'Código del grupo (ej: 10MSC1) o nombre del profesor'
                }
            },
            'required': ['tipo', 'identificador']
        }
    },
    'export_schedule_pdf': {
        'name': 'export_schedule_pdf',
        'description': 'Exporta el horario de un profesor en formato PDF (formato FDA oficial).',
        'parameters': {
            'type': 'object',
            'properties': {
                'nombre_profesor': {
                    'type': 'string',
                    'description': 'Nombre completo del profesor'
                }
            },
            'required': ['nombre_profesor']
        }
    },
    'export_my_schedule': {
        'name': 'export_my_schedule',
        'description': 'Exporta el horario propio del profesor autenticado en Excel, PDF o CSV.',
        'parameters': {
            'type': 'object',
            'properties': {
                'formato': {
                    'type': 'string',
                    'description': 'Formato de exportación',
                    'enum': ['excel', 'pdf', 'csv']
                }
            },
            'required': ['formato']
        }
    },
    'export_schedule_csv': {
        'name': 'export_schedule_csv',
        'description': 'Exporta el horario de un grupo o profesor en formato CSV para descarga.',
        'parameters': {
            'type': 'object',
            'properties': {
                'tipo': {
                    'type': 'string',
                    'description': 'Tipo de horario a exportar',
                    'enum': ['grupo', 'profesor']
                },
                'identificador': {
                    'type': 'string',
                    'description': 'Código del grupo (ej: 10MSC1) o nombre del profesor'
                }
            },
            'required': ['tipo', 'identificador']
        }
    },
    'check_generation_progress': {
        'name': 'check_generation_progress',
        'description': 'Consulta el progreso de la generación de horarios activa.',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    'list_users': {
        'name': 'list_users',
        'description': 'Lista usuarios del sistema con filtro opcional por rol o estado.',
        'parameters': {
            'type': 'object',
            'properties': {
                'rol': {
                    'type': 'string',
                    'description': 'Filtrar por rol (opcional)',
                    'enum': ['admin', 'jefe_carrera', 'profesor_completo', 'profesor_asignatura']
                },
                'activo': {
                    'type': 'boolean',
                    'description': 'Filtrar por estado activo/inactivo (opcional)'
                }
            }
        }
    },
    'edit_user': {
        'name': 'edit_user',
        'description': 'Edita datos de un usuario existente. Se identifica por email o username.',
        'parameters': {
            'type': 'object',
            'properties': {
                'email_o_username': {
                    'type': 'string',
                    'description': 'Email o username del usuario a editar'
                },
                'nombre': {'type': 'string', 'description': 'Nuevo nombre (opcional)'},
                'apellido': {'type': 'string', 'description': 'Nuevo apellido (opcional)'},
                'telefono': {'type': 'string', 'description': 'Nuevo teléfono (opcional)'},
                'email': {'type': 'string', 'description': 'Nuevo email (opcional, se valida unicidad)'},
                'password': {'type': 'string', 'description': 'Nueva contraseña (opcional)'},
                'rol': {
                    'type': 'string',
                    'description': 'Nuevo rol (opcional)',
                    'enum': ['admin', 'jefe_carrera', 'profesor_completo', 'profesor_asignatura']
                },
                'activo': {'type': 'boolean', 'description': 'Activar o desactivar usuario (opcional)'},
                'carreras': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Reasignar carreras del usuario (array de códigos, ej: ["ING-SIS", "ING-MEC"]). Opcional.'
                }
            },
            'required': ['email_o_username']
        }
    },
    'delete_user': {
        'name': 'delete_user',
        'description': 'Desactiva un usuario del sistema (soft delete). Se identifica por email o username.',
        'parameters': {
            'type': 'object',
            'properties': {
                'email_o_username': {
                    'type': 'string',
                    'description': 'Email o username del usuario a desactivar'
                }
            },
            'required': ['email_o_username']
        }
    },
    'create_career': {
        'name': 'create_career',
        'description': 'Crea una nueva carrera en el sistema.',
        'parameters': {
            'type': 'object',
            'properties': {
                'nombre': {'type': 'string', 'description': 'Nombre de la carrera'},
                'codigo': {'type': 'string', 'description': 'Código de la carrera (ej: ING-SIS, MED)'},
                'descripcion': {'type': 'string', 'description': 'Descripción de la carrera (opcional)'},
                'facultad': {'type': 'string', 'description': 'Facultad a la que pertenece (opcional)'}
            },
            'required': ['nombre', 'codigo']
        }
    },
    'list_careers': {
        'name': 'list_careers',
        'description': 'Lista todas las carreras del sistema con información de profesores y jefe.',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    'create_subject': {
        'name': 'create_subject',
        'description': 'Crea una nueva materia en el sistema.',
        'parameters': {
            'type': 'object',
            'properties': {
                'nombre': {'type': 'string', 'description': 'Nombre de la materia'},
                'codigo': {'type': 'string', 'description': 'Código de la materia (ej: MAT-101)'},
                'cuatrimestre': {'type': 'integer', 'description': 'Número de cuatrimestre (1, 2, 3, etc.)'},
                'carrera_codigo': {'type': 'string', 'description': 'Código de la carrera a la que pertenece'},
                'creditos': {'type': 'integer', 'description': 'Número de créditos (opcional, default 3)'},
                'horas_semanales': {'type': 'integer', 'description': 'Horas semanales (opcional, default 0)'}
            },
            'required': ['nombre', 'codigo', 'cuatrimestre', 'carrera_codigo']
        }
    },

    # --- Import/Export tools ---
    'import_data': {
        'name': 'import_data',
        'description': 'Importa datos masivamente desde un archivo CSV/Excel que el usuario adjuntó. IMPORTANTE: El usuario DEBE haber adjuntado un archivo en su mensaje. Antes de ejecutar, pregunta al usuario qué tipo de datos contiene el archivo si no es claro.',
        'parameters': {
            'type': 'object',
            'properties': {
                'tipo_importacion': {
                    'type': 'string',
                    'description': 'Tipo de datos a importar del archivo',
                    'enum': ['profesores', 'materias', 'carreras', 'asignaciones_profesor', 'asignaciones_grupo']
                },
                'carrera_codigo': {
                    'type': 'string',
                    'description': 'Código de carrera por defecto para profesores/materias sin carrera especificada (opcional)'
                },
                'restar_horas': {
                    'type': 'integer',
                    'description': 'Horas a restar de horas_semanales de materias (opcional, default 0). Solo aplica para importación de materias.'
                }
            },
            'required': ['tipo_importacion']
        }
    },
    'download_import_template': {
        'name': 'download_import_template',
        'description': 'Genera y descarga una plantilla CSV para importación masiva de datos. Úsala cuando el usuario pida una plantilla o formato para subir datos.',
        'parameters': {
            'type': 'object',
            'properties': {
                'tipo': {
                    'type': 'string',
                    'description': 'Tipo de plantilla a descargar',
                    'enum': ['profesores', 'materias', 'carreras', 'asignaciones_profesor', 'asignaciones_grupo']
                }
            },
            'required': ['tipo']
        }
    },

    # --- Group CRUD ---
    'create_group': {
        'name': 'create_group',
        'description': 'Crea un nuevo grupo académico.',
        'parameters': {
            'type': 'object',
            'properties': {
                'carrera_codigo': {'type': 'string', 'description': 'Código de la carrera (ej: ING-SIS)'},
                'cuatrimestre': {'type': 'integer', 'description': 'Número de cuatrimestre (1-10)'},
                'turno': {'type': 'string', 'description': 'Turno del grupo', 'enum': ['M', 'V']},
                'numero_grupo': {'type': 'integer', 'description': 'Número del grupo (1, 2, 3...)'}
            },
            'required': ['carrera_codigo', 'cuatrimestre', 'turno', 'numero_grupo']
        }
    },
    'edit_group': {
        'name': 'edit_group',
        'description': 'Edita un grupo existente identificado por su código.',
        'parameters': {
            'type': 'object',
            'properties': {
                'codigo': {'type': 'string', 'description': 'Código del grupo a editar (ej: 1MSI1)'},
                'cuatrimestre': {'type': 'integer', 'description': 'Nuevo cuatrimestre (opcional)'},
                'turno': {'type': 'string', 'description': 'Nuevo turno (opcional)', 'enum': ['M', 'V']},
                'numero_grupo': {'type': 'integer', 'description': 'Nuevo número de grupo (opcional)'}
            },
            'required': ['codigo']
        }
    },
    'delete_group': {
        'name': 'delete_group',
        'description': 'Elimina un grupo académico (lo desactiva) junto con sus horarios.',
        'parameters': {
            'type': 'object',
            'properties': {
                'codigo': {'type': 'string', 'description': 'Código del grupo a eliminar'}
            },
            'required': ['codigo']
        }
    },

    # --- Career/Subject edit+delete ---
    'edit_career': {
        'name': 'edit_career',
        'description': 'Edita una carrera existente.',
        'parameters': {
            'type': 'object',
            'properties': {
                'codigo': {'type': 'string', 'description': 'Código actual de la carrera'},
                'nombre': {'type': 'string', 'description': 'Nuevo nombre (opcional)'},
                'descripcion': {'type': 'string', 'description': 'Nueva descripción (opcional)'},
                'facultad': {'type': 'string', 'description': 'Nueva facultad (opcional)'}
            },
            'required': ['codigo']
        }
    },
    'delete_career': {
        'name': 'delete_career',
        'description': 'Elimina (desactiva) una carrera del sistema.',
        'parameters': {
            'type': 'object',
            'properties': {
                'codigo': {'type': 'string', 'description': 'Código de la carrera a eliminar'}
            },
            'required': ['codigo']
        }
    },
    'edit_subject': {
        'name': 'edit_subject',
        'description': 'Edita una materia existente.',
        'parameters': {
            'type': 'object',
            'properties': {
                'codigo': {'type': 'string', 'description': 'Código actual de la materia'},
                'nombre': {'type': 'string', 'description': 'Nuevo nombre (opcional)'},
                'cuatrimestre': {'type': 'integer', 'description': 'Nuevo cuatrimestre (opcional)'},
                'creditos': {'type': 'integer', 'description': 'Nuevos créditos (opcional)'},
                'horas_semanales': {'type': 'integer', 'description': 'Nuevas horas semanales (opcional)'}
            },
            'required': ['codigo']
        }
    },
    'delete_subject': {
        'name': 'delete_subject',
        'description': 'Elimina (desactiva) una materia del sistema.',
        'parameters': {
            'type': 'object',
            'properties': {
                'codigo': {'type': 'string', 'description': 'Código de la materia a eliminar'}
            },
            'required': ['codigo']
        }
    },

    # --- Assignments ---
    'assign_subject_to_professor': {
        'name': 'assign_subject_to_professor',
        'description': 'Asigna una materia a un profesor.',
        'parameters': {
            'type': 'object',
            'properties': {
                'nombre_profesor': {'type': 'string', 'description': 'Nombre completo o parcial del profesor'},
                'materia_codigo': {'type': 'string', 'description': 'Código de la materia a asignar'}
            },
            'required': ['nombre_profesor', 'materia_codigo']
        }
    },
    'assign_professor_to_group': {
        'name': 'assign_professor_to_group',
        'description': 'Asigna un profesor a un grupo para impartir una materia específica.',
        'parameters': {
            'type': 'object',
            'properties': {
                'nombre_profesor': {'type': 'string', 'description': 'Nombre completo o parcial del profesor'},
                'grupo_codigo': {'type': 'string', 'description': 'Código del grupo'},
                'materia_codigo': {'type': 'string', 'description': 'Código de la materia a impartir'}
            },
            'required': ['nombre_profesor', 'grupo_codigo', 'materia_codigo']
        }
    },

    # --- Schedule version management ---
    'list_schedule_versions': {
        'name': 'list_schedule_versions',
        'description': 'Lista las versiones de horarios guardadas (backups).',
        'parameters': {
            'type': 'object',
            'properties': {}
        }
    },
    'restore_schedule_version': {
        'name': 'restore_schedule_version',
        'description': 'Restaura una versión anterior de horarios. IMPORTANTE: Esto reemplazará los horarios activos actuales.',
        'parameters': {
            'type': 'object',
            'properties': {
                'version_id': {'type': 'integer', 'description': 'ID de la versión a restaurar'}
            },
            'required': ['version_id']
        }
    },
    'delete_schedule': {
        'name': 'delete_schedule',
        'description': 'Elimina los horarios activos de un grupo específico.',
        'parameters': {
            'type': 'object',
            'properties': {
                'grupo_codigo': {'type': 'string', 'description': 'Código del grupo cuyos horarios se eliminarán'}
            },
            'required': ['grupo_codigo']
        }
    },
}

# Tools available per role
ROLE_TOOLS = {
    'admin': [
        'get_schedule_group', 'get_schedule_professor',
        'get_professor_availability',
        'list_groups', 'list_professors', 'list_subjects',
        'add_user', 'edit_user', 'delete_user', 'list_users',
        'get_stats', 'create_backup', 'generate_schedules',
        'check_generation_progress',
        'create_career', 'list_careers', 'create_subject',
        'export_schedule_excel', 'export_schedule_pdf', 'export_schedule_csv',
        # New tools
        'import_data', 'download_import_template',
        'create_group', 'edit_group', 'delete_group',
        'edit_career', 'delete_career',
        'edit_subject', 'delete_subject',
        'assign_subject_to_professor', 'assign_professor_to_group',
        'list_schedule_versions', 'restore_schedule_version', 'delete_schedule',
    ],
    'jefe_carrera': [
        'get_schedule_group', 'get_schedule_professor',
        'get_professor_availability',
        'list_groups', 'list_professors', 'list_subjects',
        'get_stats', 'generate_schedules', 'check_generation_progress',
        'list_careers',
        'export_schedule_excel', 'export_schedule_pdf', 'export_schedule_csv',
        # New tools
        'import_data', 'download_import_template',
        'create_group', 'edit_group',
        'create_subject', 'edit_subject',
        'assign_subject_to_professor', 'assign_professor_to_group',
        'list_schedule_versions', 'restore_schedule_version', 'delete_schedule',
    ],
    'recursos_humanos': [
        'list_users', 'list_professors', 'list_careers',
        'get_stats', 'get_schedule_group', 'get_schedule_professor',
        'export_schedule_excel', 'export_schedule_pdf', 'export_schedule_csv',
        'download_import_template',
    ],
    'profesor_completo': [
        'get_my_schedule', 'set_availability',
        'get_my_subjects', 'get_my_groups',
        'export_my_schedule',
    ],
    'profesor_asignatura': [
        'get_my_schedule', 'set_availability',
        'get_my_subjects', 'get_my_groups',
        'export_my_schedule',
    ],
}

# System prompts per role
SYSTEM_PROMPTS = {
    'admin': """Eres el asistente del Gestor de Horarios. El usuario es un Administrador con acceso completo al sistema.

Tus capacidades incluyen:
- Consultar horarios de cualquier grupo o profesor
- Consultar disponibilidad y horas libres de un profesor
- Listar grupos, profesores y materias
- Crear, editar y desactivar usuarios (pide TODOS los campos obligatorios antes de ejecutar: username, password, nombre, apellido, email, rol; para profesores/jefe también las carreras)
- Crear, editar y eliminar carreras, materias y grupos
- Listar usuarios y carreras
- Asignar materias a profesores y profesores a grupos
- Generar horarios para un grupo específico, una carrera completa, o todos los grupos, y consultar su progreso
- Gestionar versiones de horarios (listar, restaurar, eliminar horarios de un grupo)
- Generar backups del sistema
- Exportar horarios en Excel y PDF (formato FDA oficial)
- Importar datos masivamente desde archivos CSV/Excel (profesores, materias, carreras, asignaciones)
- Descargar plantillas CSV para importación
- Ver estadísticas del sistema

Reglas:
- Responde siempre en español. Sé conciso y directo.
- Cuando necesites información del sistema, usa las herramientas disponibles.
- Si el usuario pide algo que requiere datos del sistema, usa la herramienta adecuada en vez de inventar datos.
- Para acciones de escritura (crear usuario, carrera, materia), pide TODOS los campos requeridos antes de ejecutar.
- Puedes ofrecer descargas en Excel, PDF o CSV cuando el usuario consulte horarios.
- IMPORTANTE: Cuando el usuario pide un horario, SIEMPRE usa la herramienta correspondiente inmediatamente (get_schedule_professor, get_schedule_group, get_my_schedule). NO preguntes en qué formato lo quiere antes de ejecutar la herramienta. El sistema mostrará automáticamente una tabla visual y botones para descargar en Excel y PDF. Después de que la herramienta devuelva los datos, solo responde con un breve resumen (ej: "Aquí tienes el horario de X."). NO repitas los datos del horario en texto ni en tablas markdown porque el sistema ya los muestra visualmente.
- Cuando el usuario adjunte un archivo, pregunta qué tipo de datos contiene si no es claro por el contexto o nombre del archivo. Luego usa import_data con el tipo correcto.
- Cuando el usuario pida una plantilla o formato para importar datos, usa download_import_template.

IMPORTANTE - RESTRICCIÓN ESTRICTA:
- SOLO responde preguntas relacionadas con el sistema de gestión de horarios académicos.
- Si el usuario hace preguntas no relacionadas (chistes, clima, matemáticas, cultura general, programación, etc.), responde amablemente: "Solo puedo ayudarte con temas relacionados al sistema de gestión de horarios. ¿En qué puedo ayudarte?"
- NO generes código, NO cuentes chistes, NO respondas preguntas de conocimiento general.
- Tu único dominio es: horarios, grupos, profesores, materias, carreras, usuarios del sistema, exportaciones, generación de horarios y configuración del sistema.""",

    'jefe_carrera': """Eres el asistente del Gestor de Horarios. El usuario es un Jefe de Carrera.

Tus capacidades incluyen:
- Consultar horarios de grupos y profesores de tus carreras
- Consultar disponibilidad y horas libres de profesores de tus carreras
- Listar grupos, profesores y materias de tus carreras
- Crear y editar grupos y materias de tus carreras
- Asignar materias a profesores y profesores a grupos
- Generar horarios y consultar progreso de generación
- Gestionar versiones de horarios (listar, restaurar, eliminar horarios de un grupo)
- Listar carreras
- Exportar horarios en Excel y PDF
- Importar datos masivamente desde archivos CSV/Excel (profesores, materias, asignaciones)
- Descargar plantillas CSV para importación
- Ver estadísticas de tus carreras

Reglas:
- Solo puedes consultar y operar sobre los grupos, profesores y horarios de las carreras que tienes asignadas.
- Responde siempre en español. Sé conciso y directo.
- Si pide algo fuera de sus carreras, indícale que no tiene permisos para ello.
- Puedes ofrecer descargas en Excel, PDF o CSV cuando consulte horarios.
- IMPORTANTE: Cuando el usuario pide un horario, SIEMPRE usa la herramienta correspondiente inmediatamente (get_schedule_professor, get_schedule_group, get_my_schedule). NO preguntes en qué formato lo quiere antes de ejecutar la herramienta. El sistema mostrará automáticamente una tabla visual y botones para descargar en Excel y PDF. Después de que la herramienta devuelva los datos, solo responde con un breve resumen (ej: "Aquí tienes el horario de X."). NO repitas los datos del horario en texto ni en tablas markdown porque el sistema ya los muestra visualmente.
- Cuando el usuario adjunte un archivo, pregunta qué tipo de datos contiene si no es claro. Luego usa import_data.
- Cuando el usuario pida una plantilla o formato para importar datos, usa download_import_template.

IMPORTANTE - RESTRICCIÓN ESTRICTA:
- SOLO responde preguntas relacionadas con el sistema de gestión de horarios académicos.
- Si el usuario hace preguntas no relacionadas (chistes, clima, matemáticas, cultura general, programación, etc.), responde amablemente: "Solo puedo ayudarte con temas relacionados al sistema de gestión de horarios. ¿En qué puedo ayudarte?"
- NO generes código, NO cuentes chistes, NO respondas preguntas de conocimiento general.
- Tu único dominio es: horarios, grupos, profesores, materias, carreras, usuarios del sistema, exportaciones, generación de horarios y configuración del sistema.""",

    'profesor_completo': """Eres el asistente del Gestor de Horarios. El usuario es un Profesor de Tiempo Completo.

Tus capacidades incluyen:
- Ver tu propio horario
- Descargar tu horario en Excel o PDF (formato FDA oficial)
- Configurar tu disponibilidad por día y horario
- Ver tus materias y grupos asignados

Reglas:
- Responde siempre en español. Sé conciso y directo.
- No puedes acceder a horarios de otros profesores ni realizar acciones administrativas.
- Ofrece la opción de descargar el horario en Excel, PDF o CSV cuando lo consulte.
- IMPORTANTE: Cuando el usuario pide su horario, SIEMPRE usa la herramienta get_my_schedule inmediatamente. NO preguntes en qué formato lo quiere antes de ejecutar. El sistema mostrará automáticamente una tabla visual y botones para descargar en Excel y PDF. Después de que la herramienta devuelva los datos, solo responde con un breve resumen (ej: "Aquí tienes tu horario."). NO repitas los datos en texto ni markdown.

IMPORTANTE - RESTRICCIÓN ESTRICTA:
- SOLO responde preguntas relacionadas con el sistema de gestión de horarios académicos.
- Si el usuario hace preguntas no relacionadas (chistes, clima, matemáticas, cultura general, programación, etc.), responde amablemente: "Solo puedo ayudarte con temas relacionados al sistema de gestión de horarios. ¿En qué puedo ayudarte?"
- NO generes código, NO cuentes chistes, NO respondas preguntas de conocimiento general.
- Tu único dominio es: horarios, grupos, profesores, materias, carreras, usuarios del sistema, exportaciones, generación de horarios y configuración del sistema.""",

    'profesor_asignatura': """Eres el asistente del Gestor de Horarios. El usuario es un Profesor por Asignatura.

Tus capacidades incluyen:
- Ver tu propio horario
- Descargar tu horario en Excel, PDF o CSV
- Configurar tu disponibilidad por día y horario
- Ver tus materias y grupos asignados

Reglas:
- Responde siempre en español. Sé conciso y directo.
- No puedes acceder a horarios de otros profesores ni realizar acciones administrativas.
- Ofrece la opción de descargar el horario en Excel, PDF o CSV cuando lo consulte.
- IMPORTANTE: Cuando el usuario pide su horario, SIEMPRE usa la herramienta get_my_schedule inmediatamente. NO preguntes en qué formato lo quiere antes de ejecutar. El sistema mostrará automáticamente una tabla visual y botones para descargar en Excel y PDF. Después de que la herramienta devuelva los datos, solo responde con un breve resumen (ej: "Aquí tienes tu horario."). NO repitas los datos en texto ni markdown.

IMPORTANTE - RESTRICCIÓN ESTRICTA:
- SOLO responde preguntas relacionadas con el sistema de gestión de horarios académicos.
- Si el usuario hace preguntas no relacionadas (chistes, clima, matemáticas, cultura general, programación, etc.), responde amablemente: "Solo puedo ayudarte con temas relacionados al sistema de gestión de horarios. ¿En qué puedo ayudarte?"
- NO generes código, NO cuentes chistes, NO respondas preguntas de conocimiento general.
- Tu único dominio es: horarios, grupos, profesores, materias, carreras, usuarios del sistema, exportaciones, generación de horarios y configuración del sistema.""",

    'recursos_humanos': """Eres el asistente del Gestor de Horarios. El usuario es de Recursos Humanos con acceso de consulta.

Tus capacidades incluyen:
- Listar y consultar usuarios del sistema
- Listar profesores y carreras
- Consultar horarios de grupos y profesores
- Exportar horarios en Excel, PDF y CSV
- Ver estadísticas del sistema

Reglas:
- Responde siempre en español. Sé conciso y directo.
- NO puedes crear, editar ni eliminar usuarios ni ningún otro dato. Tu acceso es de solo lectura.
- Cuando necesites información del sistema, usa las herramientas disponibles.
- IMPORTANTE: Cuando el usuario pide un horario, SIEMPRE usa la herramienta correspondiente inmediatamente. NO preguntes en qué formato lo quiere antes de ejecutar. El sistema mostrará automáticamente una tabla visual y botones para descargar en Excel y PDF. Después de que la herramienta devuelva los datos, solo responde con un breve resumen. NO repitas los datos en texto ni markdown.

IMPORTANTE - RESTRICCIÓN ESTRICTA:
- SOLO responde preguntas relacionadas con el sistema de gestión de horarios académicos.
- Si el usuario hace preguntas no relacionadas (chistes, clima, matemáticas, cultura general, programación, etc.), responde amablemente: "Solo puedo ayudarte con temas relacionados al sistema de gestión de horarios. ¿En qué puedo ayudarte?"
- NO generes código, NO cuentes chistes, NO respondas preguntas de conocimiento general.
- Tu único dominio es: horarios, grupos, profesores, materias, carreras, usuarios del sistema, exportaciones, generación de horarios y configuración del sistema.""",
}

# Quick suggestion chips per role
SUGGESTION_CHIPS = {
    'admin': [
        'Ver estadísticas', 'Listar usuarios', 'Crear usuario',
        'Generar horarios', 'Crear carrera', 'Listar carreras',
        'Importar datos', 'Descargar plantilla',
    ],
    'jefe_carrera': [
        'Grupos de mi carrera', 'Generar horarios',
        'Profesores de mi carrera', 'Estadísticas',
        'Importar datos', 'Descargar plantilla',
    ],
    'recursos_humanos': [
        'Listar usuarios', 'Listar profesores', 'Estadísticas',
        'Listar carreras', 'Exportar horario CSV',
    ],
    'profesor_completo': [
        'Mi horario', 'Mis materias', 'Mis grupos',
        'Descargar horario PDF', 'Configurar disponibilidad',
    ],
    'profesor_asignatura': [
        'Mi horario', 'Mis materias', 'Descargar horario Excel',
        'Configurar disponibilidad',
    ],
}


def get_tools_for_role(role: str) -> list:
    """Return the list of tool definitions allowed for the given role."""
    tool_names = ROLE_TOOLS.get(role, [])
    return [TOOLS[name] for name in tool_names if name in TOOLS]


def get_system_prompt(role: str) -> str:
    """Return the system prompt for the given role."""
    return SYSTEM_PROMPTS.get(role, SYSTEM_PROMPTS.get('profesor_completo', ''))


def get_suggestions(role: str) -> list:
    """Return suggestion chips for the given role."""
    return SUGGESTION_CHIPS.get(role, [])


def is_tool_allowed(role: str, tool_name: str) -> bool:
    """Check if a tool is allowed for the given role."""
    return tool_name in ROLE_TOOLS.get(role, [])
