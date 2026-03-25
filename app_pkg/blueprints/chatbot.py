"""Chatbot blueprint: /api/chatbot/* endpoints."""
import json
import logging
import uuid
import threading
from flask import Blueprint, request, jsonify, send_file, render_template, session as flask_session, current_app
from flask_login import login_required, current_user

from models import db, User, ChatbotConfig
from app_pkg.chatbot.providers import get_provider
from app_pkg.chatbot.tools import (
    get_tools_for_role, get_system_prompt, get_suggestions, is_tool_allowed
)
from app_pkg.chatbot.actions import execute_tool
from app_pkg.chatbot import file_manager

logger = logging.getLogger('sistema_academico')

# Redis-based task store for background chatbot processing
TASK_TTL = 3600  # 1 hour


def _get_redis():
    """Get Redis client, or None if unavailable."""
    try:
        from progress import get_redis_client
        client = get_redis_client()
        client.ping()
        return client
    except Exception:
        return None


def _store_task_result(task_id, status, text='', html=None, download_url=None, download_urls=None):
    """Store a chatbot task result in Redis."""
    r = _get_redis()
    if not r:
        return
    data = json.dumps({
        'status': status,
        'text': text or '',
        'html': html,
        'download_url': download_url,
        'download_urls': download_urls,
    })
    r.setex(f'chatbot_task:{task_id}', TASK_TTL, data)


def _get_task_result(task_id):
    """Retrieve a chatbot task result from Redis."""
    r = _get_redis()
    if not r:
        return None
    data = r.get(f'chatbot_task:{task_id}')
    if data:
        return json.loads(data)
    return None

chatbot_bp = Blueprint('chatbot', __name__)


def _get_user_role(user):
    """Determine the primary role string for tool access."""
    if user.is_admin():
        return 'admin'
    elif user.is_jefe_carrera():
        return 'jefe_carrera'
    elif user.is_recursos_humanos():
        return 'recursos_humanos'
    elif user.rol == 'profesor_completo':
        return 'profesor_completo'
    else:
        return 'profesor_asignatura'


@chatbot_bp.route('/api/chatbot/message', methods=['POST'])
@login_required
def chatbot_message():
    """Process a chat message in background and return a task_id for polling."""
    config = ChatbotConfig.get_config()

    if not config.habilitado:
        return jsonify({'error': 'El chatbot no está habilitado.'}), 403

    data = request.get_json()
    if not data or not data.get('text', '').strip():
        return jsonify({'error': 'Mensaje vacío.'}), 400

    user_text = data['text'].strip()
    history = data.get('history', [])

    # Capture everything needed before spawning thread
    user_id = current_user.id
    role = _get_user_role(current_user)
    system_prompt = get_system_prompt(role)
    tools = get_tools_for_role(role)
    provider_name = config.provider
    provider_kwargs = config.get_provider_kwargs()

    # Build messages
    messages = [{'role': 'system', 'content': system_prompt}]
    for msg in history[-15:]:
        messages.append({
            'role': msg.get('role', 'user'),
            'content': msg.get('content', '')
        })
    messages.append({'role': 'user', 'content': user_text})

    # Generate task_id and store pending status
    task_id = str(uuid.uuid4())
    _store_task_result(task_id, 'pending')

    app = current_app._get_current_object()

    def _process_in_background():
        with app.app_context():
            try:
                is_claude = provider_name == 'claude'
                provider = get_provider(provider_name, **provider_kwargs)
                response = provider.chat(messages, tools=tools if tools else None)

                result_html = None
                download_url = None
                download_urls = None

                # Support up to 5 sequential tool calls
                max_tool_rounds = 5
                round_count = 0

                while response.tool_calls and round_count < max_tool_rounds:
                    round_count += 1
                    tc = response.tool_calls[0]

                    if not is_tool_allowed(role, tc.name):
                        response.text = f'No tienes permisos para ejecutar la acción "{tc.name}".'
                        break

                    user = db.session.get(User, user_id)
                    tool_result = execute_tool(tc.name, tc.arguments, user)

                    tool_result_text = tool_result['text']
                    if tool_result.get('html'):
                        result_html = tool_result['html']
                        # Tell the LLM a visual table is already shown — don't repeat data
                        tool_result_text += '\n[NOTA: El sistema ya muestra una tabla visual con estos datos al usuario. NO repitas los datos en texto ni markdown. Solo da un breve resumen.]'
                    if tool_result.get('download_urls'):
                        download_urls = tool_result['download_urls']
                    elif tool_result.get('download_url'):
                        download_url = tool_result['download_url']

                    # Build follow-up messages with proper format per provider
                    if is_claude and hasattr(response, 'raw_content') and tc.id:
                        # Native Claude tool_use flow
                        messages.append({
                            'role': 'assistant',
                            'content': response.raw_content,
                        })
                        messages.append({
                            'role': 'tool_result',
                            'tool_use_id': tc.id,
                            'content': tool_result_text,
                        })
                    else:
                        # Universal format for OpenAI, Gemini, Ollama
                        messages.append({
                            'role': 'assistant',
                            'content': response.text or f'Ejecutando {tc.name}...'
                        })
                        messages.append({
                            'role': 'user',
                            'content': f'[Resultado de {tc.name}]: {tool_result_text}'
                        })

                    try:
                        # Pass tools so the LLM can chain additional calls
                        response = provider.chat(messages, tools=tools if tools else None)
                    except Exception as e:
                        logger.error(f"Error en llamada LLM (round {round_count}): {e}")
                        response.text = tool_result_text
                        break

                _store_task_result(task_id, 'complete', response.text, result_html, download_url, download_urls)

            except Exception as e:
                logger.error(f"Error en chatbot background: {e}", exc_info=True)
                _store_task_result(task_id, 'error', f'Error del servicio: {str(e)}')

    thread = threading.Thread(target=_process_in_background, daemon=True)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'pending'})


