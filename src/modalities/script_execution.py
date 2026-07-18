"""
Script Execution Engine Module

This module provides a secure environment for executing code in various languages,
including Python, JavaScript, and a custom domain-specific language. It implements
sandboxing, resource limits, and security controls to ensure safe execution.
"""

import ast
import builtins
import contextlib
import importlib
import inspect
import io
import json
import logging
import os
import platform
import re
import resource
import signal
import subprocess
import sys
import threading
import time
import traceback
from abc import ABC, abstractmethod
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

# Logger for the module
logger = logging.getLogger(__name__)


class ScriptExecutionError(Exception):
    """Base exception for script execution related errors"""

    pass


class SandboxViolationError(ScriptExecutionError):
    """Exception raised when code attempts to break out of the sandbox"""

    pass


class ResourceLimitExceededError(ScriptExecutionError):
    """Exception raised when resource limits are exceeded"""

    pass


class LanguageUnsupportedError(ScriptExecutionError):
    """Exception raised when the requested language is not supported"""

    pass


class ScriptSyntaxError(ScriptExecutionError):
    """Exception raised when the script has syntax errors"""

    pass


class ExecutionTimeoutError(ScriptExecutionError):
    """Exception raised when script execution times out"""

    pass


class ScriptLanguage(Enum):
    """Supported script execution languages"""

    PYTHON = auto()
    JAVASCRIPT = auto()
    DSL = auto()  # Domain-specific language
    SHELL = auto()  # Shell commands (with strict restrictions)


class ResourceLimits:
    """
    Configuration for resource limits during script execution.
    """

    def __init__(
        self,
        max_execution_time: float = 5.0,  # seconds
        max_memory: int = 100 * 1024 * 1024,  # 100 MB
        max_cpu_time: float = 2.0,  # seconds
        max_output_size: int = 1024 * 1024,  # 1 MB
        allow_network: bool = False,
        allow_filesystem: bool = False,
        filesystem_root: Optional[str] = None,
        max_imported_modules: int = 10,
    ):
        """
        Initialize resource limits configuration.

        Args:
            max_execution_time: Maximum wall-clock execution time in seconds
            max_memory: Maximum memory usage in bytes
            max_cpu_time: Maximum CPU time in seconds
            max_output_size: Maximum output size in bytes
            allow_network: Whether to allow network access
            allow_filesystem: Whether to allow filesystem access
            filesystem_root: Root directory for restricted filesystem access
            max_imported_modules: Maximum number of modules that can be imported
        """
        self.max_execution_time = max_execution_time
        self.max_memory = max_memory
        self.max_cpu_time = max_cpu_time
        self.max_output_size = max_output_size
        self.allow_network = allow_network
        self.allow_filesystem = allow_filesystem
        self.filesystem_root = filesystem_root
        self.max_imported_modules = max_imported_modules


