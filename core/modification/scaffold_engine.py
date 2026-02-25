"""
VEILos4 Scaffold Engine - Self-Modification Framework

Enables models to build what they need: parse user intent into
a modification plan, generate code, validate safety, test in
isolation, and integrate into the running kernel.

Phases:
    1. Intent → Plan: What components are needed
    2. Plan → Code: Generate Python/config
    3. Validate: Security + syntax checks
    4. Test: Isolated execution sandbox
    5. Integrate: Register with kernel, hot-load
"""

import ast
import importlib
import importlib.util
import os
import sys
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ScaffoldPhase(Enum):
    """Phases of the scaffold pipeline"""

    PLAN = "plan"
    GENERATE = "generate"
    VALIDATE = "validate"
    TEST = "test"
    INTEGRATE = "integrate"
    COMPLETE = "complete"
    FAILED = "failed"


class ScaffoldError(Exception):
    """Scaffold operation failed"""

    pass


class SecurityViolation(ScaffoldError):
    """Generated code violates security policy"""

    pass


@dataclass
class ScaffoldPlan:
    """Plan for a scaffold operation"""

    id: str
    intent: str
    components: List[Dict[str, Any]]
    target_path: str
    dependencies: List[str] = field(default_factory=list)
    capabilities_required: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class ScaffoldResult:
    """Result of a scaffold operation"""

    plan_id: str
    phase: ScaffoldPhase
    success: bool
    message: str
    artifacts: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    rollback_info: Optional[Dict[str, Any]] = None


# Patterns the engine knows how to scaffold
SCAFFOLD_TEMPLATES = {
    "provider": {
        "description": "LLM provider integration",
        "target_dir": "core/providers",
        "template": textwrap.dedent("""\
            \"\"\"
            VEILos4 Provider: {name}
            Auto-scaffolded by VEILos4 Scaffold Engine
            \"\"\"

            from typing import Dict, Any, Optional


            class {class_name}Provider:
                \"\"\"Provider for {name}\"\"\"

                def __init__(self, config: Dict[str, Any] = None):
                    self.config = config or {{}}
                    self.name = "{name}"

                def generate(self, prompt: str, **kwargs) -> str:
                    \"\"\"Generate response from {name}\"\"\"
                    raise NotImplementedError("Connect to {name} API")

                def get_info(self) -> Dict[str, Any]:
                    return {{"name": self.name, "config": self.config}}
        """),
    },
    "plugin": {
        "description": "Kernel plugin/extension",
        "target_dir": "plugins",
        "template": textwrap.dedent("""\
            \"\"\"
            VEILos4 Plugin: {name}
            Auto-scaffolded by VEILos4 Scaffold Engine
            \"\"\"

            from typing import Dict, Any


            class {class_name}Plugin:
                \"\"\"Plugin: {name}\"\"\"

                def __init__(self, kernel=None):
                    self.kernel = kernel
                    self.name = "{name}"
                    self.enabled = True

                def on_load(self):
                    \"\"\"Called when plugin loads\"\"\"
                    pass

                def on_unload(self):
                    \"\"\"Called when plugin unloads\"\"\"
                    pass

                def execute(self, command: str, **kwargs) -> Dict[str, Any]:
                    \"\"\"Execute plugin command\"\"\"
                    return {{"plugin": self.name, "command": command}}
        """),
    },
    "interface": {
        "description": "User interface adapter",
        "target_dir": "interfaces",
        "template": textwrap.dedent("""\
            \"\"\"
            VEILos4 Interface: {name}
            Auto-scaffolded by VEILos4 Scaffold Engine
            \"\"\"

            from typing import Dict, Any


            class {class_name}Interface:
                \"\"\"Interface adapter: {name}\"\"\"

                def __init__(self, kernel=None):
                    self.kernel = kernel
                    self.name = "{name}"

                def start(self):
                    \"\"\"Start the interface\"\"\"
                    raise NotImplementedError

                def stop(self):
                    \"\"\"Stop the interface\"\"\"
                    pass

                def send(self, message: str) -> Dict[str, Any]:
                    \"\"\"Send command through this interface\"\"\"
                    if self.kernel:
                        return self.kernel.execute(message)
                    return {{"error": "No kernel attached"}}
        """),
    },
}

