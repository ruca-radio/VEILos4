#!/usr/bin/env python3
"""
VEIL Unified Kernel Entry Point
================================

Integrates VEILos runtime (veil_core.py) with VEIL4 quantum-cognitive system (core/).
Provides a single, unified API for natural language intent → action execution.

Architecture:
  User Intent (natural language)
         ↓
  [Intent Parser] → Structured command
         ↓
  [Router] → Dispatch to VEIL4 or VEILos
         ↓
  [Executor] → Execute via appropriate subsystem
         ↓
  Result

This kernel serves as the foundation for all interface layers (TUI, Shell, Web).
"""

import json
import sys
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Import VEIL4 core system
from core.veil4_system import VEIL4
from core.parity.unified_interface import AgentType

# Import VEILos runtime
from veil_core import VEILosKernel



# Import cognitive stack and scaffold engine
from core.providers.cognitive_stack import (
    CognitiveStack,
    ModelLayer,
    ModelSpecialization,
)
from core.modification.scaffold_engine import ScaffoldEngine

class IntentParser:
    """
    Parses natural language intent into structured commands.

    Recognizes patterns like:
    - "create quantum state with options A, B, C"
    - "observe state X as agent Y"
    - "grant capability to read resource Z"
    - "load module quantum_observer.py"
    - "show system status"
    """

    def parse(self, intent: str) -> Dict[str, Any]:
        """
        Parse natural language intent into structured command.

        Args:
            intent: Natural language intent string

        Returns:
            Structured command dict with 'type', 'args', 'kwargs'
        """
        intent_lower = intent.lower().strip()

        # Quantum operations
        if "create quantum" in intent_lower or "superposition" in intent_lower:
            return {"type": "create_quantum", "intent": intent}

        if "observe" in intent_lower and "state" in intent_lower:
            return {"type": "observe_state", "intent": intent}

        if "grant" in intent_lower and "capability" in intent_lower:
            return {"type": "grant_capability", "intent": intent}

        # Agent operations
        if "register" in intent_lower and "agent" in intent_lower:
            return {"type": "register_agent", "intent": intent}

        if "list" in intent_lower and "agent" in intent_lower:
            return {"type": "list_agents", "intent": intent}

        # Module operations
        if "load" in intent_lower and "module" in intent_lower:
            return {"type": "load_module", "intent": intent}
        if any(kw in intent_lower for kw in ["scaffold", "build me", "create a", "add a", "generate"]):
            return {"type": "scaffold", "intent": intent}
        if any(kw in intent_lower for kw in ["think", "reason", "analyze", "cognitive"]):
            return {"type": "think", "intent": intent}
        if "stack" in intent_lower and any(kw in intent_lower for kw in ["info", "status", "layers", "show"]):
            return {"type": "stack_info", "intent": intent}
        if "template" in intent_lower and any(kw in intent_lower for kw in ["list", "show", "available"]):
            return {"type": "templates", "intent": intent}
        if "status" in intent_lower or "info" in intent_lower:
            return {"type": "status", "intent": intent}
        if "help" in intent_lower:
            return {"type": "help", "intent": intent}
        # Default: pass to VEILos command interpreter
        return {"type": "veilos_command", "intent": intent}

    def extract_args(self, intent: str, pattern: str) -> Dict[str, str]:
        """
        Extract arguments from intent using simple pattern matching.

        Args:
            intent: Intent string
            pattern: Pattern to match (e.g., "state_id", "agent_id")

        Returns:
            Extracted arguments
        """
        # Simple extraction - in production would use NLP
        words = intent.split()
        args = {}

        for i, word in enumerate(words):
            if word.lower() == pattern.lower() and i + 1 < len(words):
                args[pattern] = words[i + 1]

        return args


