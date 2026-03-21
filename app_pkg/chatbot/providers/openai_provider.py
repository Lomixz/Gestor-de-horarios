import json
import logging
from .base import LLMProvider, LLMResponse, ToolCall

logger = logging.getLogger('sistema_academico')


class OpenAIProvider(LLMProvider):
    """LLM provider for OpenAI API."""

    def __init__(self, api_key=None, model_name='gpt-4o-mini', max_tokens=1024,
                 temperatura=0.3, **kwargs):
        super().__init__(api_key, model_name, max_tokens, temperatura)
        if not api_key:
            raise ValueError("Se requiere API key para OpenAI")

    def _get_client(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Instala el paquete 'openai': pip install openai")
        return OpenAI(api_key=self.api_key)

    def chat(self, messages: list, tools: list = None) -> LLMResponse:
        client = self._get_client()

        kwargs = {
            'model': self.model_name,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperatura,
        }

        if tools:
            kwargs['tools'] = self._convert_tools(tools)
            kwargs['tool_choice'] = 'auto'

        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Error de OpenAI: {str(e)}")

        message = response.choices[0].message
        text = message.content or ''
        tool_calls = []

        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments) if tc.function.arguments else {}
                ))

        return LLMResponse(text=text, tool_calls=tool_calls)

    def test_connection(self) -> dict:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{'role': 'user', 'content': 'Responde solo "OK"'}],
                max_tokens=5,
            )
            return {'success': True, 'message': f'Conectado a OpenAI. Modelo: {self.model_name}'}
        except Exception as e:
            return {'success': False, 'message': f'Error de OpenAI: {str(e)}'}

    def _convert_tools(self, tools: list) -> list:
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                'type': 'function',
                'function': {
                    'name': tool['name'],
                    'description': tool['description'],
                    'parameters': tool.get('parameters', {})
                }
            })
        return openai_tools
