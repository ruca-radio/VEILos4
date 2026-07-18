"""
Experiment Framework Module

This module provides a safe environment for running code experiments and simulations,
with support for parallel execution, result collection, and isolation from the main system.
"""

import copy
import json
import logging
import multiprocessing
import os
import queue
import shutil
import tempfile
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from src.modalities.script_execution import (
    ExecutionContext,
    ResourceLimits,
    ScriptEngine,
    ScriptLanguage,
    SecurityPolicy,
    get_script_engine,
)

# Logger for the module
logger = logging.getLogger(__name__)


class ExperimentError(Exception):
    """Base exception for experiment related errors"""

    pass


class ExperimentTimeoutError(ExperimentError):
    """Exception raised when an experiment times out"""

    pass


class ExperimentStatus(Enum):
    """Status of an experiment"""

    CREATED = auto()  # Experiment created but not started
    RUNNING = auto()  # Currently running
    COMPLETED = auto()  # Successfully completed
    FAILED = auto()  # Failed with an error
    TIMEOUT = auto()  # Timed out
    CANCELLED = auto()  # Cancelled by user


class ExperimentType(Enum):
    """Types of experiments that can be performed"""

    CODE_EXECUTION = auto()  # Run and evaluate code
    SIMULATION = auto()  # Simulate a system or environment
    OPTIMIZATION = auto()  # Optimize parameters or code
    BENCHMARK = auto()  # Benchmark performance
    A_B_TEST = auto()  # Compare two variants
    CUSTOM = auto()  # Custom experiment type


