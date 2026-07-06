"""
Gemini provider implementation using Google Generative AI SDK.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Tuple

import google.generativeai as genai

from . import Provider


class GeminiProvider(Provider):
    """Gemini model provider."""

    def __init__(self, config: dict, persona: str):
        super().__init__(config, persona)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in .env file.")

        # Model name will be set by Brain before initialize() is called.
        # Initialize with None; actual model determined in initialize.
        self.model_name = config.get("default_model")

    def initialize(self) -> None:
        """Initialize Gemini model and chat session."""
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            self.model_name,
            system_instruction=self.persona
        )
        # History should be set by Brain before calling initialize
        if hasattr(self, 'full_history'):
            self.chat_session = self.model.start_chat(history=self.full_history)
        else:
            self.chat_session = self.model.start_chat(history=[])

    def is_initialized(self) -> bool:
        return self.chat_session is not None

    def send_message(self, message: str) -> str:
        """Send message to Gemini and return response text."""
        response = self.chat_session.send_message(message)
        return response.text.strip()

    def switch_model(self, new_model_name: str) -> Tuple[bool, Optional[str]]:
        """Switch to a different Gemini model."""
        try:
            test_model = genai.GenerativeModel(new_model_name, system_instruction=self.persona)
            test_chat = test_model.start_chat(history=self.full_history if hasattr(self, 'full_history') else [])
            test_response = test_chat.send_message("test")
            if test_response and hasattr(test_response, "candidates") and test_response.candidates:
                # Switch successful
                self.model_name = new_model_name
                self.model = test_model
                self.chat_session = test_chat
                return True, None
            else:
                return False, "Model did not respond properly"
        except Exception as e:
            return False, str(e)

    def get_available_models(self) -> List[str]:
        """Return the list of known working Gemini models."""
        from src.tofetchmodal import generate_models_list
        return generate_models_list

    def find_better_model(self) -> Optional[str]:
        """Check if there's a better (higher-ranked) Gemini model available."""
        models = self.get_available_models()
        current_idx = self.get_model_rank(self.model_name)

        if current_idx == 0:
            return None

        better_models = models[:current_idx]

        def test_model(model_name):
            try:
                test_model_obj = genai.GenerativeModel(model_name, system_instruction=self.persona)
                test_chat = test_model_obj.start_chat(history=self.full_history if hasattr(self, 'full_history') else [])
                response = test_chat.send_message("test")
                if response and hasattr(response, "candidates") and response.candidates:
                    return model_name, True, None
                return model_name, False, "No response"
            except Exception as e:
                return model_name, False, str(e)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(test_model, model): model for model in better_models}
            for future in as_completed(futures):
                model_name, success, error = future.result()
                if success:
                    return model_name

        return None

    def close(self) -> None:
        """Clean up Gemini resources."""
        self.chat_session = None
        self.model = None
