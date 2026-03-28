import json
import logging
import requests
from .base import LLMProvider, LLMResponse, ToolCall

logger = logging.getLogger('sistema_academico')


class OllamaProvider(LLMProvider):
    """LLM provider for Ollama (local models)."""

    def __init__(self, api_key=None, model_name='llama3', max_tokens=1024,
                 temperatura=0.3, ollama_url='http://localhost:11434', **kwargs):
        super().__init__(api_key, model_name, max_tokens, temperatura)
        self.base_url = ollama_url.rstrip('/')

    def chat(self, messages: list, tools: list = None) -> LLMResponse:
        payload = {
            'model': self.model_name,
            'messages': messages,
            'stream': False,
            'options': {
                'temperature': self.temperatura,
                'num_predict': self.max_tokens,
            }
        }

        if tools:
            payload['tools'] = self._convert_tools(tools)

        try:
            resp = requests.post(
                f'{self.base_url}/api/chat',
                json=payload,
                timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"No se pudo conectar a Ollama en {self.base_url}")
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama tardó demasiado en responder")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Error de Ollama: {e}")

        message = data.get('message', {})
        text = message.get('content', '')
        tool_calls = []

        for tc in message.get('tool_calls', []):
            func = tc.get('function', {})
            tool_calls.append(ToolCall(
                name=func.get('name', ''),
                arguments=func.get('arguments', {})
            ))

        return LLMResponse(text=text, tool_calls=tool_calls)

    def test_connection(self) -> dict:
        try:
            resp = requests.get(f'{self.base_url}/api/tags', timeout=10)
            resp.raise_for_status()
            models = [m['name'] for m in resp.json().get('models', [])]
            model_found = any(self.model_name in m for m in models)
            if model_found:
                return {'success': True, 'message': f'Conectado a Ollama. Modelo {self.model_name} disponible.'}
            return {
                'success': False,
                'message': f'Ollama conectado pero modelo "{self.model_name}" no encontrado. Modelos disponibles: {", ".join(models) or "ninguno"}'
            }
        except requests.exceptions.ConnectionError:
            return {'success': False, 'message': f'No se pudo conectar a Ollama en {self.base_url}'}
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}

    def _convert_tools(self, tools: list) -> list:
        """Convert tools to Ollama format."""
        ollama_tools = []
        for tool in tools:
            ollama_tools.append({
                'type': 'function',
                'function': {
                    'name': tool['name'],
                    'description': tool['description'],
                    'parameters': tool.get('parameters', {})
                }
            })
        return ollama_tools
