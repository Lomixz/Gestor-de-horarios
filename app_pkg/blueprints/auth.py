"""
Authentication blueprint: login, register, logout, password change.

NOTE: During transition, these routes still exist in app.py as well.
This blueprint is intended for use with the new create_app() factory.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger('sistema_academico')
audit_logger = logging.getLogger('audit')


@auth_bp.route('/')
def index():
    return render_template('index.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    from forms import LoginForm
    from models import User

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            if user.activo:
                login_user(user)
                audit_logger.info(f"LOGIN_SUCCESS user={user.username} ip={request.remote_addr}")

                if user.requiere_cambio_password:
                    flash(f'Bienvenido, {user.get_nombre_completo()}. Por seguridad, debes cambiar tu contraseña temporal.', 'warning')
                    return redirect(url_for('auth.cambiar_password_obligatorio'))

                flash(f'¡Bienvenido, {user.get_nombre_completo()}!', 'success')

                next_page = request.args.get('next')
                if next_page and urlparse(next_page).netloc == '' and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('auth.dashboard'))
            else:
                audit_logger.warning(f"LOGIN_DISABLED user={user.username} ip={request.remote_addr}")
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
        else:
            audit_logger.warning(f"LOGIN_FAILED user={form.username.data} ip={request.remote_addr}")
            flash('Usuario o contraseña incorrectos.', 'error')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    audit_logger.info(f"LOGOUT user={current_user.username}")
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.index'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    # Import here to avoid circular imports during transition
    # This is a placeholder - actual dashboard logic remains in app.py
    return redirect(url_for('dashboard'))
