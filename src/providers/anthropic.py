"""
Anthropic Claude provider implementation - placeholder for future development.

TODO:
- Implement Anthropic API integration using anthropic package
- Handle authentication via ANTHROPIC_API_KEY
- Support Claude models (claude-3-opus, claude-3-sonnet, claude-3-haiku)
- Handle Anthropic's message format (system as separate parameter)
"""

from typing import Optional, List, Tuple

from . import Provider


class AnthropicProvider(Provider):
    """Anthropic Claude provider."""

    def __init__(self, config: dict, persona: str):
        super().__init__(config, persona)
        self.api_key = None  # Will be loaded from .env: ANTHROPIC_API_KEY
        self.model_name = config.get("default_model", "claude-3-sonnet-20240229")

    def initialize(self) -> None:
        """Initialize Anthropic client."""
        raise NotImplementedError("Anthropic provider not yet implemented")

    def is_initialized(self) -> bool:
        return False

    def send_message(self, message: str) -> str:
        raise NotImplementedError("Anthropic provider not yet implemented")

    def switch_model(self, new_model_name: str) -> Tuple[bool, Optional[str]]:
        self.model_name = new_model_name
        return False, "Not implemented"

    def get_available_models(self) -> List[str]:
        return [
            # List of models...
        ]

    def close(self) -> None:
        pass