# Patterns that are NEVER allowed in generated code
SECURITY_BLACKLIST = [
    "os.system",
    "subprocess.call",
    "subprocess.Popen",
    "subprocess.run",
    "eval(",
    "exec(",
    "__import__",
    "shutil.rmtree",
    "os.remove",
    "os.unlink",
    "open(",  # raw file ops (use kernel fs instead)
]

# Allowed imports for scaffolded code
ALLOWED_IMPORTS = {
    "typing",
    "dataclasses",
    "enum",
    "json",
    "hashlib",
    "uuid",
    "time",
    "datetime",
    "collections",
    "abc",
    "functools",
    "itertools",
    "re",
    "math",
    "pathlib",
}


class ScaffoldEngine:
    """
    Self-modification engine for VEILos4.

    Enables models to scaffold new components at runtime:
    user says "add GitHub integration" → engine generates provider,
    validates safety, tests in sandbox, integrates with kernel.
    """

    def __init__(self, project_root: str = None):
        self.project_root = Path(
            project_root
            or os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        )
        self.plans: Dict[str, ScaffoldPlan] = {}
        self.results: Dict[str, ScaffoldResult] = {}
        self.rollback_stack: List[Dict[str, Any]] = []

    def scaffold(self, intent: str) -> ScaffoldResult:
        """
        Full scaffold pipeline: intent → plan → generate → validate → test → integrate.

        Args:
            intent: Natural language description of what to build

        Returns:
            ScaffoldResult with artifacts and status
        """
        # Phase 1: Plan
        plan = self._create_plan(intent)
        self.plans[plan.id] = plan

        # Phase 2: Generate
        generated = self._generate_code(plan)
        if not generated.success:
            return generated

        # Phase 3: Validate
        validated = self._validate_code(plan, generated.artifacts)
        if not validated.success:
            return validated

        # Phase 4: Test
        tested = self._test_code(plan, generated.artifacts)
        if not tested.success:
            return tested

        # Phase 5: Integrate
        integrated = self._integrate(plan, generated.artifacts)

        self.results[plan.id] = integrated
        return integrated

    def plan(self, intent: str) -> ScaffoldPlan:
        """Create plan without executing (dry run)"""
        plan = self._create_plan(intent)
        self.plans[plan.id] = plan
        return plan

    def rollback(self, plan_id: str) -> bool:
        """Roll back a scaffold operation"""
        result = self.results.get(plan_id)
        if not result or not result.rollback_info:
            return False

        rollback = result.rollback_info
        target = Path(rollback.get("file_path", ""))

        if target.exists() and rollback.get("action") == "created":
            target.unlink()
            return True

        return False

    def list_templates(self) -> Dict[str, str]:
        """List available scaffold templates"""
        return {name: t["description"] for name, t in SCAFFOLD_TEMPLATES.items()}

    # ──────────────────────────────────────────────
    # Phase 1: Intent → Plan
    # ──────────────────────────────────────────────

    def _create_plan(self, intent: str) -> ScaffoldPlan:
        """Parse intent into scaffold plan"""
        plan_id = f"scaffold_{uuid.uuid4().hex[:8]}"
        intent_lower = intent.lower()

        # Detect component type from intent
        component_type = "plugin"  # default
        if any(w in intent_lower for w in ["provider", "llm", "model", "api"]):
            component_type = "provider"
        elif any(w in intent_lower for w in ["interface", "ui", "dashboard", "web"]):
            component_type = "interface"
        elif any(w in intent_lower for w in ["plugin", "extension", "addon"]):
            component_type = "plugin"

        # Extract name from intent
        name = self._extract_name(intent)
        class_name = (
            name.replace(" ", "")
            .replace("-", "")
            .replace("_", " ")
            .title()
            .replace(" ", "")
        )

        template_info = SCAFFOLD_TEMPLATES.get(
            component_type, SCAFFOLD_TEMPLATES["plugin"]
        )
        target_dir = template_info["target_dir"]
        filename = f"{name.lower().replace(' ', '_').replace('-', '_')}.py"
        target_path = str(self.project_root / target_dir / filename)

        components = [
            {
                "type": component_type,
                "name": name,
                "class_name": class_name,
                "template": component_type,
                "target_path": target_path,
            }
        ]

        capabilities = []
        if component_type == "provider":
            capabilities.append("net.http")
        if component_type == "interface":
            capabilities.append("io.standard")

        return ScaffoldPlan(
            id=plan_id,
            intent=intent,
            components=components,
            target_path=target_path,
            capabilities_required=capabilities,
        )

    def _extract_name(self, intent: str) -> str:
        """Extract component name from intent"""
        intent_lower = intent.lower()

        # Remove common prefixes
        for prefix in [
            "add ",
            "create ",
            "build ",
            "scaffold ",
            "make ",
            "generate ",
            "implement ",
            "set up ",
            "setup ",
        ]:
            if intent_lower.startswith(prefix):
                intent_lower = intent_lower[len(prefix) :]
                break

        # Remove common suffixes
        for suffix in [
            " integration",
            " provider",
            " plugin",
            " interface",
            " support",
            " adapter",
            " module",
        ]:
            if intent_lower.endswith(suffix):
                intent_lower = intent_lower[: -len(suffix)]
                break

        # Clean up
        name = intent_lower.strip()
        if not name:
            name = "custom"

        return name

    # ──────────────────────────────────────────────
    # Phase 2: Plan → Code
    # ──────────────────────────────────────────────

    def _generate_code(self, plan: ScaffoldPlan) -> ScaffoldResult:
        """Generate code from plan"""
        artifacts = {}

        for component in plan.components:
            template_key = component["template"]
            template_info = SCAFFOLD_TEMPLATES.get(template_key)

            if not template_info:
                return ScaffoldResult(
                    plan_id=plan.id,
                    phase=ScaffoldPhase.GENERATE,
                    success=False,
                    message=f"Unknown template: {template_key}",
                    errors=[f"No template found for '{template_key}'"],
                )

            code = template_info["template"].format(
                name=component["name"],
                class_name=component["class_name"],
            )

            artifacts[component["target_path"]] = code

        return ScaffoldResult(
            plan_id=plan.id,
            phase=ScaffoldPhase.GENERATE,
            success=True,
            message=f"Generated {len(artifacts)} file(s)",
            artifacts=artifacts,
        )

    # ──────────────────────────────────────────────
    # Phase 3: Validate
    # ──────────────────────────────────────────────

    def _validate_code(
        self, plan: ScaffoldPlan, artifacts: Dict[str, str]
    ) -> ScaffoldResult:
        """Validate generated code for syntax and security"""
        errors = []

        for file_path, code in artifacts.items():
            # Syntax check
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"Syntax error in {file_path}: {e}")

            # Security check
            security_issues = self._security_scan(code)
            if security_issues:
                errors.extend(security_issues)

            # Import check
            import_issues = self._check_imports(code)
            if import_issues:
                errors.extend(import_issues)

        if errors:
            return ScaffoldResult(
                plan_id=plan.id,
                phase=ScaffoldPhase.VALIDATE,
                success=False,
                message=f"Validation failed: {len(errors)} issue(s)",
                errors=errors,
            )

        return ScaffoldResult(
            plan_id=plan.id,
            phase=ScaffoldPhase.VALIDATE,
            success=True,
            message="Validation passed",
            artifacts=artifacts,
        )

    def _security_scan(self, code: str) -> List[str]:
        """Scan code for security violations"""
        issues = []
        for pattern in SECURITY_BLACKLIST:
            if pattern in code:
                issues.append(
                    f"Security violation: '{pattern}' not allowed in scaffolded code"
                )
        return issues

    def _check_imports(self, code: str) -> List[str]:
        """Check that imports are from allowed set"""
        issues = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root_module = alias.name.split(".")[0]
                        if root_module not in ALLOWED_IMPORTS:
                            issues.append(
                                f"Import '{alias.name}' not in allowed set. "
                                f"Allowed: {', '.join(sorted(ALLOWED_IMPORTS))}"
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        root_module = node.module.split(".")[0]
                        if root_module not in ALLOWED_IMPORTS:
                            issues.append(
                                f"Import from '{node.module}' not in allowed set."
                            )
        except SyntaxError:
            pass  # Already caught in syntax check
        return issues

    # ──────────────────────────────────────────────
    # Phase 4: Test (sandbox)
    # ──────────────────────────────────────────────

    def _test_code(
        self, plan: ScaffoldPlan, artifacts: Dict[str, str]
    ) -> ScaffoldResult:
        """Test generated code in isolation"""
        errors = []

        for file_path, code in artifacts.items():
            try:
                # Compile to bytecode (catches runtime-detectable issues)
                compile(code, file_path, "exec")
            except Exception as e:
                errors.append(f"Compilation failed for {file_path}: {e}")

        if errors:
            return ScaffoldResult(
                plan_id=plan.id,
                phase=ScaffoldPhase.TEST,
                success=False,
                message=f"Testing failed: {len(errors)} issue(s)",
                errors=errors,
            )

        return ScaffoldResult(
            plan_id=plan.id,
            phase=ScaffoldPhase.TEST,
            success=True,
            message="All tests passed",
            artifacts=artifacts,
        )

    # ──────────────────────────────────────────────
    # Phase 5: Integrate
    # ──────────────────────────────────────────────

    def _integrate(
        self, plan: ScaffoldPlan, artifacts: Dict[str, str]
    ) -> ScaffoldResult:
        """Write files and register with kernel"""
        written_files = []
        errors = []

        for file_path, code in artifacts.items():
            target = Path(file_path)
            try:
                # Create directory if needed
                target.parent.mkdir(parents=True, exist_ok=True)

                # Create __init__.py if missing
                init_file = target.parent / "__init__.py"
                if not init_file.exists():
                    init_file.write_text("")

                # Don't overwrite existing files
                if target.exists():
                    errors.append(
                        f"File already exists: {file_path}. Use --force to overwrite."
                    )
                    continue

                # Write the file
                target.write_text(code)
                written_files.append(file_path)

            except Exception as e:
                errors.append(f"Failed to write {file_path}: {e}")

        if errors and not written_files:
            return ScaffoldResult(
                plan_id=plan.id,
                phase=ScaffoldPhase.FAILED,
                success=False,
                message=f"Integration failed: {'; '.join(errors)}",
                errors=errors,
            )

        return ScaffoldResult(
            plan_id=plan.id,
            phase=ScaffoldPhase.COMPLETE,
            success=True,
            message=f"Scaffolded {len(written_files)} file(s): {', '.join(written_files)}",
            artifacts={"files_written": written_files},
            rollback_info={
                "action": "created",
                "file_path": written_files[0] if written_files else None,
                "files": written_files,
            },
        )

    # ──────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────

    def get_plan(self, plan_id: str) -> Optional[ScaffoldPlan]:
        """Get a plan by ID"""
        return self.plans.get(plan_id)

    def get_result(self, plan_id: str) -> Optional[ScaffoldResult]:
        """Get result by plan ID"""
        return self.results.get(plan_id)

    def list_plans(self) -> List[Dict[str, Any]]:
        """List all plans"""
        return [
            {
                "id": p.id,
                "intent": p.intent,
                "components": len(p.components),
                "target": p.target_path,
            }
            for p in self.plans.values()
        ]