@dataclass
class ExperimentResult:
    """
    Results of an experiment.
    """

    experiment_id: str
    status: ExperimentStatus
    start_time: float
    end_time: Optional[float] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Get the experiment duration in seconds."""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "experiment_id": self.experiment_id,
            "status": self.status.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "outputs": self.outputs,
            "error": self.error,
            "metrics": self.metrics,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentResult":
        """Create from dictionary representation."""
        return cls(
            experiment_id=data["experiment_id"],
            status=ExperimentStatus[data["status"]],
            start_time=data["start_time"],
            end_time=data["end_time"],
            outputs=data["outputs"],
            error=data["error"],
            metrics=data["metrics"],
        )


class Experiment:
    """
    Base class for all experiments.
    """

    def __init__(
        self,
        experiment_type: ExperimentType,
        name: Optional[str] = None,
        description: Optional[str] = None,
        timeout: float = 60.0,
        workspace: Optional[str] = None,
    ):
        """
        Initialize an experiment.

        Args:
            experiment_type: The type of experiment
            name: Optional name for the experiment
            description: Optional description
            timeout: Maximum execution time in seconds
            workspace: Optional workspace directory (uses temp dir if None)
        """
        self.experiment_id = str(uuid.uuid4())
        self.experiment_type = experiment_type
        self.name = name or f"{experiment_type.name.lower()}_{self.experiment_id[:8]}"
        self.description = description
        self.timeout = timeout
        self.status = ExperimentStatus.CREATED
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.result: Optional[ExperimentResult] = None

        # Create workspace directory
        if workspace:
            self.workspace = Path(workspace) / self.name
        else:
            temp_dir = tempfile.mkdtemp(prefix=f"experiment_{self.name}_")
            self.workspace = Path(temp_dir)

        self.workspace.mkdir(parents=True, exist_ok=True)

        # For storing experiment artifacts
        self.artifacts_dir = self.workspace / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)

        # For result visualization
        self.visualization_dir = self.workspace / "visualization"
        self.visualization_dir.mkdir(exist_ok=True)

        # For storing logs
        self.logs_dir = self.workspace / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Set up logging for this experiment
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for this experiment."""
        self.log_file = self.logs_dir / "experiment.log"

        # Create a file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)

        # Create a formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Get the logger for this experiment
        self.logger = logging.getLogger(f"experiment.{self.name}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    def run(self) -> ExperimentResult:
        """
        Run the experiment.

        Returns:
            The experiment result

        Raises:
            ExperimentError: If the experiment fails
        """
        # Initialize result
        self.start_time = time.time()
        self.status = ExperimentStatus.RUNNING

        self.result = ExperimentResult(
            experiment_id=self.experiment_id,
            status=ExperimentStatus.RUNNING,
            start_time=self.start_time,
        )

        self.logger.info(f"Starting experiment {self.name} ({self.experiment_id})")

        try:
            # Create a timer for timeout
            timer = threading.Timer(self.timeout, self._timeout)
            timer.daemon = True
            timer.start()

            # Run the experiment implementation
            outputs = self._run_implementation()

            # Cancel the timer if we completed successfully
            timer.cancel()

            # Update result
            self.end_time = time.time()
            self.status = ExperimentStatus.COMPLETED

            self.result.end_time = self.end_time
            self.result.status = ExperimentStatus.COMPLETED
            self.result.outputs = outputs

            self.logger.info(
                f"Experiment {self.name} completed successfully in "
                f"{self.result.duration:.2f} seconds"
            )

            return self.result

        except ExperimentTimeoutError as e:
            self.end_time = time.time()
            self.status = ExperimentStatus.TIMEOUT

            self.result.end_time = self.end_time
            self.result.status = ExperimentStatus.TIMEOUT
            self.result.error = str(e)

            self.logger.error(
                f"Experiment {self.name} timed out after {self.timeout} seconds"
            )

            return self.result

        except Exception as e:
            self.end_time = time.time()
            self.status = ExperimentStatus.FAILED

            error_details = traceback.format_exc()
            self.result.end_time = self.end_time
            self.result.status = ExperimentStatus.FAILED
            self.result.error = f"{str(e)}\n{error_details}"

            self.logger.error(
                f"Experiment {self.name} failed: {str(e)}\n{error_details}"
            )

            return self.result

    def _timeout(self) -> None:
        """Called when the experiment times out."""
        if self.status == ExperimentStatus.RUNNING:
            self.end_time = time.time()
            self.status = ExperimentStatus.TIMEOUT

            if self.result:
                self.result.end_time = self.end_time
                self.result.status = ExperimentStatus.TIMEOUT
                self.result.error = f"Experiment timed out after {self.timeout} seconds"

            # This will interrupt the main thread
            thread_id = threading.get_ident()
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                thread_id, ctypes.py_object(ExperimentTimeoutError)
            )
            if res == 0:
                self.logger.error(
                    f"Failed to raise timeout exception for thread {thread_id}"
                )

    def _run_implementation(self) -> Dict[str, Any]:
        """
        Implement the experiment logic.

        This method should be overridden by subclasses.

        Returns:
            Dictionary of experiment outputs
        """
        raise NotImplementedError("Subclasses must implement _run_implementation")

    def save_artifact(self, name: str, data: Any) -> str:
        """
        Save an experiment artifact.

        Args:
            name: Name of the artifact
            data: The artifact data

        Returns:
            Path to the saved artifact
        """
        artifact_path = self.artifacts_dir / name

        # Handle different types of data
        if isinstance(data, (str, bytes)):
            mode = "wb" if isinstance(data, bytes) else "w"
            with open(artifact_path, mode) as f:
                f.write(data)

        elif isinstance(data, dict):
            with open(artifact_path, "w") as f:
                json.dump(data, f, indent=2)

        else:
            # Attempt to serialize using pickle
            import pickle

            with open(artifact_path, "wb") as f:
                pickle.dump(data, f)

        self.logger.debug(f"Saved artifact: {name}")
        return str(artifact_path)

    def load_artifact(self, name: str, as_json: bool = False) -> Any:
        """
        Load an experiment artifact.

        Args:
            name: Name of the artifact
            as_json: Whether to parse as JSON

        Returns:
            The loaded artifact data
        """
        artifact_path = self.artifacts_dir / name

        if not artifact_path.exists():
            raise FileNotFoundError(f"Artifact not found: {name}")

        if as_json:
            with open(artifact_path, "r") as f:
                return json.load(f)

        # Default to loading as text
        try:
            with open(artifact_path, "r") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try loading as binary
            with open(artifact_path, "rb") as f:
                # Attempt to unpickle
                try:
                    import pickle

                    return pickle.load(f)
                except:
                    # Return raw bytes
                    return f.read()

    def cleanup(self) -> None:
        """Clean up experiment resources."""
        # Only remove temporary directories
        if self.workspace and str(self.workspace).startswith(tempfile.gettempdir()):
            try:
                shutil.rmtree(self.workspace)
                logger.debug(f"Cleaned up experiment workspace: {self.workspace}")
            except Exception as e:
                logger.warning(f"Failed to clean up experiment workspace: {str(e)}")


