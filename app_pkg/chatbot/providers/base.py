from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: Optional[str], model_name: str,
                 max_tokens: int = 1024, temperatura: float = 0.3, **kwargs):
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperatura = temperatura

    @abstractmethod
    def chat(self, messages: list, tools: list = None) -> LLMResponse:
        """Send messages to the LLM and return a normalized response."""
        pass

    @abstractmethod
    def test_connection(self) -> dict:
        """Test connectivity. Returns {'success': bool, 'message': str}."""
        pass
