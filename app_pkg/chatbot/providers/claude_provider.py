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

        # Extract system prompt and build Claude-native messages
        system = None
        chat_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system = msg['content']
            elif msg['role'] == 'tool_result':
                # Native tool_result block (sent by chatbot blueprint)
                chat_messages.append({
                    'role': 'user',
                    'content': [{
                        'type': 'tool_result',
                        'tool_use_id': msg['tool_use_id'],
                        'content': msg['content'],
                    }]
                })
            elif msg['role'] == 'assistant' and isinstance(msg.get('content'), list):
                # Assistant message with tool_use blocks
                chat_messages.append({
                    'role': 'assistant',
                    'content': msg['content']
                })
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

        # Store raw content blocks for proper tool_use flow
        raw_content = []
        for block in response.content:
            if block.type == 'text':
                text += block.text
                raw_content.append({'type': 'text', 'text': block.text})
            elif block.type == 'tool_use':
                tool_calls.append(ToolCall(
                    name=block.name,
                    arguments=block.input if block.input else {},
                    id=block.id,
                ))
                raw_content.append({
                    'type': 'tool_use',
                    'id': block.id,
                    'name': block.name,
                    'input': block.input if block.input else {},
                })

        resp = LLMResponse(text=text, tool_calls=tool_calls)
        # Attach raw content for building proper follow-up messages
        resp.raw_content = raw_content
        return resp

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
