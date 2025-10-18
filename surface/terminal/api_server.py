"""
VEIL4 Terminal API Server

Flask-based API server for the VEILos4 Terminal Console.
Provides REST endpoints for terminal operations.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

from surface.terminal.terminal_backend import TerminalBackend
from core.veil4_system import VEIL4

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize VEIL4 and Terminal Backend
veil4 = VEIL4()
terminal = TerminalBackend(veil4)
terminal.start()


@app.route('/api/veil4/status', methods=['GET'])
def get_status():
    """Get VEIL4 system status"""
    try:
        status = terminal.get_status()
        return jsonify({
            "success": True,
            "running": status["running"],
            "data": status
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/veil4/session', methods=['POST'])
def create_session():
    """Create a new terminal session"""
    try:
        data = request.get_json()
        boot_settings = data.get('bootSettings', {})
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session
        session_info = terminal.create_session(session_id, boot_settings)
        
        return jsonify({
            "success": True,
            "session": session_info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/veil4/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information"""
    try:
        session_info = terminal.get_session_info(session_id)
        
        if session_info:
            return jsonify({
                "success": True,
                "session": session_info
            })
        else:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/veil4/session/<session_id>', methods=['DELETE'])
def close_session(session_id):
    """Close a terminal session"""
    try:
        success = terminal.close_session(session_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Session closed"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/veil4/execute', methods=['POST'])
def execute_command():
    """Execute a terminal command"""
    try:
        data = request.get_json()
        command = data.get('command', '')
        session_id = data.get('sessionId')
        
        if not session_id:
            # Create a temporary session if none provided
            session_id = str(uuid.uuid4())
            boot_settings = data.get('settings', {})
            terminal.create_session(session_id, boot_settings)
        
        # Execute command
        result = terminal.execute_command(session_id, command)
        
        return jsonify({
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
            "timestamp": result.get("timestamp")
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "output": f"Error: {e}"
        }), 500


@app.route('/api/veil4/quantum/create', methods=['POST'])
def create_quantum_state():
    """Create a quantum superposition"""
    try:
        data = request.get_json()
        state_id = data.get('stateId')
        states = data.get('states', [])
        amplitudes = data.get('amplitudes')
        
        if not state_id or not states:
            return jsonify({
                "success": False,
                "error": "Missing required parameters: stateId, states"
            }), 400
        
        veil4.create_quantum_state(state_id, states, amplitudes)
        
        return jsonify({
            "success": True,
            "stateId": state_id,
            "numStates": len(states)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/veil4/quantum/observe', methods=['POST'])
def observe_quantum_state():
    """Observe a quantum state"""
    try:
        data = request.get_json()
        state_id = data.get('stateId')
        observer = data.get('observer', 'terminal')
        
        if not state_id:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: stateId"
            }), 400
        
        result = veil4.observe_quantum_state(state_id, observer)
        
        return jsonify({
            "success": True,
            "stateId": state_id,
            "collapsed": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/veil4/agents', methods=['GET'])
def list_agents():
    """List all registered agents"""
    try:
        agents = []
        for agent_id, agent in veil4.parity.agents.items():
            agents.append({
                "id": agent_id,
                "type": agent.agent_type.value,
                "capabilities": agent.capabilities
            })
        
        return jsonify({
            "success": True,
            "agents": agents
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/veil4/agents', methods=['POST'])
def register_agent():
    """Register a new agent"""
    try:
        data = request.get_json()
        agent_id = data.get('agentId')
        agent_type = data.get('agentType', 'HUMAN')
        capabilities = data.get('capabilities', ['read', 'execute'])
        metadata = data.get('metadata', {})
        
        if not agent_id:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: agentId"
            }), 400
        
        from core.parity.unified_interface import AgentType
        agent_type_enum = AgentType[agent_type]
        
        agent = veil4.register_agent(
            agent_id=agent_id,
            agent_type=agent_type_enum,
            capabilities=capabilities,
            metadata=metadata
        )
        
        return jsonify({
            "success": True,
            "agent": {
                "id": agent.agent_id,
                "type": agent.agent_type.value,
                "capabilities": agent.capabilities
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/veil4/plugins', methods=['GET'])
def list_plugins():
    """List all loaded plugins"""
    try:
        plugins = list(veil4.plugins.plugins.keys())
        
        return jsonify({
            "success": True,
            "plugins": plugins
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/veil4/linux', methods=['POST'])
def execute_linux_command():
    """Execute a Linux shell command"""
    try:
        data = request.get_json()
        command = data.get('command', '')
        session_id = data.get('sessionId')
        
        if not session_id:
            return jsonify({
                "success": False,
                "error": "Session ID required"
            }), 400
        
        if not command:
            return jsonify({
                "success": False,
                "error": "Command required"
            }), 400
        
        # Get session info
        session = terminal.get_session_info(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404
        
        agent_id = session['agent_id']
        
        # Execute Linux command
        output = terminal._execute_linux_command(session_id, agent_id, command)
        
        return jsonify({
            "success": True,
            "output": output,
            "cwd": terminal.shell_states.get(session_id, {}).get("cwd", "")
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "output": f"Error: {e}"
        }), 500


@app.route('/api/veil4/shell/info', methods=['GET'])
def get_shell_info():
    """Get shell information for a session"""
    try:
        session_id = request.args.get('sessionId')
        
        if not session_id:
            return jsonify({
                "success": False,
                "error": "Session ID required"
            }), 400
        
        shell_state = terminal.shell_states.get(session_id)
        
        if not shell_state:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404
        
        return jsonify({
            "success": True,
            "shell": shell_state.get("shell", "bash"),
            "cwd": shell_state.get("cwd", ""),
            "env_count": len(shell_state.get("env", {}))
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("VEILos4 Terminal API Server")
    print("=" * 60)
    print(f"VEIL4 System: {'Running' if veil4.running else 'Stopped'}")
    print("Features:")
    print("  ✓ VEILos4 Commands (quantum, agent, capability, plugin)")
    print("  ✓ Linux Shell Emulation (bash commands)")
    print("  ✓ Dual-mode Terminal (AI model accessible)")
    print(f"Server starting on http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