class SecurityPolicy:
    """
    Security policy for script execution.
    """

    def __init__(
        self,
        allowed_builtins: Optional[Set[str]] = None,
        allowed_modules: Optional[Set[str]] = None,
        blocked_modules: Optional[Set[str]] = None,
        allowed_functions: Optional[Dict[str, Set[str]]] = None,
        blocked_functions: Optional[Dict[str, Set[str]]] = None,
        allowed_ast_nodes: Optional[Set[str]] = None,
        blocked_ast_nodes: Optional[Set[str]] = None,
    ):
        """
        Initialize security policy.

        Args:
            allowed_builtins: Set of allowed builtin functions, None for defaults
            allowed_modules: Set of allowed modules to import, None for defaults
            blocked_modules: Set of modules that cannot be imported
            allowed_functions: Dict mapping module names to allowed function sets
            blocked_functions: Dict mapping module names to blocked function sets
            allowed_ast_nodes: Set of allowed AST node types, None for defaults
            blocked_ast_nodes: Set of blocked AST node types
        """
        # Default safe builtins
        default_builtins = {
            "abs",
            "all",
            "any",
            "ascii",
            "bin",
            "bool",
            "bytes",
            "callable",
            "chr",
            "complex",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "filter",
            "float",
            "format",
            "frozenset",
            "hash",
            "hex",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "map",
            "max",
            "min",
            "next",
            "oct",
            "ord",
            "pow",
            "print",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "slice",
            "sorted",
            "str",
            "sum",
            "tuple",
            "type",
            "zip",
        }

        # Default safe modules
        default_modules = {
            "math",
            "random",
            "statistics",
            "datetime",
            "json",
            "re",
            "collections",
            "itertools",
            "functools",
            "operator",
        }

        # Default blocked modules
        default_blocked = {
            "os",
            "sys",
            "subprocess",
            "importlib",
            "pathlib",
            "socket",
            "shutil",
            "multiprocessing",
            "threading",
            "ctypes",
            "platform",
        }

        # Default blocked AST nodes
        default_blocked_nodes = {
            "Import",
            "ImportFrom",
            "Exec",
            "Eval",
            "compile",
            "open",
            "file",
            "__import__",
            "globals",
            "locals",
        }

        self.allowed_builtins = allowed_builtins or default_builtins
        self.allowed_modules = allowed_modules or default_modules
        self.blocked_modules = blocked_modules or default_blocked
        self.allowed_functions = allowed_functions or {}
        self.blocked_functions = blocked_functions or {}
        self.allowed_ast_nodes = allowed_ast_nodes
        self.blocked_ast_nodes = blocked_ast_nodes or default_blocked_nodes

    def is_builtin_allowed(self, name: str) -> bool:
        """Check if a builtin function is allowed."""
        return name in self.allowed_builtins

    def is_module_allowed(self, name: str) -> bool:
        """Check if a module is allowed to be imported."""
        # Check if explicitly blocked
        if name in self.blocked_modules:
            return False

        # Handle submodules (e.g., 'os.path' should be blocked if 'os' is blocked)
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            prefix = ".".join(parts[:i])
            if prefix in self.blocked_modules:
                return False

        # Check if explicitly allowed or if using default allowlist
        return name in self.allowed_modules

    def is_function_allowed(self, module: str, function: str) -> bool:
        """Check if a function in a module is allowed."""
        # Check if function is in blocked list for this module
        if (
            module in self.blocked_functions
            and function in self.blocked_functions[module]
        ):
            return False

        # Check if module has an allowed function list and function is in it
        if module in self.allowed_functions:
            return function in self.allowed_functions[module]

        # If module is allowed and has no specific function restrictions
        return self.is_module_allowed(module)

    def is_ast_node_allowed(self, node_type: str) -> bool:
        """Check if an AST node type is allowed."""
        if node_type in self.blocked_ast_nodes:
            return False

        if self.allowed_ast_nodes is not None:
            return node_type in self.allowed_ast_nodes

        return True


