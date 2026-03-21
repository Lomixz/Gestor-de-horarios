import json
import logging
from .base import LLMProvider, LLMResponse, ToolCall

logger = logging.getLogger('sistema_academico')


class ClaudeProvider(LLMProvider):
    """LLM provider for Anthropic Claude API."""

    def __init__(self, api_key=None, model_name='claude-sonnet-4-6', max_tokens=1024,
                 temperatura=0.3, **kwargs):
        super().__init__(api_key, model_name, max_tokens, temperatura)
        if not api_key:
            raise ValueError("Se requiere API key para Claude")

    def _get_client(self):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("Instala el paquete 'anthropic': pip install anthropic")
        return Anthropic(api_key=self.api_key)

    def chat(self, messages: list, tools: list = None) -> LLMResponse:
        client = self._get_client()

        # Extract system prompt
        system = None
        chat_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system = msg['content']
            else:
                chat_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })

        kwargs = {
            'model': self.model_name,
            'messages': chat_messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperatura,
        }

        if system:
            kwargs['system'] = system

        if tools:
            kwargs['tools'] = self._convert_tools(tools)

        try:
            response = client.messages.create(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Error de Claude: {str(e)}")

        text = ''
        tool_calls = []

        for block in response.content:
            if block.type == 'text':
                text += block.text
            elif block.type == 'tool_use':
                tool_calls.append(ToolCall(
                    name=block.name,
                    arguments=block.input if block.input else {}
                ))

        return LLMResponse(text=text, tool_calls=tool_calls)

    def test_connection(self) -> dict:
        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model_name,
                messages=[{'role': 'user', 'content': 'Responde solo "OK"'}],
                max_tokens=5,
            )
            return {'success': True, 'message': f'Conectado a Claude. Modelo: {self.model_name}'}
        except Exception as e:
            return {'success': False, 'message': f'Error de Claude: {str(e)}'}

    def _convert_tools(self, tools: list) -> list:
        claude_tools = []
        for tool in tools:
            claude_tools.append({
                'name': tool['name'],
                'description': tool['description'],
                'input_schema': tool.get('parameters', {'type': 'object', 'properties': {}})
            })
        return claude_tools
