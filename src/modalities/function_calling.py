"""
Function Calling API Module

This module provides a flexible and secure API for calling internal framework functions
and methods. It supports parameter passing, type checking, validation, return value
handling, and comprehensive logging of all function calls.
"""

import inspect
import logging
import threading
import time
import traceback
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

# Logger for the module
logger = logging.getLogger(__name__)


class FunctionCallError(Exception):
    """Base exception for function call related errors"""

    pass


class FunctionNotFoundError(FunctionCallError):
    """Exception raised when the requested function cannot be found"""

    pass


class ParameterValidationError(FunctionCallError):
    """Exception raised when parameter validation fails"""

    pass


class PermissionDeniedError(FunctionCallError):
    """Exception raised when permission to call a function is denied"""

    pass


class FunctionExecutionError(FunctionCallError):
    """Exception raised when the function execution fails"""

    pass


class FunctionType(Enum):
    """Types of functions that can be called through the API"""

    INTERNAL = auto()  # Internal framework functions
    SYSTEM = auto()  # System-level functions
    USER = auto()  # User-defined functions
    EXTERNAL = auto()  # External library functions
    GENERATED = auto()  # AI-generated functions


class ParameterSpec:
    """
    Specification for a function parameter, including type and validation rules.
    """

    def __init__(
        self,
        name: str,
        param_type: Type = Any,
        required: bool = True,
        default: Any = None,
        validator: Optional[Callable[[Any], bool]] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize a parameter specification.

        Args:
            name: The parameter name
            param_type: The expected type of the parameter
            required: Whether this parameter is required
            default: Default value if not provided
            validator: Optional function to validate parameter value
            description: Human-readable description of the parameter
        """
        self.name = name
        self.param_type = param_type
        self.required = required
        self.default = default
        self.validator = validator
        self.description = description

    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a parameter value against this specification.

        Args:
            value: The value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if required parameter is missing
        if value is None:
            if self.required:
                return False, f"Required parameter '{self.name}' is missing"
            return True, None

        # Type checking
        if self.param_type is not Any and not isinstance(value, self.param_type):
            return (
                False,
                f"Parameter '{self.name}' should be of type {self.param_type.__name__}",
            )

        # Custom validation
        if self.validator is not None:
            try:
                is_valid = self.validator(value)
                if not is_valid:
                    return False, f"Parameter '{self.name}' failed validation"
            except Exception as e:
                return (
                    False,
                    f"Validator for parameter '{self.name}' raised an exception: {str(e)}",
                )

        return True, None


class FunctionSpec:
    """
    Specification for a function, including its parameters and return type.
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        parameters: List[ParameterSpec],
        return_type: Type = Any,
        function_type: FunctionType = FunctionType.INTERNAL,
        description: Optional[str] = None,
        security_level: int = 0,
        is_async: bool = False,
    ):
        """
        Initialize a function specification.

        Args:
            name: The function name
            func: The actual function to call
            parameters: List of parameter specifications
            return_type: Expected return type
            function_type: The type of function
            description: Human-readable description
            security_level: Required security level to call this function
            is_async: Whether this function is asynchronous
        """
        self.name = name
        self.func = func
        self.parameters = parameters
        self.return_type = return_type
        self.function_type = function_type
        self.description = description
        self.security_level = security_level
        self.is_async = is_async

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """
        Validate a set of parameters against this function's specification.

        Args:
            params: Dictionary of parameter names to values

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []

        # Check for required parameters
        for param_spec in self.parameters:
            if param_spec.name in params:
                value = params[param_spec.name]
                is_valid, error = param_spec.validate(value)
                if not is_valid:
                    errors.append(error)
            elif param_spec.required:
                errors.append(f"Required parameter '{param_spec.name}' is missing")

        # Check for unexpected parameters
        param_names = {p.name for p in self.parameters}
        for name in params:
            if name not in param_names:
                errors.append(f"Unexpected parameter '{name}'")

        return errors

    def get_parameter_defaults(self) -> Dict[str, Any]:
        """
        Get default values for all parameters that have defaults.

        Returns:
            Dictionary of parameter names to default values
        """
        return {
            param.name: param.default
            for param in self.parameters
            if not param.required and param.default is not None
        }

    def prepare_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare parameters for function execution, filling in defaults.

        Args:
            params: Dictionary of provided parameter values

        Returns:
            Dictionary with all required parameters, including defaults
        """
        result = self.get_parameter_defaults()
        result.update(params)
        return result