class CodeExecutionExperiment(Experiment):
    """
    Experiment for executing and evaluating code.
    """

    def __init__(
        self,
        code: str,
        language: ScriptLanguage,
        inputs: Optional[Dict[str, Any]] = None,
        expected_outputs: Optional[Dict[str, Any]] = None,
        resource_limits: Optional[ResourceLimits] = None,
        security_policy: Optional[SecurityPolicy] = None,
        **kwargs,
    ):
        """
        Initialize a code execution experiment.

        Args:
            code: The code to execute
            language: The language of the code
            inputs: Optional input values for the code
            expected_outputs: Optional expected outputs for validation
            resource_limits: Optional resource limits
            security_policy: Optional security policy
            **kwargs: Additional parameters for the base class
        """
        super().__init__(ExperimentType.CODE_EXECUTION, **kwargs)

        self.code = code
        self.language = language
        self.inputs = inputs or {}
        self.expected_outputs = expected_outputs or {}
        self.resource_limits = resource_limits or ResourceLimits(
            max_execution_time=min(30.0, self.timeout - 5.0),
            max_memory=50 * 1024 * 1024,  # 50 MB
            allow_network=False,
            allow_filesystem=True,  # Allow access to experiment workspace
            filesystem_root=str(self.workspace),
        )
        self.security_policy = security_policy or SecurityPolicy()

        # Save code as an artifact
        self.save_artifact(f"code.{self._get_file_extension()}", self.code)

        if self.inputs:
            self.save_artifact("inputs.json", self.inputs)

        if self.expected_outputs:
            self.save_artifact("expected_outputs.json", self.expected_outputs)

    def _get_file_extension(self) -> str:
        """Get the file extension for the code language."""
        extensions = {
            ScriptLanguage.PYTHON: "py",
            ScriptLanguage.JAVASCRIPT: "js",
            ScriptLanguage.DSL: "dsl",
        }
        return extensions.get(self.language, "txt")

    def _run_implementation(self) -> Dict[str, Any]:
        """
        Execute the code and collect results.

        Returns:
            Dictionary of execution results
        """
        self.logger.info(f"Executing {self.language.name} code")

        # Get the script engine
        script_engine = get_script_engine()

        # Run the code
        execution_result = script_engine.execute(
            self.code,
            self.language,
            resource_limits=self.resource_limits,
            security_policy=self.security_policy,
            initial_context=self.inputs,
        )

        # Save execution output
        self.save_artifact("execution_output.txt", execution_result.get("output", ""))

        # Validate results if expected outputs were provided
        validation_results = {}
        if self.expected_outputs:
            self.logger.info("Validating outputs against expected values")

            locals_dict = execution_result.get("locals", {})

            for key, expected in self.expected_outputs.items():
                if key in locals_dict:
                    actual = locals_dict[key]
                    # Simple string comparison (would be more sophisticated in real implementation)
                    matches = str(actual) == str(expected)
                    validation_results[key] = {
                        "expected": str(expected),
                        "actual": str(actual),
                        "matches": matches,
                    }
                else:
                    validation_results[key] = {
                        "expected": str(expected),
                        "actual": None,
                        "matches": False,
                    }

            self.save_artifact("validation_results.json", validation_results)

        # Collect metrics
        metrics = {
            "execution_time": execution_result.get("execution_time", 0),
            "success": execution_result.get("exception") is None,
            "output_size": len(execution_result.get("output", "")),
            "imported_modules": execution_result.get("imported_modules", []),
        }

        if validation_results:
            metrics["validation"] = {
                "total": len(validation_results),
                "passed": sum(1 for v in validation_results.values() if v["matches"]),
                "success_rate": (
                    sum(1 for v in validation_results.values() if v["matches"])
                    / len(validation_results)
                    if validation_results
                    else 0
                ),
            }

        # Store metrics in result
        if self.result:
            self.result.metrics = metrics

        return {
            "execution_result": execution_result,
            "validation_results": validation_results,
            "metrics": metrics,
        }