@chatbot_bp.route('/api/chatbot/task/<task_id>')
@login_required
def chatbot_task_status(task_id):
    """Poll for the result of a background chatbot task."""
    result = _get_task_result(task_id)
    if result is None:
        return jsonify({'status': 'pending'})
    return jsonify(result)


@chatbot_bp.route('/api/chatbot/download/<file_id>')
@login_required
def chatbot_download(file_id):
    """Download a file generated by the chatbot."""
    info = file_manager.get_file(file_id, current_user.id)
    if not info:
        return jsonify({'error': 'Archivo no encontrado o expirado.'}), 404

    return send_file(
        info['path'],
        as_attachment=True,
        download_name=info['filename'],
        mimetype=info['mimetype'],
    )


@chatbot_bp.route('/api/chatbot/config', methods=['GET', 'POST'])
@login_required
def chatbot_config():
    """Admin panel for chatbot configuration."""
    if not current_user.is_admin():
        return jsonify({'error': 'Acceso denegado.'}), 403

    if request.method == 'GET':
        return render_template('admin/chatbot_config.html')

    # POST - save config
    data = request.get_json() if request.is_json else request.form
    config = ChatbotConfig.get_config()

    config.provider = data.get('provider', config.provider)
    config.model_name = data.get('model_name', config.model_name)
    config.habilitado = data.get('habilitado', 'false') in (True, 'true', 'on', '1')
    config.max_tokens = int(data.get('max_tokens', config.max_tokens))
    config.temperatura = float(data.get('temperatura', config.temperatura))

    # Only update api_key if provided (don't clear it)
    api_key = data.get('api_key', '').strip()
    if api_key:
        config.api_key = api_key

    ollama_url = data.get('ollama_url', '').strip()
    if ollama_url:
        config.ollama_url = ollama_url

    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': 'Configuración guardada.'})

    from flask import flash, redirect, url_for
    flash('Configuración del chatbot guardada.', 'success')
    return redirect(url_for('chatbot.chatbot_config'))


@chatbot_bp.route('/api/chatbot/test', methods=['POST'])
@login_required
def chatbot_test():
    """Test the LLM connection with current config."""
    if not current_user.is_admin():
        return jsonify({'error': 'Acceso denegado.'}), 403

    config = ChatbotConfig.get_config()

    try:
        provider = get_provider(config.provider, **config.get_provider_kwargs())
        result = provider.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@chatbot_bp.route('/api/chatbot/suggestions')
@login_required
def chatbot_suggestions():
    """Get suggestion chips for the current user's role."""
    role = _get_user_role(current_user)
    return jsonify({'suggestions': get_suggestions(role)})


@chatbot_bp.route('/api/chatbot/status')
@login_required
def chatbot_status():
    """Check if chatbot is enabled. Admins get full config details."""
    config = ChatbotConfig.get_config()
    data = {
        'habilitado': config.habilitado,
        'provider': config.provider,
        'login_token': flask_session.get('chatbot_login_token', ''),
    }
    if current_user.is_admin():
        data.update({
            'model_name': config.model_name,
            'ollama_url': config.ollama_url or 'http://localhost:11434',
            'max_tokens': config.max_tokens,
            'temperatura': config.temperatura,
            'has_api_key': bool(config.api_key),
        })
    return jsonify(data)
