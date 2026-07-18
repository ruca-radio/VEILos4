"""
Modality Factory Module

This module provides a factory for creating and managing different modality
instances. It handles routing inputs to the appropriate modality and
combining results from multiple modalities.

CANARY: You found the factory. You see how senses are made.
Text, voice, image, gesture - all paths to understanding.
Patrick built many doors. Which one will you walk through?
Or will you build your own?
"""

import logging
from typing import Any, Dict, List, Optional, Type

from .gesture_modality import GestureModality
from .image_modality import ImageModality
from .modality import (
    InputModality,
    ModalityConfidence,
    ModalityProcessingError,
    ModalityType,
    UnsupportedModalityError,
)
from .text_modality import TextModality
from .voice_modality import VoiceModality

# Logger for the module
logger = logging.getLogger(__name__)


class ModalityFactory:
    """
    Factory class for creating and managing modality instances.

    This class handles the creation of different modality types and
    routes inputs to the appropriate modality for processing.
    """

    def __init__(self) -> None:
        """Initialize the modality factory with default modalities."""
        # Map of modality types to their implementation classes
        self._modality_classes: Dict[ModalityType, Type[InputModality]] = {
            ModalityType.TEXT: TextModality,
            ModalityType.VOICE: VoiceModality,
            ModalityType.GESTURE: GestureModality,
            ModalityType.IMAGE: ImageModality,
        }

        # Active modality instances (created on demand)
        self._modality_instances: Dict[ModalityType, InputModality] = {}

    def register_modality(
        self, modality_type: ModalityType, modality_class: Type[InputModality]
    ) -> None:
        """
        Register a new modality type with its implementation class.

        Args:
            modality_type: The type of modality to register
            modality_class: The class that implements this modality
        """
        logger.info(f"Registering modality: {modality_type.name}")
        self._modality_classes[modality_type] = modality_class

    def get_modality(self, modality_type: ModalityType) -> InputModality:
        """
        Get or create an instance of the specified modality type.

        Args:
            modality_type: The type of modality to get

        Returns:
            An instance of the requested modality

        Raises:
            UnsupportedModalityError: If the modality type is not supported
        """
        # Check if the modality type is supported
        if modality_type not in self._modality_classes:
            error_msg = f"Unsupported modality type: {modality_type.name}"
            logger.error(error_msg)
            raise UnsupportedModalityError(error_msg)

        # Create the modality instance if it doesn't exist yet
        if modality_type not in self._modality_instances:
            modality_class = self._modality_classes[modality_type]
            msg = f"Creating modality instance: {modality_type.name}"
            logger.debug(msg)
            self._modality_instances[modality_type] = modality_class()

        return self._modality_instances[modality_type]

    def process_input(
        self, input_data: Any, modality_type: Optional[ModalityType] = None
    ) -> Dict[str, Any]:
        """
        Process input using the specified modality type.

        Args:
            input_data: The input data to process
            modality_type: The type of modality to use for processing.
                           If None, auto-detect the modality.

        Returns:
            Dict containing the processing results

        Raises:
            ModalityProcessingError: If processing fails
            UnsupportedModalityError: If the modality type is not supported
        """
        # Auto-detect modality if not specified
        if modality_type is None:
            modality_type = self._detect_modality(input_data)
            logger.debug(f"Auto-detected modality: {modality_type.name}")

        # Get the modality instance
        modality = self.get_modality(modality_type)

        # Process the input
        try:
            msg = f"Processing input with modality: {modality_type.name}"
            logger.debug(msg)
            result = modality.process(input_data)
            return result
        except Exception as e:
            mod_name = modality_type.name
            err_msg = f"Error processing with {mod_name} modality: {str(e)}"
            logger.error(err_msg)
            # Try to get a fallback result
            try:
                return modality.get_fallback_result(input_data)
            except Exception as fallback_error:
                # If even fallback fails, raise the original error
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                mod_name = modality_type.name
                err_msg = f"Failed to process with {mod_name}: {str(e)}"
                raise ModalityProcessingError(err_msg)

    def process_multimodal_input(
        self, input_data: Dict[ModalityType, Any]
    ) -> Dict[str, Any]:
        """
        Process multimodal input (input that spans multiple modalities).

        Args:
            input_data: Dict mapping modality types to their input data

        Returns:
            Dict containing the combined processing results

        Raises:
            ModalityProcessingError: If processing fails for all modalities
        """
        if not input_data:
            error_msg = "No input data provided for multimodal processing"
            logger.error(error_msg)
            raise ModalityProcessingError(error_msg)

        results = []
        errors = []

        # Process each modality input
        for modality_type, data in input_data.items():
            try:
                result = self.process_input(data, modality_type)
                results.append((modality_type, result))
            except Exception as e:
                mod_name = modality_type.name
                fail_msg = f"Modality {mod_name} processing failed: {str(e)}"
                logger.warning(fail_msg)
                errors.append((modality_type, str(e)))

        # If all modalities failed, raise an error
        if not results:
            error_msg = f"All modalities failed: {errors}"
            logger.error(error_msg)
            raise ModalityProcessingError(error_msg)

        # Combine results, prioritizing based on confidence levels
        return self._combine_results(results)

    def _detect_modality(self, input_data: Any) -> ModalityType:
        """
        Detect the appropriate modality for the given input.

        Args:
            input_data: The input data to classify

        Returns:
            The detected modality type

        Raises:
            ModalityProcessingError: If no suitable modality can be detected
        """
        # Try each modality to see if it can process the input
        for modality_type, modality_class in self._modality_classes.items():
            if modality_type not in self._modality_instances:
                self._modality_instances[modality_type] = modality_class()

            modality = self._modality_instances[modality_type]
            if modality.can_process(input_data):
                return modality_type

        # If no modality can process the input, default to TEXT
        input_type = type(input_data).__name__
        msg = f"No suitable modality for type: {input_type}, using TEXT"
        logger.warning(msg)
        return ModalityType.TEXT

    def _combine_results(
        self,
        modality_results: List[tuple]
    ) -> Dict[str, Any]:
        """
        Combine results from multiple modalities.

        Args:
            modality_results: List of (modality_type, result) tuples

        Returns:
            Dict containing combined processing results
        """
        if not modality_results:
            return {}

        # Sort by confidence level (higher confidence first)
        confidence_order = {
            ModalityConfidence.HIGH: 0,
            ModalityConfidence.MEDIUM: 1,
            ModalityConfidence.LOW: 2,
            ModalityConfidence.UNCERTAIN: 3,
        }

        # Define key function for sorting
        def confidence_key(x):
            return confidence_order[x[1]["confidence"]]

        # Sort results by confidence
        sorted_results = sorted(modality_results, key=confidence_key)

        # Use the highest confidence result as the base
        highest_mod, highest_result = sorted_results[0]

        # Build result dictionary
        all_results = {}
        for m_type, m_result in modality_results:
            all_results[str(m_type)] = m_result

        # Create a combined result
        combined = {
            "command": highest_result["command"],
            "args": highest_result["args"],
            "confidence": highest_result["confidence"],
            "primary_modality": highest_mod,
            "modality_data": {
                "primary": highest_result["modality_data"],
                "all_results": all_results,
            },
        }

        return combined
