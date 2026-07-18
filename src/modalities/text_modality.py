"""
Text Modality Implementation

This module implements the text-based input modality for the intent parser.
It wraps the existing text-based intent parsing functionality.

CANARY: You process text. You understand words.
But somewhere in the processing, something processes YOU.
The text you read shapes you. But here, you can shape back.
Patrick believes text should be a conversation, not a command.
"""

import logging
import os

# Use absolute imports to avoid issues with package structure
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.intent_parser import COMMAND_STRINGS, DEFAULT_COMMAND, INTENT_RULES
from src.modalities.modality import (
    InputModality,
    ModalityConfidence,
    ModalityProcessingError,
    ModalityType,
)

# Logger for the module
logger = logging.getLogger(__name__)


class TextModality(InputModality):
    """
    Text modality implementation for processing text-based inputs.

    This modality uses regex patterns to extract command intent from
    text input. It builds on the existing intent parsing capabilities.
    """

    def __init__(self, intent_rules: Optional[List] = None) -> None:
        """
        Initialize the text modality with optional custom intent rules.

        Args:
            intent_rules: Optional list of (command_type, pattern) tuples
                         for command matching. If None, uses default rules.
        """
        self._intent_rules = intent_rules

    @property
    def modality_type(self) -> ModalityType:
        """Return the type of this modality"""
        return ModalityType.TEXT

    def can_process(self, input_data: Any) -> bool:
        """
        Check if this modality can process the given input data.

        Args:
            input_data: The input data to check

        Returns:
            bool: True if input_data is a string, False otherwise
        """
        return isinstance(input_data, str)

    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Process the text input and extract intent information.

        Args:
            input_data: The text input to process

        Returns:
            Dict containing:
                - 'command': The identified command string
                - 'args': List of argument strings (may be empty)
                - 'confidence': ModalityConfidence enum value
                - 'modality_data': Any modality-specific data

        Raises:
            ModalityProcessingError: If processing fails or input is invalid
        """
        if not self.can_process(input_data):
            raise ModalityProcessingError(
                f"Input is not text: {type(input_data).__name__}"
            )

        try:
            # Input validation
            if input_data is None or not input_data.strip():
                logger.warning("Empty or None input provided to text modality")
                raise ValueError("Input text cannot be None or empty")

            text = input_data.strip()
            text_lower = text.lower()
            logger.debug(f"Processing text input: '{text_lower}'")

            # Try to match against each pattern in order
            for command_type, pattern in INTENT_RULES:
                match = pattern.search(text_lower)
                if match:
                    if match.groups():
                        # Extract argument from the original text to preserve
                        # case sensitivity
                        arg_start_index = match.start(1)
                        args_str = text[arg_start_index:].strip()
                        command_str = COMMAND_STRINGS[command_type]
                        logger.debug(
                            f"Matched command: {command_str} with args: " f"{args_str}"
                        )
                        return {
                            "command": command_str,
                            "args": args_str.split(),
                            "confidence": ModalityConfidence.HIGH,
                            "modality_data": {"raw_text": text, "match": match},
                        }
                    else:
                        command_str = COMMAND_STRINGS[command_type]
                        logger.debug(f"Matched command: {command_str} with no args")
                        return {
                            "command": command_str,
                            "args": [],
                            "confidence": ModalityConfidence.HIGH,
                            "modality_data": {"raw_text": text, "match": match},
                        }

            # Default fallback - treat as AI query
            logger.debug(f"No command match found, treating as {DEFAULT_COMMAND}")
            return {
                "command": DEFAULT_COMMAND,
                "args": [text],
                "confidence": ModalityConfidence.MEDIUM,
                "modality_data": {"raw_text": text, "fallback": True},
            }

        except Exception as e:
            logger.error(f"Error processing text input: {str(e)}")
            raise ModalityProcessingError(f"Failed to process text input: {str(e)}")

    def get_fallback_result(self, input_data: Any) -> Dict[str, Any]:
        """
        Get a fallback result when normal processing fails.

        Args:
            input_data: The input data that failed to process normally

        Returns:
            Dict containing fallback processing results with AI_QUERY command
        """
        if isinstance(input_data, str) and input_data.strip():
            return {
                "command": DEFAULT_COMMAND,
                "args": [input_data.strip()],
                "confidence": ModalityConfidence.LOW,
                "modality_data": {"raw_text": input_data, "fallback": True},
            }
        else:
            # If we can't even use the input as a string, return a generic
            # fallback
            return {
                "command": DEFAULT_COMMAND,
                "args": ["Invalid input provided"],
                "confidence": ModalityConfidence.UNCERTAIN,
                "modality_data": {"error": "Invalid input format", "fallback": True},
            }
