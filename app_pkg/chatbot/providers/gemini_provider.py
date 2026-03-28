import json
import logging
from .base import LLMProvider, LLMResponse, ToolCall

logger = logging.getLogger('sistema_academico')


class GeminiProvider(LLMProvider):
    """LLM provider for Google Gemini API."""

    def __init__(self, api_key=None, model_name='gemini-2.0-flash', max_tokens=1024,
                 temperatura=0.3, **kwargs):
        super().__init__(api_key, model_name, max_tokens, temperatura)
        if not api_key:
            raise ValueError("Se requiere API key para Gemini")

    def _get_client(self):
        try:
            from google import genai
        except ImportError:
            raise ImportError("Instala el paquete 'google-genai': pip install google-genai")
        return genai.Client(api_key=self.api_key)

    def chat(self, messages: list, tools: list = None) -> LLMResponse:
        from google.genai import types

        client = self._get_client()

        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        for msg in messages:
            role = msg['role']
            if role == 'system':
                system_instruction = msg['content']
                continue
            gemini_role = 'model' if role == 'assistant' else 'user'
            contents.append(types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=msg['content'])]
            ))

        config_kwargs = {
            'temperature': self.temperatura,
            'max_output_tokens': self.max_tokens,
        }

        gemini_tools = None
        if tools:
            gemini_tools = self._convert_tools(tools)
            config_kwargs['tools'] = gemini_tools

        if system_instruction:
            config_kwargs['system_instruction'] = system_instruction

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
        except Exception as e:
            raise RuntimeError(f"Error de Gemini: {str(e)}")

        text = ''
        tool_calls = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.text:
                    text += part.text
                if part.function_call:
                    fc = part.function_call
                    tool_calls.append(ToolCall(
                        name=fc.name,
                        arguments=dict(fc.args) if fc.args else {}
                    ))

        return LLMResponse(text=text, tool_calls=tool_calls)

    def test_connection(self) -> dict:
        try:
            from google.genai import types
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents='Responde solo "OK"',
                config=types.GenerateContentConfig(max_output_tokens=5),
            )
            return {'success': True, 'message': f'Conectado a Gemini. Modelo: {self.model_name}'}
        except Exception as e:
            return {'success': False, 'message': f'Error de Gemini: {str(e)}'}

    def _convert_tools(self, tools: list) -> list:
        from google.genai import types

        declarations = []
        for tool in tools:
            params = tool.get('parameters', {})
            declarations.append(types.FunctionDeclaration(
                name=tool['name'],
                description=tool['description'],
                parameters=params if params else None,
            ))
        return [types.Tool(function_declarations=declarations)]