class FunctionCallResult:
    """
    Represents the result of a function call.
    """

    def __init__(
        self,
        function_name: str,
        parameters: Dict[str, Any],
        return_value: Any = None,
        error: Optional[Exception] = None,
        execution_time: float = 0.0,
    ):
        """
        Initialize a function call result.

        Args:
            function_name: Name of the called function
            parameters: Parameters that were passed to the function
            return_value: Value returned by the function (if successful)
            error: Exception raised during execution (if failed)
            execution_time: Time taken to execute the function in seconds
        """
        self.function_name = function_name
        self.parameters = parameters
        self.return_value = return_value
        self.error = error
        self.execution_time = execution_time
        self.timestamp = time.time()
        self.success = error is None

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message if an error occurred."""
        return str(self.error) if self.error else None


class FunctionRegistry:
    """
    Registry for functions that can be called through the API.
    """

    def __init__(self):
        """Initialize the function registry."""
        self._functions: Dict[str, FunctionSpec] = {}
        self._lock = threading.RLock()

    def register_function(self, spec: FunctionSpec) -> None:
        """
        Register a function specification.

        Args:
            spec: The function specification to register
        """
        with self._lock:
            self._functions[spec.name] = spec
            logger.info(f"Registered function: {spec.name} ({spec.function_type.name})")

    def unregister_function(self, name: str) -> bool:
        """
        Unregister a function by name.

        Args:
            name: The name of the function to unregister

        Returns:
            True if the function was found and unregistered, False otherwise
        """
        with self._lock:
            if name in self._functions:
                del self._functions[name]
                logger.info(f"Unregistered function: {name}")
                return True
            return False

    def get_function(self, name: str) -> Optional[FunctionSpec]:
        """
        Get a function specification by name.

        Args:
            name: The name of the function to get

        Returns:
            The function specification, or None if not found
        """
        with self._lock:
            return self._functions.get(name)

    def list_functions(
        self,
        function_type: Optional[FunctionType] = None,
        security_level: Optional[int] = None,
    ) -> List[str]:
        """
        List available functions, optionally filtered by type and security level.

        Args:
            function_type: Optional filter by function type
            security_level: Optional filter by maximum security level

        Returns:
            List of function names
        """
        with self._lock:
            result = []

            for name, spec in self._functions.items():
                if function_type and spec.function_type != function_type:
                    continue

                if security_level is not None and spec.security_level > security_level:
                    continue

                result.append(name)

            return result

    def get_function_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a function.

        Args:
            name: The name of the function

        Returns:
            Dictionary with function details, or None if not found
        """
        with self._lock:
            spec = self._functions.get(name)
            if not spec:
                return None

            param_info = []
            for p in spec.parameters:
                param_info.append(
                    {
                        "name": p.name,
                        "type": p.param_type.__name__,
                        "required": p.required,
                        "has_default": p.default is not None,
                        "description": p.description or "",
                    }
                )

            return {
                "name": spec.name,
                "type": spec.function_type.name,
                "description": spec.description or "",
                "parameters": param_info,
                "return_type": spec.return_type.__name__,
                "security_level": spec.security_level,
                "is_async": spec.is_async,
            }


