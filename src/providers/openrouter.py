"""
OpenRouter provider implementation - placeholder for future development.

TODO:
- Implement OpenRouter API integration
- Handle authentication via OPENROUTER_API_KEY
- Support model discovery from OpenRouter endpoints
- Implement streaming/non-streaming responses
- Handle provider-specific features (params, pricing, etc)
"""

from typing import Optional, List, Tuple

from . import Provider


class OpenRouterProvider(Provider):
    """OpenRouter provider - allows access to multiple model providers through one API."""

    def __init__(self, config: dict, persona: str):
        super().__init__(config, persona)
        self.api_key = None  # Will be loaded from .env: OPENROUTER_API_KEY
        self.model_name = config.get("default_model")

    def initialize(self) -> None:
        """Initialize OpenRouter client."""
        raise NotImplementedError("OpenRouter provider not yet implemented")

    def is_initialized(self) -> bool:
        return False

    def send_message(self, message: str) -> str:
        raise NotImplementedError("OpenRouter provider not yet implemented")

    def switch_model(self, new_model_name: str) -> Tuple[bool, Optional[str]]:
        # For OpenRouter, any model name that's valid on the platform can be used
        self.model_name = new_model_name
        return False, "Not implemented"

    def get_available_models(self) -> List[str]:
        """Return known OpenRouter model IDs (placeholder)."""
        return [
            # List of models...
        ]

    def close(self) -> None:
        pass