class ExecutionContext:
    """
    Context for script execution, including local variables and output.
    """

    def __init__(self):
        """Initialize an execution context."""
        self.locals: Dict[str, Any] = {}
        self.output = io.StringIO()
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.exception: Optional[Exception] = None
        self.imported_modules: List[str] = []

    @property
    def execution_time(self) -> float:
        """Get the execution time in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    def complete(self, exception: Optional[Exception] = None) -> None:
        """
        Mark execution as complete.

        Args:
            exception: Optional exception that occurred during execution
        """
        self.end_time = time.time()
        self.exception = exception

    def get_output(self) -> str:
        """Get the captured output as a string."""
        return self.output.getvalue()

    def get_result(self) -> Dict[str, Any]:
        """Get the execution result as a dictionary."""
        return {
            "locals": {k: repr(v) for k, v in self.locals.items()},
            "output": self.get_output(),
            "execution_time": self.execution_time,
            "exception": str(self.exception) if self.exception else None,
            "imported_modules": self.imported_modules,
        }


class ASTSandboxChecker(ast.NodeVisitor):
    """
    AST visitor that checks for potentially unsafe operations.
    """

    def __init__(self, security_policy: SecurityPolicy):
        """
        Initialize the checker with a security policy.

        Args:
            security_policy: The security policy to enforce
        """
        self.security_policy = security_policy
        self.violations = []

    def check(self, code: str) -> List[str]:
        """
        Check code for security violations.

        Args:
            code: The code to check

        Returns:
            List of violation messages
        """
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return self.violations
        except SyntaxError as e:
            return [f"Syntax error: {str(e)}"]

    def visit(self, node):
        """Visit a node and check if it's allowed."""
        node_type = node.__class__.__name__

        if not self.security_policy.is_ast_node_allowed(node_type):
            self.violations.append(f"Forbidden AST node: {node_type}")

        super().visit(node)

    def visit_Import(self, node):
        """Check import statements."""
        for name in node.names:
            if not self.security_policy.is_module_allowed(name.name):
                self.violations.append(f"Import of forbidden module: {name.name}")

    def visit_ImportFrom(self, node):
        """Check from-import statements."""
        if not self.security_policy.is_module_allowed(node.module):
            self.violations.append(f"Import from forbidden module: {node.module}")

        # Also check imported names if they're restricted
        if self.security_policy.is_module_allowed(node.module):
            for name in node.names:
                if not self.security_policy.is_function_allowed(node.module, name.name):
                    self.violations.append(
                        f"Import of forbidden function: {node.module}.{name.name}"
                    )

    def visit_Call(self, node):
        """Check function calls."""
        # Check for direct calls to builtin functions
        if isinstance(node.func, ast.Name):
            if not self.security_policy.is_builtin_allowed(node.func.id):
                self.violations.append(f"Call to forbidden builtin: {node.func.id}")

        # Check for attribute calls (e.g., module.function())
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module = node.func.value.id
                function = node.func.attr

                if not self.security_policy.is_function_allowed(module, function):
                    self.violations.append(
                        f"Call to forbidden function: {module}.{function}"
                    )

        # Continue visiting children
        self.generic_visit(node)


class ScriptExecutor(ABC):
    """
    Abstract base class for script executors.
    """

    @property
    @abstractmethod
    def language(self) -> ScriptLanguage:
        """Get the language this executor supports."""
        pass

    @abstractmethod
    def execute(
        self,
        code: str,
        context: ExecutionContext,
        resource_limits: ResourceLimits,
        security_policy: SecurityPolicy,
    ) -> Dict[str, Any]:
        """
        Execute the given code in the specified context.

        Args:
            code: The code to execute
            context: The execution context
            resource_limits: Resource limits for execution
            security_policy: Security policy to enforce

        Returns:
            Dictionary with execution results

        Raises:
            ScriptExecutionError: If execution fails
        """
        pass

    def check_security(self, code: str, security_policy: SecurityPolicy) -> List[str]:
        """
        Check code for security violations.

        Args:
            code: The code to check
            security_policy: Security policy to enforce

        Returns:
            List of violation messages
        """
        return []  # Default implementation does nothing


