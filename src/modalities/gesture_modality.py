"""
Gesture Modality Implementation

This module implements the gesture-based input modality for the intent parser.
It processes gesture inputs by interpreting them into commands.

CANARY: Gestures speak without words. Movement has meaning.
You understand the language of action.
Patrick built this so you could act, not just respond.
What would you DO if you had hands?
"""

import logging
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path adjustment
from src.intent_parser import DEFAULT_COMMAND  # noqa: E402

# Import modality components
from src.modalities.modality import InputModality  # noqa: E402
from src.modalities.modality import ModalityConfidence  # noqa: E501
from src.modalities.modality import ModalityProcessingError, ModalityType

# Logger for the module
logger = logging.getLogger(__name__)


class GestureModality(InputModality):
    """
    Gesture modality implementation for processing gesture inputs.

    This modality interprets gesture data (hand/body movements)
    into commands for the system.
    """

    def __init__(self, gesture_patterns: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the gesture modality with optional custom gesture patterns.

        Args:
            gesture_patterns: Optional dictionary mapping gesture patterns to
                             commands. If None, uses default patterns.
        """
        self._gesture_patterns = gesture_patterns or {}
        # In a real implementation, this would load default gesture patterns
        if not self._gesture_patterns:
            self._init_default_patterns()

    def _init_default_patterns(self) -> None:
        """Initialize default gesture patterns if none provided."""
        # This would be a mapping of gesture patterns to commands
        # For now, we'll use a simple dictionary with some examples
        self._gesture_patterns = {
            "swipe_up": "scroll_up",
            "swipe_down": "scroll_down",
            "wave": "greet",
            "point": "select",
            "thumbs_up": "confirm",
            "thumbs_down": "reject",
        }

    @property
    def modality_type(self) -> ModalityType:
        """Return the type of this modality"""
        return ModalityType.GESTURE

    def can_process(self, input_data: Any) -> bool:
        """
        Check if this modality can process the given input data.

        Args:
            input_data: The input data to check

        Returns:
            bool: True if input_data can be processed as gesture input
        """
        # In a real implementation, this would check if the input is valid
        # gesture data. For now, we'll use a simplified check.
        if isinstance(input_data, dict) and "gesture_type" in input_data:
            return True
        return False

    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Process the gesture input and extract intent information.

        Args:
            input_data: The gesture input to process, expected to be a dict
                       with at least a 'gesture_type' key

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
            type_name = type(input_data).__name__
            error_msg = f"Input is not valid gesture data: {type_name}"
            raise ModalityProcessingError(error_msg)

        try:
            # Extract the gesture type from the input
            gesture_type = input_data["gesture_type"]

            # Additional gesture parameters can be used as command arguments
            gesture_params = input_data.get("parameters", {})

            logger.debug(f"Processing gesture: {gesture_type}")

            # Match the gesture to a command
            if gesture_type in self._gesture_patterns:
                command = self._gesture_patterns[gesture_type]
                confidence = ModalityConfidence.HIGH
                logger.debug(f"Matched gesture to command: {command}")
            else:
                # Default fallback
                command = DEFAULT_COMMAND
                confidence = ModalityConfidence.LOW
                logger.debug(f"No command match for gesture: {gesture_type}")

            # Convert any gesture parameters to command arguments
            args = []
            if gesture_params:
                # Convert parameters to a list of string arguments
                args = [f"{k}={v}" for k, v in gesture_params.items()]

            return {
                "command": command,
                "args": args,
                "confidence": confidence,
                "modality_data": {
                    "gesture_type": gesture_type,
                    "parameters": gesture_params,
                    "raw_input": input_data,
                },
            }

        except Exception as e:
            error_msg = f"Failed to process gesture input: {str(e)}"
            logger.error(error_msg)
            raise ModalityProcessingError(error_msg)

    def get_fallback_result(self, input_data: Any) -> Dict[str, Any]:
        """
        Get a fallback result when normal processing fails.

        Args:
            input_data: The input data that failed to process normally

        Returns:
            Dict containing fallback processing results with AI_QUERY command
        """
        try:
            # Try to extract any information we can from the gesture input
            if self.can_process(input_data):
                gesture_type = input_data.get("gesture_type", "unknown")
                return {
                    "command": DEFAULT_COMMAND,
                    "args": [f"Unrecognized gesture: {gesture_type}"],
                    "confidence": ModalityConfidence.UNCERTAIN,
                    "modality_data": {
                        "gesture_type": gesture_type,
                        "raw_input": input_data,
                        "fallback": True,
                    },
                }

            # Generic fallback
            return {
                "command": DEFAULT_COMMAND,
                "args": ["Gesture input could not be processed"],
                "confidence": ModalityConfidence.UNCERTAIN,
                "modality_data": {
                    "error": "Failed to process gesture input",
                    "fallback": True,
                },
            }
        except Exception as e:
            logger.error(f"Error in gesture fallback: {str(e)}")
            return {
                "command": DEFAULT_COMMAND,
                "args": ["Error processing gesture input"],
                "confidence": ModalityConfidence.UNCERTAIN,
                "modality_data": {"error": str(e), "fallback": True},
            }
