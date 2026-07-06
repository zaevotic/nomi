"""
OpenAI provider implementation - placeholder for future development.

TODO:
- Implement OpenAI API integration using openai package
- Handle authentication via OPENAI_API_KEY
- Support ChatGPT models (gpt-4, gpt-3.5-turbo, etc.)
- Implement streaming and function calling if needed
"""

from typing import Optional, List, Tuple

from . import Provider


class OpenAIProvider(Provider):
    """OpenAI ChatGPT provider."""

    def __init__(self, config: dict, persona: str):
        super().__init__(config, persona)
        self.api_key = None  # Will be loaded from .env: OPENAI_API_KEY
        self.model_name = config.get("default_model", "gpt-3.5-turbo")

    def initialize(self) -> None:
        """Initialize OpenAI client."""
        raise NotImplementedError("OpenAI provider not yet implemented")

    def is_initialized(self) -> bool:
        return False

    def send_message(self, message: str) -> str:
        raise NotImplementedError("OpenAI provider not yet implemented")

    def switch_model(self, new_model_name: str) -> Tuple[bool, Optional[str]]:
        self.model_name = new_model_name
        return False, "Not implemented"

    def get_available_models(self) -> List[str]:
        """Return typical OpenAI model names."""
        return [
            # List of models...
        ]

    def close(self) -> None:
        pass