class VEILKernel:
    """
    Unified VEIL Kernel - Main orchestrator.

    Coordinates between:
    - VEIL4: Quantum-cognitive OS (core/)
    - VEILos: Token-interpreted runtime (veil_core.py)
    - Intent Parser: Natural language → structured commands

    Provides single execute() method for all operations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize unified VEIL kernel.

        Args:
            config: System configuration
        """
        self.config = config or {}

        # Initialize subsystems
        self.veil4 = VEIL4(config=self.config)
        self.veilos = VEILosKernel()
        self.parser = IntentParser()
        self.cognitive_stack = CognitiveStack()
        self.scaffold_engine = ScaffoldEngine()
        # System state
        self.running = False
        self.execution_history = []

    def start(self):
        """Start the unified kernel"""
        if self.running:
            return

        # Start VEIL4
        self.veil4.start()
        # Add default cognitive layers
        self.cognitive_stack.add_layer(
            ModelLayer(
                model_name="reasoning-primary",
                provider="mock",
                specialization=ModelSpecialization.REASONING,
                priority=100,
            )
        )
        self.cognitive_stack.add_layer(
            ModelLayer(
                model_name="creative-primary",
                provider="mock",
                specialization=ModelSpecialization.CREATIVE,
                priority=80,
            )
        )
        self.cognitive_stack.add_layer(
            ModelLayer(
                model_name="analysis-primary",
                provider="mock",
                specialization=ModelSpecialization.ANALYSIS,
                priority=90,
            )
        )
        # VEILos initializes on creation
        self.running = True
        return {
            "status": "success",
            "message": "VEIL Unified Kernel started",
            "subsystems": ["VEIL4", "VEILos", "CognitiveStack", "ScaffoldEngine"],
            "cognitive_layers": len(self.cognitive_stack.layers),
        }

    def shutdown(self):
        """Shutdown the unified kernel"""
        if not self.running:
            return

        # Shutdown VEIL4
        self.veil4.shutdown()

        self.running = False

        return {"status": "success", "message": "VEIL Unified Kernel shutdown"}

    def execute(self, intent: str, agent_id: str = "system") -> Dict[str, Any]:
        """
        Execute a user intent through the unified kernel.

        Main entry point: natural language intent → action execution.

        Args:
            intent: Natural language intent or command
            agent_id: Agent executing the intent

        Returns:
            Execution result with status and data
        """
        if not self.running:
            return {
                "status": "error",
                "message": "Kernel not running. Call start() first.",
            }

        try:
            # Parse intent
            command = self.parser.parse(intent)
            command_type = command.get("type")

            # Route to appropriate handler
            if command_type == "create_quantum":
                result = self._handle_create_quantum(intent, agent_id)

            elif command_type == "observe_state":
                result = self._handle_observe_state(intent, agent_id)

            elif command_type == "grant_capability":
                result = self._handle_grant_capability(intent, agent_id)

            elif command_type == "register_agent":
                result = self._handle_register_agent(intent, agent_id)

            elif command_type == "list_agents":
                result = self._handle_list_agents(agent_id)

            elif command_type == "load_module":
                result = self._handle_load_module(intent, agent_id)


            elif command_type == "scaffold":
                result = self._handle_scaffold(intent, agent_id)

            elif command_type == "think":
                result = self._handle_think(intent, agent_id)

            elif command_type == "stack_info":
                result = self._handle_stack_info(agent_id)

            elif command_type == "templates":
                result = self._handle_templates(agent_id)

            elif command_type == "status":
                result = self._handle_status(agent_id)

            elif command_type == "help":
                result = self._handle_help()

            elif command_type == "veilos_command":
                # Pass to VEILos command interpreter
                result = self.veilos.execute_command(intent)
                if not isinstance(result, dict):
                    result = {"status": "success", "data": result}
                elif "status" not in result:
                    result["status"] = "success"

            else:
                result = {
                    "status": "error",
                    "message": f"Unknown command type: {command_type}",
                }

            # Record execution
            self.execution_history.append(
                {
                    "intent": intent,
                    "agent_id": agent_id,
                    "command_type": command_type,
                    "result": result,
                }
            )

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Execution failed: {str(e)}",
                "intent": intent,
            }

    def _handle_create_quantum(self, intent: str, agent_id: str) -> Dict[str, Any]:
        """Handle quantum state creation"""
        # Try to extract a user-specified state ID from intent
        # Patterns: 'create quantum state <id>', 'create quantum state with options ...'
        words = intent.split()
        state_id = None
        states = []

        # Find 'state' keyword and extract ID
        for i, word in enumerate(words):
            if word.lower() == 'state' and i + 1 < len(words):
                candidate = words[i + 1]
                if candidate.lower() not in ('with', 'from', 'using', 'of'):
                    state_id = candidate
                break

        if not state_id:
            state_id = f"state_{len(self.veil4.quantum.superpositions)}"
        # Extract options from 'with options X, Y, Z' pattern
        intent_lower = intent.lower()
        if 'options' in intent_lower or 'with' in intent_lower:
            # Find everything after 'options' or last 'with'
            for marker in ('options', 'with'):
                idx = intent_lower.rfind(marker)
                if idx >= 0:
                    options_str = intent[idx + len(marker):].strip()
                    if options_str:
                        option_names = [o.strip() for o in options_str.replace(' and ', ',').split(',') if o.strip()]
                        if option_names:
                            prob = 1.0 / len(option_names)
                            states = [{"option": name, "probability": round(prob, 4)} for name in option_names]
                    break

        if not states:
            states = [
                {"option": "A", "probability": 0.5},
                {"option": "B", "probability": 0.5},
            ]

        self.veil4.create_quantum_state(state_id, states)
        return {
            "status": "success",
            "message": "Quantum state created",
            "state_id": state_id,
            "states": states,
        }

    def _handle_observe_state(self, intent: str, agent_id: str) -> Dict[str, Any]:
        """Handle quantum state observation"""
        # Extract state_id from intent (simple pattern matching)
        words = intent.split()
        state_id = None

        for i, word in enumerate(words):
            if word.lower() == "state" and i + 1 < len(words):
                state_id = words[i + 1]
                break

        if not state_id or state_id not in self.veil4.quantum.superpositions:
            return {
                "status": "error",
                "message": f"State not found: {state_id}",
                "available_states": list(self.veil4.quantum.superpositions.keys()),
            }

        result = self.veil4.observe_quantum_state(state_id, agent_id)

        return {
            "status": "success",
            "message": "State observed and collapsed",
            "state_id": state_id,
            "collapsed_to": result,
        }

    def _handle_grant_capability(self, intent: str, agent_id: str) -> Dict[str, Any]:
        """Handle capability granting"""
        # Simple example: grant read capability
        resource = "data/default"
        permissions = ["read"]

        token = self.veil4.grant_capability(
            resource=resource,
            permissions=permissions,
            agent_id=agent_id,
            duration_seconds=3600,
        )

        return {
            "status": "success",
            "message": "Capability granted",
            "resource": resource,
            "permissions": permissions,
            "token": token,
        }

    def _handle_register_agent(self, intent: str, agent_id: str) -> Dict[str, Any]:
        """Handle agent registration"""
        # Determine agent type from intent
        agent_type = AgentType.HUMAN if "user" in intent.lower() else AgentType.MODEL

        agent = self.veil4.register_agent(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=["read", "write"],
            metadata={"registered_via": "kernel"},
        )

        return {
            "status": "success",
            "message": "Agent registered",
            "agent_id": agent_id,
            "agent_type": agent_type.value,
        }

    def _handle_list_agents(self, agent_id: str) -> Dict[str, Any]:
        """Handle agent listing"""
        agents = [
            {
                "id": aid,
                "type": agent.agent_type.value,
                "capabilities": agent.capabilities,
            }
            for aid, agent in self.veil4.parity.agents.items()
        ]

        return {
            "status": "success",
            "message": f"Found {len(agents)} agents",
            "agents": agents,
        }

    def _handle_load_module(self, intent: str, agent_id: str) -> Dict[str, Any]:
        """Handle module loading via VEILos"""
        # Extract module name from intent
        words = intent.split()
        module_name = None

        for i, word in enumerate(words):
            if word.lower() == "module" and i + 1 < len(words):
                module_name = words[i + 1]
                break

        if not module_name:
            return {"status": "error", "message": "Module name not specified"}

        result = self.veilos.load_module(module_name)

        return {
            "status": result.get("status"),
            "message": result.get("message", "Module loaded"),
            "module": module_name,
            "data": result,
        }


    def _handle_scaffold(self, intent: str, agent_id: str) -> Dict[str, Any]:
        """Handle scaffold requests via ScaffoldEngine"""
        try:
            result = self.scaffold_engine.scaffold(intent)
            return {
                "status": "success" if result.success else "error",
                "message": result.message,
                "plan_id": result.plan_id,
                "phase": result.phase.value,
                "artifacts": result.artifacts,
                "errors": result.errors,
                "rollback_available": result.rollback_info is not None,
            }
        except Exception as e:
            return {"status": "error", "message": f"Scaffold failed: {str(e)}"}

    def _handle_think(self, intent: str, agent_id: str) -> Dict[str, Any]:
        """Handle cognitive processing requests"""
        result = self.cognitive_stack.process_prompt(intent)
        return {
            "status": "success",
            "message": "Cognitive processing complete",
            "consensus": result.get("consensus", ""),
            "confidence": result.get("confidence", 0.0),
            "layer_responses": result.get("layer_responses", []),
        }

    def _handle_stack_info(self, agent_id: str) -> Dict[str, Any]:
        """Handle cognitive stack info requests"""
        info = self.cognitive_stack.get_stack_info()
        return {
            "status": "success",
            "message": "Cognitive stack info",
            "stack": info,
        }

    def _handle_templates(self, agent_id: str) -> Dict[str, Any]:
        """Handle template listing requests"""
        templates = self.scaffold_engine.list_templates()
        return {
            "status": "success",
            "message": f"Available templates: {len(templates)}",
            "templates": templates,
        }

    def _handle_status(self, agent_id: str) -> Dict[str, Any]:
        """Handle status request"""
        veil4_status = self.veil4.get_system_status()
        veilos_status = self.veilos.status()
        stack_info = self.cognitive_stack.get_stack_info()
        return {
            "status": "success",
            "message": "System status",
            "kernel": {
                "running": self.running,
                "execution_count": len(self.execution_history),
            },
            "veil4": veil4_status,
            "veilos": veilos_status,
            "cognitive_stack": stack_info,
            "scaffold_engine": {
                "templates": list(self.scaffold_engine.list_templates().keys()),
            },
        }

    def _handle_help(self) -> Dict[str, Any]:
        """Handle help request"""
        return {
            "status": "success",
            "message": "VEIL Unified Kernel Help",
            "commands": {
                "quantum": [
                    "create quantum state with options A, B, C",
                    "observe state <state_id> as <agent_id>",
                ],
                "security": ["grant capability to <agent_id> for <resource>"],
                "agents": ["register agent <agent_id>", "list agents"],
                "modules": ["load module <module_name>"],
                "scaffold": [
                    "scaffold <description>",
                    "build me a <component>",
                    "create a <thing>",
                    "generate <code>",
                ],
                "cognitive": [
                    "think about <topic>",
                    "reason about <problem>",
                    "analyze <subject>",
                ],
                "stack": [
                    "show stack info",
                    "show available templates",
                ],
                "system": ["status", "help"],
            },
        }


def main():
    """Main entry point for VEIL kernel"""
    kernel = VEILKernel()
    kernel.start()

    # If arguments provided, execute them
    if len(sys.argv) > 1:
        intent = " ".join(sys.argv[1:])
        result = kernel.execute(intent)
        print(json.dumps(result, indent=2))
    else:
        # Interactive mode
        print("=" * 60)
        print("VEIL Unified Kernel v1.0")
        print("Type 'help' for commands, 'exit' to quit")
        print("=" * 60)
        print()

        while True:
            try:
                intent = input("veil> ").strip()

                if intent.lower() in ["exit", "quit"]:
                    kernel.shutdown()
                    print("VEIL Kernel shutdown")
                    break

                if not intent:
                    continue

                result = kernel.execute(intent)
                print(json.dumps(result, indent=2))
                print()

            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
