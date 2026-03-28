#!/usr/bin/env python3
"""
Script de inicialización del sistema de configuración y backups
Ejecutar una vez para configurar las tablas necesarias
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def init_config_system():
    """Inicializar sistema de configuración y backups"""
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(basedir, "instance", "sistema_academico.db")}'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 5,
            'pool_pre_ping': True,
        }

    # Importar db desde models (igual que en app.py)
    from models import db, ConfiguracionSistema, BackupHistory

    # Inicializar db con la app (igual que en app.py)
    db.init_app(app)

    with app.app_context():
        # Crear tablas
        print("🔧 Creando tablas del sistema de configuración...")
        db.create_all()

        # Configuraciones por defecto
        configs_por_defecto = [
            # Configuración de base de datos
            {'clave': 'db_type', 'valor': 'sqlite', 'tipo': 'string', 'descripcion': 'Tipo de base de datos', 'categoria': 'database'},
            {'clave': 'sqlite_path', 'valor': 'instance/sistema_academico.db', 'tipo': 'string', 'descripcion': 'Ruta del archivo SQLite', 'categoria': 'database'},

            # Configuración de backups
            {'clave': 'backup_frequency', 'valor': 'daily', 'tipo': 'string', 'descripcion': 'Frecuencia de backup automático', 'categoria': 'backup'},
            {'clave': 'backup_retention', 'valor': '30', 'tipo': 'int', 'descripcion': 'Días de retención de backups', 'categoria': 'backup'},
            {'clave': 'backup_location', 'valor': 'backups/', 'tipo': 'string', 'descripcion': 'Ubicación de backups', 'categoria': 'backup'},

            # Configuración general del sistema
            {'clave': 'system_name', 'valor': 'Sistema Académico', 'tipo': 'string', 'descripcion': 'Nombre del sistema', 'categoria': 'general'},
            {'clave': 'system_version', 'valor': '2.0.0', 'tipo': 'string', 'descripcion': 'Versión del sistema', 'categoria': 'general'},
            {'clave': 'admin_email', 'valor': 'admin@sistemaacademico.com', 'tipo': 'string', 'descripcion': 'Email de administración', 'categoria': 'general'},
            {'clave': 'contact_phone', 'valor': '+52 55 1234 5678', 'tipo': 'string', 'descripcion': 'Teléfono de contacto', 'categoria': 'general'},

            # Configuración de seguridad
            {'clave': 'password_min_length', 'valor': '8', 'tipo': 'int', 'descripcion': 'Longitud mínima de contraseña', 'categoria': 'security'},
            {'clave': 'max_login_attempts', 'valor': '5', 'tipo': 'int', 'descripcion': 'Intentos máximos de login', 'categoria': 'security'},
            {'clave': 'session_timeout', 'valor': '60', 'tipo': 'int', 'descripcion': 'Tiempo de sesión en minutos', 'categoria': 'security'},
            {'clave': 'password_change_days', 'valor': '60', 'tipo': 'int', 'descripcion': 'Días para cambio de contraseña', 'categoria': 'security'},

            # Configuración de horarios
            {'clave': 'max_hours_per_day', 'valor': '8', 'tipo': 'int', 'descripcion': 'Horas máximas por día', 'categoria': 'schedule'},
            {'clave': 'class_days_per_week', 'valor': '5', 'tipo': 'int', 'descripcion': 'Días de clase por semana', 'categoria': 'schedule'},
            {'clave': 'class_duration', 'valor': '50', 'tipo': 'int', 'descripcion': 'Duración de clase en minutos', 'categoria': 'schedule'},
            {'clave': 'break_between_classes', 'valor': '10', 'tipo': 'int', 'descripcion': 'Tiempo entre clases en minutos', 'categoria': 'schedule'},

            # Configuración de disponibilidad
            {'clave': 'require_explicit_availability', 'valor': 'false', 'tipo': 'bool', 'descripcion': 'Requerir disponibilidad explícita de profesores (si false, se asume disponibilidad completa)', 'categoria': 'schedule'},
        ]

        print("📝 Configurando valores por defecto...")
        for config_data in configs_por_defecto:
            config = ConfiguracionSistema.query.filter_by(clave=config_data['clave']).first()
            if not config:
                config = ConfiguracionSistema(**config_data)
                db.session.add(config)
                print(f"   ✅ {config_data['clave']}: {config_data['valor']}")
            else:
                print(f"   ⏭️  {config_data['clave']}: ya existe")

        # Crear directorios necesarios
        print("📁 Creando directorios necesarios...")
        dirs = ['backups', 'logs', 'static/uploads', 'static/uploads/perfiles']
        for dir_path in dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"   ✅ {dir_path}")
            else:
                print(f"   ⏭️  {dir_path}: ya existe")

        db.session.commit()
        print("🎉 Sistema de configuración inicializado exitosamente!")
        print()
        print("📋 Próximos pasos:")
        print("   1. Configurar backups automáticos con: python backup_manager.py auto")
        print("   2. Ver estado del sistema con: python backup_manager.py status")
        print("   3. Acceder a la configuración web en: /admin/configuracion")

if __name__ == "__main__":
    init_config_system()