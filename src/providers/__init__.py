"""
Provider abstraction layer for different AI model backends.

Each provider implements the common interface for:
- Model initialization
- Sending messages
- Switching models
- Checking model availability
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple


class Provider(ABC):
    """Abstract base class for AI model providers."""

    def __init__(self, config: dict, persona: str):
        """
        Initialize provider with configuration.

        Args:
            config: Full application config dict
            persona: System instruction / personality
        """
        self.config = config
        self.persona = persona
        self.model_name: Optional[str] = None
        self.model = None
        self.chat_session = None
        self.history = []  # Optional: provider-specific history tracking

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the model. Must set self.model_name, self.model, self.chat_session."""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if model is ready to use."""
        pass

    @abstractmethod
    def send_message(self, message: str) -> str:
        """
        Send a message and get response.

        Returns:
            Response text from the model
        Raises:
            Exception on failure
        """
        pass

    @abstractmethod
    def switch_model(self, new_model_name: str) -> Tuple[bool, Optional[str]]:
        """
        Switch to a different model.

        Returns:
            (success, error_message)
        """
        pass

    def get_available_models(self) -> List[str]:
        """
        Return list of available model names for this provider.
        Default implementation returns empty list - override if provider has known models.
        """
        return []

    def get_model_rank(self, model_name: str) -> int:
        """
        Get ranking index for a model (0 = highest priority).
        Default assumes all models equal rank.
        """
        models = self.get_available_models()
        try:
            return models.index(model_name)
        except ValueError:
            return len(models)

    def find_better_model(self) -> Optional[str]:
        """
        Check if there's a better (higher-ranked) available model.
        Default: returns None (no auto-upgrade).
        Override if provider has model ranking.
        """
        return None

    def close(self) -> None:
        """Clean up resources if needed."""
        pass