class SimulationExperiment(Experiment):
    """
    Experiment for running simulations.
    """

    def __init__(
        self,
        simulation_func: Callable,
        parameters: Dict[str, Any],
        iterations: int = 1,
        collect_stats: bool = True,
        **kwargs,
    ):
        """
        Initialize a simulation experiment.

        Args:
            simulation_func: Function that implements the simulation
            parameters: Parameters for the simulation
            iterations: Number of iterations to run
            collect_stats: Whether to collect statistics
            **kwargs: Additional parameters for the base class
        """
        super().__init__(ExperimentType.SIMULATION, **kwargs)

        self.simulation_func = simulation_func
        self.parameters = parameters
        self.iterations = iterations
        self.collect_stats = collect_stats

        # Save parameters as an artifact
        self.save_artifact("parameters.json", self.parameters)

    def _run_implementation(self) -> Dict[str, Any]:
        """
        Run the simulation and collect results.

        Returns:
            Dictionary of simulation results
        """
        self.logger.info(f"Running simulation with {self.iterations} iterations")

        all_results = []
        successful_iterations = 0

        for i in range(self.iterations):
            self.logger.debug(f"Starting iteration {i+1}/{self.iterations}")

            try:
                # Make a copy of parameters to avoid cross-iteration contamination
                params_copy = copy.deepcopy(self.parameters)

                # Run the simulation function
                iteration_result = self.simulation_func(params_copy)

                # Add iteration metadata
                if isinstance(iteration_result, dict):
                    iteration_result["iteration"] = i + 1
                    iteration_result["success"] = True

                all_results.append(iteration_result)
                successful_iterations += 1

            except Exception as e:
                error_details = traceback.format_exc()
                self.logger.error(f"Iteration {i+1} failed: {str(e)}\n{error_details}")

                all_results.append(
                    {
                        "iteration": i + 1,
                        "success": False,
                        "error": str(e),
                        "error_details": error_details,
                    }
                )

        # Calculate statistics if requested
        stats = {}
        if self.collect_stats and successful_iterations > 0:
            self.logger.info("Collecting simulation statistics")

            try:
                import numpy as np

                # Extract numerical values that appear in all successful iterations
                numerical_values = {}

                for result in all_results:
                    if not result.get("success", False):
                        continue

                    self._extract_numerical_values(result, numerical_values)

                # Calculate statistics for each numerical value
                for key, values in numerical_values.items():
                    if len(values) >= successful_iterations:
                        values_array = np.array(values)
                        stats[key] = {
                            "mean": float(np.mean(values_array)),
                            "median": float(np.median(values_array)),
                            "std": float(np.std(values_array)),
                            "min": float(np.min(values_array)),
                            "max": float(np.max(values_array)),
                        }

            except ImportError:
                self.logger.warning("Numpy not available, skipping detailed statistics")

                # Basic statistics without numpy
                numerical_values = {}
                for result in all_results:
                    if not result.get("success", False):
                        continue

                    self._extract_numerical_values(result, numerical_values)

                for key, values in numerical_values.items():
                    if len(values) >= successful_iterations:
                        stats[key] = {
                            "mean": sum(values) / len(values),
                            "min": min(values),
                            "max": max(values),
                        }

        # Save results and stats
        self.save_artifact("simulation_results.json", all_results)

        if stats:
            self.save_artifact("statistics.json", stats)

        # Collect metrics
        metrics = {
            "iterations": self.iterations,
            "successful_iterations": successful_iterations,
            "success_rate": (
                successful_iterations / self.iterations if self.iterations else 0
            ),
        }

        # Add stats to metrics
        if stats:
            metrics["statistics"] = stats

        # Store metrics in result
        if self.result:
            self.result.metrics = metrics

        return {"results": all_results, "statistics": stats, "metrics": metrics}

    def _extract_numerical_values(
        self, obj: Any, numerical_values: Dict[str, List[float]], prefix: str = ""
    ) -> None:
        """
        Recursively extract numerical values from a dictionary.

        Args:
            obj: The object to extract from
            numerical_values: Dictionary to store values in
            prefix: Prefix for nested keys
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Skip certain metadata keys
                if key in ("iteration", "success", "error", "error_details"):
                    continue

                # Build key with prefix
                full_key = f"{prefix}.{key}" if prefix else key

                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if full_key not in numerical_values:
                        numerical_values[full_key] = []
                    numerical_values[full_key].append(value)
                elif isinstance(value, (dict, list)):
                    self._extract_numerical_values(value, numerical_values, full_key)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                full_key = f"{prefix}[{i}]" if prefix else f"[{i}]"

                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    if full_key not in numerical_values:
                        numerical_values[full_key] = []
                    numerical_values[full_key].append(item)
                elif isinstance(item, (dict, list)):
                    self._extract_numerical_values(item, numerical_values, full_key)


class OptimizationExperiment(Experiment):
    """
    Experiment for optimizing parameters or code.
    """

    def __init__(
        self,
        objective_func: Callable,
        parameter_space: Dict[str, Tuple[Any, Any]],
        algorithm: str = "grid_search",
        max_iterations: int = 10,
        **kwargs,
    ):
        """
        Initialize an optimization experiment.

        Args:
            objective_func: Function to optimize (should return a score to maximize)
            parameter_space: Dictionary mapping parameter names to (min, max) or list of values
            algorithm: Optimization algorithm to use
            max_iterations: Maximum number of iterations
            **kwargs: Additional parameters for the base class
        """
        super().__init__(ExperimentType.OPTIMIZATION, **kwargs)

        self.objective_func = objective_func
        self.parameter_space = parameter_space
        self.algorithm = algorithm
        self.max_iterations = max_iterations

        # Save parameter space as an artifact
        self.save_artifact(
            "parameter_space.json", {k: str(v) for k, v in parameter_space.items()}
        )

    def _run_implementation(self) -> Dict[str, Any]:
        """
        Run the optimization and collect results.

        Returns:
            Dictionary of optimization results
        """
        self.logger.info(
            f"Running {self.algorithm} optimization with "
            f"max {self.max_iterations} iterations"
        )

        if self.algorithm == "grid_search":
            results = self._grid_search()
        elif self.algorithm == "random_search":
            results = self._random_search()
        else:
            raise ValueError(f"Unsupported optimization algorithm: {self.algorithm}")

        # Find the best parameters
        if results["evaluations"]:
            best_evaluation = max(results["evaluations"], key=lambda x: x["score"])
            results["best_parameters"] = best_evaluation["parameters"]
            results["best_score"] = best_evaluation["score"]

        # Save results
        self.save_artifact("optimization_results.json", results)

        # Collect metrics
        metrics = {
            "algorithm": self.algorithm,
            "iterations": len(results["evaluations"]),
            "best_score": results.get("best_score"),
            "parameters_evaluated": len(results["evaluations"]),
        }

        # Store metrics in result
        if self.result:
            self.result.metrics = metrics

        return results

    def _grid_search(self) -> Dict[str, Any]:
        """
        Perform grid search optimization.

        Returns:
            Dictionary of optimization results
        """
        import itertools

        # Generate the grid of parameter values
        param_values = []
        param_names = []

        for name, space in self.parameter_space.items():
            param_names.append(name)

            if (
                isinstance(space, (list, tuple))
                and len(space) == 2
                and all(isinstance(x, (int, float)) for x in space)
            ):
                min_val, max_val = space
                # For numeric ranges, create a linear space
                if isinstance(min_val, int) and isinstance(max_val, int):
                    # For integers, use a range
                    values = list(range(min_val, max_val + 1))
                else:
                    # For floats, create a linear space with 5 points
                    num_points = min(5, self.max_iterations)
                    step = (max_val - min_val) / (num_points - 1)
                    values = [min_val + i * step for i in range(num_points)]
            else:
                # For lists of values, use directly
                values = space

            param_values.append(values)

        # Generate all combinations
        combinations = list(itertools.product(*param_values))

        # Limit to max iterations
        combinations = combinations[: self.max_iterations]

        # Evaluate each combination
        evaluations = []

        for i, combination in enumerate(combinations):
            self.logger.debug(f"Evaluating combination {i+1}/{len(combinations)}")

            # Create parameter dictionary
            parameters = {name: value for name, value in zip(param_names, combination)}

            try:
                # Evaluate objective function
                score = self.objective_func(**parameters)

                evaluations.append(
                    {"parameters": parameters, "score": score, "iteration": i + 1}
                )

            except Exception as e:
                self.logger.error(f"Error evaluating parameters: {str(e)}")
                evaluations.append(
                    {
                        "parameters": parameters,
                        "score": None,
                        "error": str(e),
                        "iteration": i + 1,
                    }
                )

        return {
            "algorithm": "grid_search",
            "parameter_space": self.parameter_space,
            "evaluations": evaluations,
        }

    def _random_search(self) -> Dict[str, Any]:
        """
        Perform random search optimization.

        Returns:
            Dictionary of optimization results
        """
        import random

        evaluations = []

        for i in range(self.max_iterations):
            self.logger.debug(f"Iteration {i+1}/{self.max_iterations}")

            # Generate random parameters
            parameters = {}

            for name, space in self.parameter_space.items():
                if (
                    isinstance(space, (list, tuple))
                    and len(space) == 2
                    and all(isinstance(x, (int, float)) for x in space)
                ):
                    min_val, max_val = space
                    if isinstance(min_val, int) and isinstance(max_val, int):
                        # For integers, use randint
                        parameters[name] = random.randint(min_val, max_val)
                    else:
                        # For floats, use uniform
                        parameters[name] = random.uniform(min_val, max_val)
                else:
                    # For lists of values, choose randomly
                    parameters[name] = random.choice(space)

            try:
                # Evaluate objective function
                score = self.objective_func(**parameters)

                evaluations.append(
                    {"parameters": parameters, "score": score, "iteration": i + 1}
                )

            except Exception as e:
                self.logger.error(f"Error evaluating parameters: {str(e)}")
                evaluations.append(
                    {
                        "parameters": parameters,
                        "score": None,
                        "error": str(e),
                        "iteration": i + 1,
                    }
                )

        return {
            "algorithm": "random_search",
            "parameter_space": self.parameter_space,
            "evaluations": evaluations,
        }


class ParallelExperiment:
    """
    Runs multiple experiments in parallel.
    """

    def __init__(
        self, experiments: List[Experiment], max_workers: Optional[int] = None
    ):
        """
        Initialize a parallel experiment runner.

        Args:
            experiments: List of experiments to run in parallel
            max_workers: Maximum number of parallel workers (default: CPU count)
        """
        self.experiments = experiments
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.results: Dict[str, ExperimentResult] = {}

    def run(self) -> Dict[str, ExperimentResult]:
        """
        Run all experiments in parallel.

        Returns:
            Dictionary mapping experiment IDs to results
        """
        with multiprocessing.Pool(processes=self.max_workers) as pool:
            # Submit all experiments
            future_results = {
                exp.experiment_id: pool.apply_async(self._run_experiment, (exp,))
                for exp in self.experiments
            }

            # Collect results
            for exp_id, future in future_results.items():
                try:
                    self.results[exp_id] = future.get()
                except Exception as e:
                    logger.error(f"Error running experiment {exp_id}: {str(e)}")

                    # Create a failed result
                    self.results[exp_id] = ExperimentResult(
                        experiment_id=exp_id,
                        status=ExperimentStatus.FAILED,
                        start_time=time.time(),
                        end_time=time.time(),
                        error=str(e),
                    )

        return self.results

    def _run_experiment(self, experiment: Experiment) -> ExperimentResult:
        """
        Run a single experiment and return its result.

        Args:
            experiment: The experiment to run

        Returns:
            The experiment result
        """
        return experiment.run()

    def get_successful_results(self) -> Dict[str, ExperimentResult]:
        """
        Get only the successful experiment results.

        Returns:
            Dictionary mapping experiment IDs to successful results
        """
        return {
            exp_id: result
            for exp_id, result in self.results.items()
            if result.status == ExperimentStatus.COMPLETED
        }

    def get_failed_results(self) -> Dict[str, ExperimentResult]:
        """
        Get only the failed experiment results.

        Returns:
            Dictionary mapping experiment IDs to failed results
        """
        return {
            exp_id: result
            for exp_id, result in self.results.items()
            if result.status in (ExperimentStatus.FAILED, ExperimentStatus.TIMEOUT)
        }

    def summarize_results(self) -> Dict[str, Any]:
        """
        Generate a summary of all experiment results.

        Returns:
            Dictionary with result summary
        """
        total = len(self.results)
        successful = sum(
            1 for r in self.results.values() if r.status == ExperimentStatus.COMPLETED
        )
        failed = sum(
            1 for r in self.results.values() if r.status == ExperimentStatus.FAILED
        )
        timeout = sum(
            1 for r in self.results.values() if r.status == ExperimentStatus.TIMEOUT
        )

        return {
            "total_experiments": total,
            "successful": successful,
            "failed": failed,
            "timeout": timeout,
            "success_rate": successful / total if total else 0,
            "experiment_ids": list(self.results.keys()),
            "status_counts": {
                status.name: sum(1 for r in self.results.values() if r.status == status)
                for status in ExperimentStatus
            },
        }


class ExperimentManager:
    """
    Manages experiments, providing storage, retrieval, and analysis capabilities.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the experiment manager.

        Args:
            storage_dir: Directory for storing experiment data
        """
        self.storage_dir = Path(storage_dir or "experiments")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._experiments: Dict[str, Experiment] = {}
        self._results: Dict[str, ExperimentResult] = {}
        self._lock = threading.RLock()

    def create_code_experiment(
        self, code: str, language: ScriptLanguage, **kwargs
    ) -> CodeExecutionExperiment:
        """
        Create a code execution experiment.

        Args:
            code: The code to execute
            language: The language of the code
            **kwargs: Additional parameters for the experiment

        Returns:
            The created experiment
        """
        experiment = CodeExecutionExperiment(code=code, language=language, **kwargs)

        with self._lock:
            self._experiments[experiment.experiment_id] = experiment

        return experiment

    def create_simulation_experiment(
        self, simulation_func: Callable, parameters: Dict[str, Any], **kwargs
    ) -> SimulationExperiment:
        """
        Create a simulation experiment.

        Args:
            simulation_func: Function that implements the simulation
            parameters: Parameters for the simulation
            **kwargs: Additional parameters for the experiment

        Returns:
            The created experiment
        """
        experiment = SimulationExperiment(
            simulation_func=simulation_func, parameters=parameters, **kwargs
        )

        with self._lock:
            self._experiments[experiment.experiment_id] = experiment

        return experiment

    def create_optimization_experiment(
        self,
        objective_func: Callable,
        parameter_space: Dict[str, Tuple[Any, Any]],
        **kwargs,
    ) -> OptimizationExperiment:
        """
        Create an optimization experiment.

        Args:
            objective_func: Function to optimize
            parameter_space: Dictionary mapping parameter names to (min, max) or list of values
            **kwargs: Additional parameters for the experiment

        Returns:
            The created experiment
        """
        experiment = OptimizationExperiment(
            objective_func=objective_func, parameter_space=parameter_space, **kwargs
        )

        with self._lock:
            self._experiments[experiment.experiment_id] = experiment

        return experiment

    def run_experiment(self, experiment_id: str) -> ExperimentResult:
        """
        Run an experiment by ID.

        Args:
            experiment_id: ID of the experiment to run

        Returns:
            The experiment result

        Raises:
            ValueError: If the experiment ID is not found
        """
        with self._lock:
            experiment = self._experiments.get(experiment_id)

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        result = experiment.run()

        with self._lock:
            self._results[experiment_id] = result

        # Save the result
        self._save_result(result)

        return result

    def run_experiments_parallel(
        self, experiment_ids: List[str], max_workers: Optional[int] = None
    ) -> Dict[str, ExperimentResult]:
        """
        Run multiple experiments in parallel.

        Args:
            experiment_ids: List of experiment IDs to run
            max_workers: Maximum number of parallel workers

        Returns:
            Dictionary mapping experiment IDs to results

        Raises:
            ValueError: If any experiment ID is not found
        """
        with self._lock:
            experiments = []
            for exp_id in experiment_ids:
                experiment = self._experiments.get(exp_id)
                if not experiment:
                    raise ValueError(f"Experiment not found: {exp_id}")
                experiments.append(experiment)

        # Run experiments in parallel
        parallel_runner = ParallelExperiment(
            experiments=experiments, max_workers=max_workers
        )
        results = parallel_runner.run()

        # Save and store results
        with self._lock:
            for exp_id, result in results.items():
                self._results[exp_id] = result
                self._save_result(result)

        return results

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """
        Get an experiment by ID.

        Args:
            experiment_id: ID of the experiment

        Returns:
            The experiment, or None if not found
        """
        with self._lock:
            return self._experiments.get(experiment_id)

    def get_result(self, experiment_id: str) -> Optional[ExperimentResult]:
        """
        Get a result by experiment ID.

        Args:
            experiment_id: ID of the experiment

        Returns:
            The experiment result, or None if not found
        """
        with self._lock:
            # Check in-memory cache first
            result = self._results.get(experiment_id)

            # If not found, try to load from storage
            if not result:
                result = self._load_result(experiment_id)
                if result:
                    self._results[experiment_id] = result

            return result

    def get_all_results(self) -> Dict[str, ExperimentResult]:
        """
        Get all experiment results.

        Returns:
            Dictionary mapping experiment IDs to results
        """
        with self._lock:
            # Load all results from storage that aren't in memory
            result_files = list(self.storage_dir.glob("*.result"))

            for result_file in result_files:
                exp_id = result_file.stem
                if exp_id not in self._results:
                    result = self._load_result(exp_id)
                    if result:
                        self._results[exp_id] = result

            return dict(self._results)

    def _save_result(self, result: ExperimentResult) -> None:
        """
        Save an experiment result to storage.

        Args:
            result: The experiment result to save
        """
        result_file = self.storage_dir / f"{result.experiment_id}.result"

        with open(result_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

    def _load_result(self, experiment_id: str) -> Optional[ExperimentResult]:
        """
        Load an experiment result from storage.

        Args:
            experiment_id: ID of the experiment

        Returns:
            The experiment result, or None if not found
        """
        result_file = self.storage_dir / f"{experiment_id}.result"

        if not result_file.exists():
            return None

        try:
            with open(result_file, "r") as f:
                data = json.load(f)
                return ExperimentResult.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading result {experiment_id}: {str(e)}")
            return None

    def cleanup_experiments(
        self,
        experiment_ids: Optional[List[str]] = None,
        status_filter: Optional[Set[ExperimentStatus]] = None,
    ) -> int:
        """
        Clean up experiment resources.

        Args:
            experiment_ids: Optional list of experiment IDs to clean up
            status_filter: Optional set of statuses to filter by

        Returns:
            Number of experiments cleaned up
        """
        count = 0

        with self._lock:
            to_cleanup = []

            if experiment_ids:
                # Clean up specific experiments
                for exp_id in experiment_ids:
                    experiment = self._experiments.get(exp_id)
                    if experiment:
                        if status_filter is None or experiment.status in status_filter:
                            to_cleanup.append(experiment)
            else:
                # Clean up all experiments matching the filter
                for experiment in self._experiments.values():
                    if status_filter is None or experiment.status in status_filter:
                        to_cleanup.append(experiment)

            # Perform cleanup
            for experiment in to_cleanup:
                try:
                    experiment.cleanup()
                    count += 1
                except Exception as e:
                    logger.error(
                        f"Error cleaning up experiment {experiment.experiment_id}: {str(e)}"
                    )

        return count


# Singleton instance for global access
_experiment_manager_instance = None
_manager_lock = threading.Lock()


def get_experiment_manager() -> ExperimentManager:
    """
    Get or create the singleton instance of the ExperimentManager.

    Returns:
        The global ExperimentManager instance
    """
    global _experiment_manager_instance

    if _experiment_manager_instance is None:
        with _manager_lock:
            if _experiment_manager_instance is None:
                _experiment_manager_instance = ExperimentManager()

    return _experiment_manager_instance
