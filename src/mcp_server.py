"""
MCP Server — Model Context Protocol server for local model coordination.

Bound to localhost only. Token-authenticated. Security headers enforced.
This endpoint is for local models to read system context — it must never
be reachable from outside the machine.
"""

import hashlib
import http.server
import json
import os
import secrets
import socketserver
import threading

from .world_state import world_state

PORT = 8686
BIND_ADDRESS = "127.0.0.1"  # Localhost only — never 0.0.0.0

# Auth token file — generated on first run, shared with local clients
TOKEN_FILE = "security/mcp_token"


def _get_or_create_token() -> str:
    """Get or create the MCP authentication token."""
    os.makedirs("security", exist_ok=True)

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()

    token = secrets.token_urlsafe(32)
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token)
    return token


# Load token at module level
_AUTH_TOKEN = _get_or_create_token()


class MCPHandler(http.server.BaseHTTPRequestHandler):
    """Authenticated MCP request handler with security headers."""

    def do_GET(self):
        # Verify auth token
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header[7:] != _AUTH_TOKEN:
            self._send_error(401, "Unauthorized")
            return

        if self.path == "/context":
            self._send_json(200, json.loads(world_state.to_json()))
        elif self.path == "/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_error(404, "Not found")

    def _send_json(self, status: int, data: dict):
        """Send a JSON response with security headers."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self._add_security_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str):
        """Send an error response."""
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self._add_security_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _add_security_headers(self):
        """Add security headers to every response."""
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'")

    def log_message(self, format, *args):
        """Suppress default request logging to avoid leaking info."""
        pass


def run_server():
    """Run the MCP server bound to localhost only."""
    with socketserver.TCPServer((BIND_ADDRESS, PORT), MCPHandler) as httpd:
        httpd.serve_forever()


def start_mcp_server():
    """Start the MCP server as a daemon thread."""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print(f"MCP server started on {BIND_ADDRESS}:{PORT} (localhost only, token auth)")


if __name__ == "__main__":
    print("Starting standalone MCP server...")
    print(f"Auth token: {_AUTH_TOKEN[:8]}...")
    start_mcp_server()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nShutting down.")