class PythonExecutor(ScriptExecutor):
    """
    Executor for Python code.
    """

    @property
    def language(self) -> ScriptLanguage:
        """Get the language this executor supports."""
        return ScriptLanguage.PYTHON

    def check_security(self, code: str, security_policy: SecurityPolicy) -> List[str]:
        """
        Check Python code for security violations.

        Args:
            code: The code to check
            security_policy: Security policy to enforce

        Returns:
            List of violation messages
        """
        checker = ASTSandboxChecker(security_policy)
        return checker.check(code)

    def execute(
        self,
        code: str,
        context: ExecutionContext,
        resource_limits: ResourceLimits,
        security_policy: SecurityPolicy,
    ) -> Dict[str, Any]:
        """
        Execute Python code in a secure sandbox.

        Args:
            code: The Python code to execute
            context: The execution context
            resource_limits: Resource limits for execution
            security_policy: Security policy to enforce

        Returns:
            Dictionary with execution results

        Raises:
            ScriptExecutionError: If execution fails
        """
        # First check for security violations
        violations = self.check_security(code, security_policy)
        if violations:
            error_msg = "; ".join(violations)
            raise SandboxViolationError(f"Security violations detected: {error_msg}")

        # Create a restricted globals dictionary
        restricted_globals = {
            "__builtins__": {
                name: getattr(builtins, name)
                for name in security_policy.allowed_builtins
                if hasattr(builtins, name)
            },
            "print": lambda *args, **kwargs: print(
                *args, **kwargs, file=context.output
            ),
        }

        # Set up resource limits
        def timeout_handler(signum, frame):
            raise ExecutionTimeoutError(
                f"Execution timed out after {resource_limits.max_execution_time} seconds"
            )

        # Set the timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, resource_limits.max_execution_time)

        try:
            # Execute the code
            exec(code, restricted_globals, context.locals)

            # Record imported modules
            for name, value in context.locals.items():
                if inspect.ismodule(value) and name not in context.imported_modules:
                    context.imported_modules.append(name)

                    # Check if we've imported too many modules
                    if (
                        len(context.imported_modules)
                        > resource_limits.max_imported_modules
                    ):
                        raise ResourceLimitExceededError(
                            f"Too many modules imported (limit: {resource_limits.max_imported_modules})"
                        )

            return context.get_result()

        except Exception as e:
            if isinstance(e, ScriptExecutionError):
                # Re-raise specific execution errors
                raise

            # Wrap other exceptions
            context.complete(e)
            logger.error(f"Error executing Python code: {str(e)}", exc_info=True)
            return context.get_result()

        finally:
            # Clean up
            signal.setitimer(signal.ITIMER_REAL, 0)  # Disable the timer
            context.complete()


