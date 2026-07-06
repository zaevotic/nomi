import os
import json
from typing import Optional, List, Tuple
# pyrefly: ignore [missing-import]
import ollama
from . import Provider


class LocalProvider(Provider):

    def __init__(self, config: dict, persona: str):
        super().__init__(config, persona)
        self.model_name = config.get("default_model", "qwen2.5")
        self.host = os.getenv("OLLAMA_HOST", config.get("ollama_host", "http://localhost:11434"))
        self._client: Optional[ollama.Client] = None
        self._messages: List[dict] = []

    def _get_client(self) -> ollama.Client:
        if self._client is None:
            self._client = ollama.Client(host=self.host)
        return self._client

    def initialize(self) -> None:
        client = self._get_client()

        try:
            available = [m.model for m in client.list().models]
        except Exception as e:
            raise ConnectionError(
                f"Could not connect to Ollama at {self.host}. "
                f"Make sure Ollama is running (`ollama serve`). Error: {e}"
            )

        if self.model_name and not any(self.model_name in m for m in available):
            raise ValueError(
                f"Model '{self.model_name}' not found in Ollama. "
                f"Pull it first with: ollama pull {self.model_name}\n"
                f"Available models: {', '.join(available) or 'none'}"
            )

        self._messages = []

        if self.persona:
            self._messages.append({"role": "system", "content": self.persona})

        # Load saved history — handles both full_history format (parts=[{"text": ...}])
        # and display format (parts=["..."])
        for msg in getattr(self, "full_history", None) or []:
            role = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
            parts = msg.get("parts", [])
            if not parts:
                continue
            raw = parts[0]
            content = raw.get("text", "") if isinstance(raw, dict) else str(raw)
            if content:
                self._messages.append({"role": role, "content": content})

        self.chat_session = True

    def is_initialized(self) -> bool:
        return self.chat_session is not None and self._client is not None

    def send_message(self, message: str) -> str:
        client = self._get_client()
        self._messages.append({"role": "user", "content": message})

        response = client.chat(model=self.model_name, messages=self._messages)
        reply = response.message.content.strip()

        self._messages.append({"role": "assistant", "content": reply})
        return reply

    def switch_model(self, new_model_name: str) -> Tuple[bool, Optional[str]]:
        try:
            client = self._get_client()
            available = [m.model for m in client.list().models]
            if not any(new_model_name in m for m in available):
                return False, f"Model '{new_model_name}' not found locally. Run: ollama pull {new_model_name}"
            self.model_name = new_model_name
            return True, None
        except Exception as e:
            return False, str(e)

    def get_available_models(self) -> List[str]:
        try:
            return [m.model for m in self._get_client().list().models]
        except Exception:
            return ["qwen2.5", "llama3.2", "llama3.1", "mistral", "gemma2", "phi3", "deepseek-r1"]

    def close(self) -> None:
        self.chat_session = None
        self._client = None
        self._messages = []
