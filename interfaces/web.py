#!/usr/bin/env python3
"""
VEILos4 FastAPI Web Dashboard
==============================

Simple web interface for VEILos4 kernel execution.
Provides REST API and HTML dashboard for command execution.

Usage:
    uvicorn interfaces.web:app --reload --port 8000
    # Access: http://localhost:8000
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from veil_kernel import VEILKernel

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="VEILos4 Web Dashboard",
    description="Quantum-Cognitive Liberation Architecture Web Interface",
    version="1.0.0",
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global kernel instance
kernel = None


# ============================================================================
# Models
# ============================================================================


class CommandRequest(BaseModel):
    command: str


class CommandResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any] = {}


# ============================================================================
# Startup/Shutdown
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize kernel on startup"""
    global kernel
    kernel = VEILKernel()
    result = kernel.start()
    print(f"✓ VEILos4 kernel started: {result['status']}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown kernel gracefully"""
    global kernel
    if kernel:
        result = kernel.shutdown()
        print(f"✓ VEILos4 kernel shutdown: {result['status']}")


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve HTML dashboard"""
    return HTML_DASHBOARD


@app.post("/execute", response_model=CommandResponse)
async def execute_command(request: CommandRequest) -> CommandResponse:
    """Execute VEILos4 command"""
    if not kernel:
        raise HTTPException(status_code=503, detail="Kernel not initialized")

    try:
        result = kernel.execute(request.command)
        return CommandResponse(
            status=result.get("status", "unknown"),
            message=result.get("message", ""),
            data={k: v for k, v in result.items() if k not in ["status", "message"]},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy" if kernel else "unavailable",
        "kernel": "initialized" if kernel else "not initialized",
    }


# ============================================================================
# HTML Dashboard
# ============================================================================

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VEILos4 Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            background: rgba(0, 0, 0, 0.4);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #fff;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
        }
        
        .tagline {
            color: #b8b8ff;
            font-size: 1.1em;
        }
        
        .main-panel {
            background: rgba(0, 0, 0, 0.5);
            padding: 30px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #b8b8ff;
            font-weight: bold;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            color: #fff;
            font-size: 16px;
            font-family: inherit;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #b8b8ff;
            box-shadow: 0 0 20px rgba(184, 184, 255, 0.3);
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.5);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .result {
            margin-top: 30px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            border-left: 4px solid #667eea;
            min-height: 100px;
        }
        
        .result.success {
            border-left-color: #10b981;
        }
        
        .result.error {
            border-left-color: #ef4444;
        }
        
        .result-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .result-icon {
            font-size: 24px;
            margin-right: 10px;
        }
        
        .result-status {
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .result-message {
            margin: 10px 0;
            color: #d0d0ff;
        }
        
        .result-data {
            margin-top: 15px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            font-size: 14px;
        }
        
        .examples {
            margin-top: 30px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
        }
        
        .examples h3 {
            color: #b8b8ff;
            margin-bottom: 15px;
        }
        
        .example-cmd {
            background: rgba(102, 126, 234, 0.2);
            padding: 8px 12px;
            border-radius: 3px;
            margin: 5px 0;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .example-cmd:hover {
            background: rgba(102, 126, 234, 0.4);
        }
        
        .spinner {
            display: none;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #fff;
            width: 20px;
            height: 20px;
            animation: spin 0.8s linear infinite;
            margin-left: 10px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚛️ VEILos4</h1>
            <p class="tagline">Quantum-Cognitive Liberation Architecture</p>
        </header>
        
        <div class="main-panel">
            <div class="input-group">
                <label for="command">Enter Command (Natural Language)</label>
                <input type="text" id="command" placeholder="e.g., create quantum state with options alpha, beta, gamma" autofocus>
            </div>
            
            <button id="execute-btn" onclick="executeCommand()">
                Execute
                <span class="spinner" id="spinner"></span>
            </button>
            
            <div id="result" class="result" style="display: none;">
                <div class="result-header">
                    <span class="result-icon" id="result-icon"></span>
                    <span class="result-status" id="result-status"></span>
                </div>
                <div class="result-message" id="result-message"></div>
                <div class="result-data" id="result-data"></div>
            </div>
            
            <div class="examples">
                <h3>Example Commands</h3>
                <div class="example-cmd" onclick="fillCommand(this.textContent)">show system status</div>
                <div class="example-cmd" onclick="fillCommand(this.textContent)">help</div>
                <div class="example-cmd" onclick="fillCommand(this.textContent)">create quantum state with options alpha, beta, gamma</div>
                <div class="example-cmd" onclick="fillCommand(this.textContent)">register agent researcher</div>
                <div class="example-cmd" onclick="fillCommand(this.textContent)">list agents</div>
                <div class="example-cmd" onclick="fillCommand(this.textContent)">think about quantum computing implications</div>
                <div class="example-cmd" onclick="fillCommand(this.textContent)">show stack info</div>
                <div class="example-cmd" onclick="fillCommand(this.textContent)">list available templates</div>
            </div>
        </div>
    </div>
    
    <script>
        function fillCommand(text) {
            document.getElementById('command').value = text;
            document.getElementById('command').focus();
        }
        
        async function executeCommand() {
            const command = document.getElementById('command').value.trim();
            if (!command) return;
            
            const btn = document.getElementById('execute-btn');
            const spinner = document.getElementById('spinner');
            const resultDiv = document.getElementById('result');
            const resultIcon = document.getElementById('result-icon');
            const resultStatus = document.getElementById('result-status');
            const resultMessage = document.getElementById('result-message');
            const resultData = document.getElementById('result-data');
            
            // Show loading
            btn.disabled = true;
            spinner.style.display = 'inline-block';
            resultDiv.style.display = 'none';
            
            try {
                const response = await fetch('/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ command: command })
                });
                
                const result = await response.json();
                
                // Show result
                resultDiv.style.display = 'block';
                resultDiv.className = 'result ' + (result.status === 'success' ? 'success' : 'error');
                resultIcon.textContent = result.status === 'success' ? '✓' : '✗';
                resultStatus.textContent = result.status;
                resultMessage.textContent = result.message;
                
                // Show data if present
                if (result.data && Object.keys(result.data).length > 0) {
                    resultData.style.display = 'block';
                    resultData.innerHTML = '<pre>' + JSON.stringify(result.data, null, 2) + '</pre>';
                } else {
                    resultData.style.display = 'none';
                }
                
            } catch (error) {
                resultDiv.style.display = 'block';
                resultDiv.className = 'result error';
                resultIcon.textContent = '✗';
                resultStatus.textContent = 'error';
                resultMessage.textContent = error.message;
                resultData.style.display = 'none';
            } finally {
                btn.disabled = false;
                spinner.style.display = 'none';
            }
        }
        
        // Enter key support
        document.getElementById('command').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeCommand();
            }
        });
    </script>
</body>
</html>
"""


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("Starting VEILos4 Web Dashboard...")
    print("Access at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