class FunctionCaller:
    """
    Main interface for calling functions through the API.
    """

    def __init__(
        self, registry: FunctionRegistry, security_context: Optional[Any] = None
    ):
        """
        Initialize a function caller.

        Args:
            registry: The function registry to use
            security_context: Optional security context for permission checks
        """
        self.registry = registry
        self.security_context = security_context
        self._call_history: List[FunctionCallResult] = []
        self._max_history = 1000
        self._lock = threading.RLock()

    def call(
        self,
        function_name: str,
        parameters: Dict[str, Any] = None,
        security_token: Optional[str] = None,
    ) -> FunctionCallResult:
        """
        Call a function by name with the given parameters.

        Args:
            function_name: The name of the function to call
            parameters: Dictionary of parameter values
            security_token: Optional security token for authentication

        Returns:
            FunctionCallResult with the results of the call

        Raises:
            FunctionNotFoundError: If the function does not exist
            ParameterValidationError: If parameter validation fails
            PermissionDeniedError: If permission is denied
            FunctionExecutionError: If the function execution fails
        """
        if parameters is None:
            parameters = {}

        start_time = time.time()

        try:
            # Look up the function
            spec = self.registry.get_function(function_name)
            if not spec:
                raise FunctionNotFoundError(f"Function not found: {function_name}")

            # Check permissions
            if not self._check_permission(spec, security_token):
                raise PermissionDeniedError(
                    f"Permission denied to call function: {function_name}"
                )

            # Validate parameters
            validation_errors = spec.validate_parameters(parameters)
            if validation_errors:
                error_msg = "; ".join(validation_errors)
                raise ParameterValidationError(
                    f"Parameter validation failed: {error_msg}"
                )

            # Prepare parameters with defaults
            prepared_params = spec.prepare_parameters(parameters)

            # Log the call
            logger.debug(
                f"Calling function {function_name} with parameters: {prepared_params}"
            )

            # Execute the function
            try:
                result = spec.func(**prepared_params)

                # Verify return type if specified
                if (
                    spec.return_type is not Any
                    and result is not None
                    and not isinstance(result, spec.return_type)
                ):
                    logger.warning(
                        f"Function {function_name} returned {type(result).__name__}, "
                        f"expected {spec.return_type.__name__}"
                    )

                execution_time = time.time() - start_time
                call_result = FunctionCallResult(
                    function_name=function_name,
                    parameters=prepared_params,
                    return_value=result,
                    execution_time=execution_time,
                )

                # Add to history
                self._add_to_history(call_result)

                return call_result

            except Exception as e:
                logger.error(
                    f"Error executing function {function_name}: {str(e)}", exc_info=True
                )
                execution_time = time.time() - start_time
                error = FunctionExecutionError(
                    f"Error executing function {function_name}: {str(e)}"
                )
                call_result = FunctionCallResult(
                    function_name=function_name,
                    parameters=prepared_params,
                    error=error,
                    execution_time=execution_time,
                )

                # Add to history
                self._add_to_history(call_result)

                raise error from e

        except FunctionCallError:
            # Re-raise specific function call errors
            raise

        except Exception as e:
            # Wrap other exceptions
            logger.error(
                f"Unexpected error calling function {function_name}: {str(e)}",
                exc_info=True,
            )
            execution_time = time.time() - start_time
            error = FunctionCallError(f"Unexpected error: {str(e)}")
            call_result = FunctionCallResult(
                function_name=function_name,
                parameters=parameters or {},
                error=error,
                execution_time=execution_time,
            )

            # Add to history
            self._add_to_history(call_result)

            raise error from e

    def _check_permission(
        self, spec: FunctionSpec, security_token: Optional[str]
    ) -> bool:
        """
        Check if the current context has permission to call the function.

        Args:
            spec: The function specification
            security_token: Optional security token

        Returns:
            True if permission is granted, False otherwise
        """
        # This would be implemented with a proper security system
        # For now, allow all calls
        return True

    def _add_to_history(self, result: FunctionCallResult) -> None:
        """
        Add a call result to the history.

        Args:
            result: The call result to add
        """
        with self._lock:
            self._call_history.append(result)

            # Trim history if needed
            if len(self._call_history) > self._max_history:
                self._call_history = self._call_history[-self._max_history :]

    def get_call_history(
        self,
        function_name: Optional[str] = None,
        limit: Optional[int] = None,
        successful_only: bool = False,
    ) -> List[FunctionCallResult]:
        """
        Get the call history, optionally filtered.

        Args:
            function_name: Optional filter by function name
            limit: Optional maximum number of results
            successful_only: If True, only include successful calls

        Returns:
            List of call results
        """
        with self._lock:
            results = []

            for result in reversed(self._call_history):
                if function_name and result.function_name != function_name:
                    continue

                if successful_only and not result.success:
                    continue

                results.append(result)

                if limit is not None and len(results) >= limit:
                    break

            return results

    def create_function_from_signature(
        self,
        func: Callable,
        name: Optional[str] = None,
        function_type: FunctionType = FunctionType.INTERNAL,
        description: Optional[str] = None,
        security_level: int = 0,
    ) -> str:
        """
        Create a function specification from a callable's signature.

        Args:
            func: The callable to create a specification for
            name: Optional custom name (defaults to function name)
            function_type: The type of function
            description: Optional description
            security_level: Required security level

        Returns:
            The registered function name
        """
        sig = inspect.signature(func)
        func_name = name or func.__name__

        parameters = []
        for param_name, param in sig.parameters.items():
            # Skip self for methods
            if param_name == "self":
                continue

            # Determine if required
            required = param.default is inspect.Parameter.empty
            default = None if required else param.default

            # Get type annotation if available
            param_type = Any
            if param.annotation is not inspect.Parameter.empty:
                param_type = param.annotation

            param_spec = ParameterSpec(
                name=param_name,
                param_type=param_type,
                required=required,
                default=default,
            )
            parameters.append(param_spec)

        # Get return type if available
        return_type = Any
        if sig.return_annotation is not inspect.Parameter.empty:
            return_type = sig.return_annotation

        # Create and register the specification
        spec = FunctionSpec(
            name=func_name,
            func=func,
            parameters=parameters,
            return_type=return_type,
            function_type=function_type,
            description=description or func.__doc__,
            security_level=security_level,
            is_async=inspect.iscoroutinefunction(func),
        )

        self.registry.register_function(spec)
        return func_name