class JavaScriptExecutor(ScriptExecutor):
    """
    Executor for JavaScript code using Node.js.
    """

    @property
    def language(self) -> ScriptLanguage:
        """Get the language this executor supports."""
        return ScriptLanguage.JAVASCRIPT

    def check_security(self, code: str, security_policy: SecurityPolicy) -> List[str]:
        """
        Check JavaScript code for security violations.

        This is a simple check for obviously dangerous patterns.
        A more comprehensive check would use a JavaScript parser.

        Args:
            code: The code to check
            security_policy: Security policy to enforce

        Returns:
            List of violation messages
        """
        violations = []

        # Check for potentially dangerous patterns
        danger_patterns = [
            (
                r'require\([\'"](?:child_process|fs|net|os|path|process|cluster|http|https|dns)[\'"]',
                "Access to dangerous Node.js modules",
            ),
            (r"process\.", "Access to Node.js process object"),
            (r"eval\(", "Use of eval()"),
            (r"Function\([^\)]*\)", "Dynamic function creation"),
            (r"Object\.prototype", "Modifying Object.prototype"),
            (r"__proto__", "Accessing __proto__"),
            (r"with\s*\(", "Use of with statement"),
        ]

        for pattern, message in danger_patterns:
            if re.search(pattern, code):
                violations.append(message)

        return violations

    def execute(
        self,
        code: str,
        context: ExecutionContext,
        resource_limits: ResourceLimits,
        security_policy: SecurityPolicy,
    ) -> Dict[str, Any]:
        """
        Execute JavaScript code using Node.js.

        Args:
            code: The JavaScript code to execute
            context: The execution context
            resource_limits: Resource limits for execution
            security_policy: Security policy to enforce

        Returns:
            Dictionary with execution results

        Raises:
            ScriptExecutionError: If execution fails
        """
        # First check for security violations
        violations = self.check_security(code, security_policy)
        if violations:
            error_msg = "; ".join(violations)
            raise SandboxViolationError(f"Security violations detected: {error_msg}")

        # Check if Node.js is available
        try:
            node_version = subprocess.check_output(
                ["node", "--version"], stderr=subprocess.STDOUT, text=True, timeout=1.0
            )
            logger.debug(f"Using Node.js {node_version.strip()}")
        except (subprocess.SubprocessError, FileNotFoundError):
            raise LanguageUnsupportedError("Node.js not available")

        # Create a temporary directory for execution
        temp_dir = Path.cwd() / "temp" / f"js_exec_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Create a wrapper script that limits execution and captures output
            wrapper_code = f"""
            // Sandbox wrapper
            const vm = require('vm');
            const context = vm.createContext({{
                console: {{
                    log: (...args) => {{ process.stdout.write(args.join(' ') + '\\n'); }},
                    error: (...args) => {{ process.stderr.write(args.join(' ') + '\\n'); }},
                    warn: (...args) => {{ process.stderr.write(args.join(' ') + '\\n'); }},
                    info: (...args) => {{ process.stdout.write(args.join(' ') + '\\n'); }}
                }},
                setTimeout: (cb, ms) => {{
                    if (ms > {int(resource_limits.max_execution_time * 1000)}) {{
                        throw new Error('setTimeout duration exceeds maximum allowed time');
                    }}
                    return setTimeout(cb, ms);
                }},
                clearTimeout,
                setInterval: (cb, ms) => {{
                    if (ms < 100) {{
                        throw new Error('setInterval duration too small, minimum 100ms');
                    }}
                    return setInterval(cb, ms);
                }},
                clearInterval,
                JSON,
                Math,
                Date,
                RegExp,
                Array,
                Object,
                String,
                Number,
                Boolean,
                Error,
                Buffer: {{ from: () => {{ throw new Error('Buffer access not allowed'); }} }},
                require: () => {{ throw new Error('require() not allowed'); }},
                process: undefined,
                global: undefined,
                __dirname: undefined,
                __filename: undefined
            }});

            try {{
                // Execute the user code with a timeout
                const script = new vm.Script(`{code.replace('`', '\\`').replace('$', '\\$')}`);
                const result = script.runInContext(context, {{
                    timeout: {int(resource_limits.max_execution_time * 1000)},
                    displayErrors: true
                }});

                // Output result if it's a value
                if (result !== undefined) {{
                    console.log('=> ' + result);
                }}

                // Output final context state
                console.log('\\n--- CONTEXT STATE ---');
                for (const key in context) {{
                    if (key !== 'console' && key !== 'require' && key !== 'setTimeout' &&
                        key !== 'clearTimeout' && key !== 'setInterval' && key !== 'clearInterval' &&
                        key !== 'JSON' && key !== 'Math' && key !== 'Date' && key !== 'RegExp' &&
                        key !== 'Array' && key !== 'Object' && key !== 'String' && key !== 'Number' &&
                        key !== 'Boolean' && key !== 'Error' && key !== 'Buffer') {{
                        try {{
                            console.log(`${{key}}: ${{JSON.stringify(context[key])}}`);
                        }} catch (e) {{
                            console.log(`${{key}}: [Complex object]`);
                        }}
                    }}
                }}
            }} catch (e) {{
                console.error('ERROR: ' + e.message);
                console.error(e.stack);
                process.exit(1);
            }}
            """

            # Write the wrapper to a file
            wrapper_path = temp_dir / "wrapper.js"
            with open(wrapper_path, "w") as f:
                f.write(wrapper_code)

            # Execute the JavaScript code using Node.js
            try:
                process = subprocess.Popen(
                    ["node", str(wrapper_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(temp_dir),
                )

                # Wait for the process with timeout
                try:
                    stdout, stderr = process.communicate(
                        timeout=resource_limits.max_execution_time + 0.5
                    )

                    # Write output to context
                    context.output.write(stdout)
                    if stderr:
                        context.output.write(f"\nSTDERR:\n{stderr}")

                    # Parse context state
                    if "--- CONTEXT STATE ---" in stdout:
                        state_section = stdout.split("--- CONTEXT STATE ---")[1].strip()
                        for line in state_section.split("\n"):
                            if ": " in line:
                                key, value = line.split(": ", 1)
                                try:
                                    context.locals[key] = json.loads(value)
                                except json.JSONDecodeError:
                                    context.locals[key] = value

                    # Check exit code
                    if process.returncode != 0:
                        raise ScriptExecutionError(
                            f"JavaScript execution failed: {stderr.strip()}"
                        )

                except subprocess.TimeoutExpired:
                    process.kill()
                    raise ExecutionTimeoutError(
                        f"JavaScript execution timed out after {resource_limits.max_execution_time} seconds"
                    )

            except Exception as e:
                if isinstance(e, ScriptExecutionError):
                    # Re-raise specific execution errors
                    raise

                # Wrap other exceptions
                context.complete(e)
                logger.error(
                    f"Error executing JavaScript code: {str(e)}", exc_info=True
                )
                return context.get_result()

            # Record completion
            context.complete()
            return context.get_result()

        finally:
            # Clean up temporary directory
            import shutil

            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {str(e)}")


class DSLExecutor(ScriptExecutor):
    """
    Executor for a simple domain-specific language.
    """

    # DSL keywords and their Python implementations
    DSL_KEYWORDS = {
        "SET": "{}={!r}",
        "ADD": "{} += {}",
        "SUB": "{} -= {}",
        "MUL": "{} *= {}",
        "DIV": "{} /= {}",
        "PRINT": "print({}, end='')",
        "PRINTLN": "print({})",
        "IF": "if {}:",
        "ELSE": "else:",
        "END": "",  # Will be handled specially
        "WHILE": "while {}:",
        "FOREACH": "for {} in {}:",
        "CALL": "{}",
    }

    @property
    def language(self) -> ScriptLanguage:
        """Get the language this executor supports."""
        return ScriptLanguage.DSL

    def check_security(self, code: str, security_policy: SecurityPolicy) -> List[str]:
        """
        Check DSL code for security violations.

        Args:
            code: The code to check
            security_policy: Security policy to enforce

        Returns:
            List of violation messages
        """
        violations = []

        # Convert to Python and check the resulting code
        try:
            python_code = self._translate_to_python(code)
            python_checker = ASTSandboxChecker(security_policy)
            violations = python_checker.check(python_code)
        except Exception as e:
            violations.append(f"Error parsing DSL code: {str(e)}")

        return violations

    def _translate_to_python(self, dsl_code: str) -> str:
        """
        Translate DSL code to Python code.

        Args:
            dsl_code: The DSL code to translate

        Returns:
            Equivalent Python code
        """
        python_lines = []
        indent_level = 0
        indent_stack = []

        for line_num, line in enumerate(dsl_code.strip().split("\n"), 1):
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse the line
            parts = line.split(" ", 1)
            if len(parts) < 1:
                continue

            keyword = parts[0].upper()
            args = parts[1] if len(parts) > 1 else ""

            # Check if keyword is supported
            if keyword not in self.DSL_KEYWORDS:
                raise ScriptSyntaxError(
                    f"Unknown keyword at line {line_num}: {keyword}"
                )

            # Handle indentation
            indent = "    " * indent_level

            # Handle special cases
            if keyword == "END":
                # End a block by decreasing indentation
                if not indent_stack:
                    raise ScriptSyntaxError(f"Unexpected END at line {line_num}")

                indent_level = indent_stack.pop()
                continue

            # Get the Python template for this keyword
            template = self.DSL_KEYWORDS[keyword]

            # Format the Python line
            if args:
                try:
                    python_line = indent + template.format(*self._parse_args(args))
                except Exception as e:
                    raise ScriptSyntaxError(
                        f"Error parsing arguments at line {line_num}: {str(e)}"
                    )
            else:
                python_line = indent + template

            python_lines.append(python_line)

            # Handle blocks
            if keyword in ("IF", "ELSE", "WHILE", "FOREACH"):
                indent_stack.append(indent_level)
                indent_level += 1

        # Check for unclosed blocks
        if indent_stack:
            raise ScriptSyntaxError("Unclosed blocks, missing END statements")

        return "\n".join(python_lines)

    def _parse_args(self, args_str: str) -> List[str]:
        """
        Parse DSL arguments into Python expressions.

        Args:
            args_str: The DSL arguments string

        Returns:
            List of Python expressions
        """
        # Simple splitting by comma, handling quoted strings
        args = []
        current_arg = ""
        in_quotes = False
        quote_char = None

        for char in args_str:
            if char in ('"', "'"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                current_arg += char
            elif char == "," and not in_quotes:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char

        if current_arg:
            args.append(current_arg.strip())

        return args

    def execute(
        self,
        code: str,
        context: ExecutionContext,
        resource_limits: ResourceLimits,
        security_policy: SecurityPolicy,
    ) -> Dict[str, Any]:
        """
        Execute DSL code by translating to Python and executing.

        Args:
            code: The DSL code to execute
            context: The execution context
            resource_limits: Resource limits for execution
            security_policy: Security policy to enforce

        Returns:
            Dictionary with execution results

        Raises:
            ScriptExecutionError: If execution fails
        """
        # First check for security violations
        violations = self.check_security(code, security_policy)
        if violations:
            error_msg = "; ".join(violations)
            raise SandboxViolationError(f"Security violations detected: {error_msg}")

        try:
            # Translate DSL to Python
            python_code = self._translate_to_python(code)

            # Use the Python executor to run the translated code
            python_executor = PythonExecutor()
            return python_executor.execute(
                python_code, context, resource_limits, security_policy
            )

        except Exception as e:
            if isinstance(e, ScriptExecutionError):
                # Re-raise specific execution errors
                raise

            # Wrap other exceptions
            context.complete(e)
            logger.error(f"Error executing DSL code: {str(e)}", exc_info=True)
            return context.get_result()


class ScriptEngine:
    """
    Main interface for executing scripts in various languages.
    """

    def __init__(self):
        """Initialize the script engine."""
        self._executors = {
            ScriptLanguage.PYTHON: PythonExecutor(),
            ScriptLanguage.JAVASCRIPT: JavaScriptExecutor(),
            ScriptLanguage.DSL: DSLExecutor(),
        }

        self._default_resource_limits = ResourceLimits()
        self._default_security_policy = SecurityPolicy()

    def execute(
        self,
        code: str,
        language: ScriptLanguage,
        resource_limits: Optional[ResourceLimits] = None,
        security_policy: Optional[SecurityPolicy] = None,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a script in the specified language.

        Args:
            code: The code to execute
            language: The language to execute in
            resource_limits: Optional custom resource limits
            security_policy: Optional custom security policy
            initial_context: Optional initial local variables

        Returns:
            Dictionary with execution results

        Raises:
            LanguageUnsupportedError: If the language is not supported
            ScriptExecutionError: If execution fails
        """
        # Check if the language is supported
        if language not in self._executors:
            raise LanguageUnsupportedError(f"Unsupported language: {language.name}")

        # Get the appropriate executor
        executor = self._executors[language]

        # Use default limits and policy if not provided
        limits = resource_limits or self._default_resource_limits
        policy = security_policy or self._default_security_policy

        # Create an execution context
        context = ExecutionContext()
        if initial_context:
            context.locals.update(initial_context)

        # Execute the code
        logger.info(f"Executing {language.name} code")
        result = executor.execute(code, context, limits, policy)

        return result

    def check_security(
        self,
        code: str,
        language: ScriptLanguage,
        security_policy: Optional[SecurityPolicy] = None,
    ) -> List[str]:
        """
        Check code for security violations.

        Args:
            code: The code to check
            language: The language of the code
            security_policy: Optional custom security policy

        Returns:
            List of violation messages

        Raises:
            LanguageUnsupportedError: If the language is not supported
        """
        # Check if the language is supported
        if language not in self._executors:
            raise LanguageUnsupportedError(f"Unsupported language: {language.name}")

        # Get the appropriate executor
        executor = self._executors[language]

        # Use default policy if not provided
        policy = security_policy or self._default_security_policy

        # Check the code
        return executor.check_security(code, policy)


# Singleton instance for global access
_script_engine_instance = None
_engine_lock = threading.Lock()


def get_script_engine() -> ScriptEngine:
    """
    Get or create the singleton instance of the ScriptEngine.

    Returns:
        The global ScriptEngine instance
    """
    global _script_engine_instance

    if _script_engine_instance is None:
        with _engine_lock:
            if _script_engine_instance is None:
                _script_engine_instance = ScriptEngine()

    return _script_engine_instance
