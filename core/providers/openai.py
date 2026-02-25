"""
VEILos4 Provider: openai
Auto-scaffolded by VEILos4 Scaffold Engine
"""

from typing import Dict, Any, Optional


class OpenaiProvider:
    """Provider for openai"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "openai"

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from openai"""
        raise NotImplementedError("Connect to openai API")

    def get_info(self) -> Dict[str, Any]:
        return {"name": self.name, "config": self.config}