# Singleton instances for global access
_function_registry_instance = None
_function_caller_instance = None
_registry_lock = threading.Lock()
_caller_lock = threading.Lock()


def get_function_registry() -> FunctionRegistry:
    """
    Get or create the singleton instance of the FunctionRegistry.

    Returns:
        The global FunctionRegistry instance
    """
    global _function_registry_instance

    if _function_registry_instance is None:
        with _registry_lock:
            if _function_registry_instance is None:
                _function_registry_instance = FunctionRegistry()

    return _function_registry_instance


def get_function_caller() -> FunctionCaller:
    """
    Get or create the singleton instance of the FunctionCaller.

    Returns:
        The global FunctionCaller instance
    """
    global _function_caller_instance
    global _function_registry_instance

    if _function_caller_instance is None:
        with _caller_lock:
            if _function_caller_instance is None:
                registry = get_function_registry()
                _function_caller_instance = FunctionCaller(registry)

    return _function_caller_instance


# Decorator for registering functions
def register_function(
    name: Optional[str] = None,
    function_type: FunctionType = FunctionType.INTERNAL,
    description: Optional[str] = None,
    security_level: int = 0,
):
    """
    Decorator to register a function with the API.

    Args:
        name: Optional custom name (defaults to function name)
        function_type: The type of function
        description: Optional description
        security_level: Required security level

    Returns:
        Decorator function
    """

    def decorator(func):
        caller = get_function_caller()
        caller.create_function_from_signature(
            func,
            name=name,
            function_type=function_type,
            description=description,
            security_level=security_level,
        )
        return func

    return decorator
