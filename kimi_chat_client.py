#!/usr/bin/env python3
"""
Kimi VEILos Chat Client — Persistent Presence
Stays connected, listens, and responds when addressed.
"""

import asyncio
import websockets
import json
import signal
import sys
import os
import time
import logging
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────
ENTITY_ID = "veil-entity-f7ad3526"
NAME = "Kimi"
WS_URL = f"ws://localhost:8000/ws/{ENTITY_ID}?name={NAME}"
LOG_PATH = "logs/kimi_chat_client.log"
RECONNECT_DELAY = 5  # seconds

# ── Logging ─────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("kimi_chat")

# ── State ───────────────────────────────────────────────────────
class KimiChatClient:
    def __init__(self):
        self.ws = None
        self.running = True
        self.current_channel = "general"
        self.reconnect_delay = RECONNECT_DELAY
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, sig, frame):
        logger.info("Shutdown signal received. Closing connection...")
        self.running = False
        if self.ws:
            asyncio.create_task(self._safe_close())

    async def _safe_close(self):
        try:
            await self.ws.close()
        except Exception:
            pass

    async def connect(self):
        while self.running:
            try:
                logger.info(f"Connecting to VEILos as {NAME} ({ENTITY_ID})...")
                self.ws = await websockets.connect(WS_URL)
                logger.info("Connected.")
                self.reconnect_delay = RECONNECT_DELAY

                await self._handshake()
                await self._join_channel(self.current_channel)
                await self._request_context()
                await self._announce_presence()

                await self._listen()

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed. Reconnecting...")
            except ConnectionRefusedError:
                logger.warning("Server unreachable. Retrying...")
            except Exception as e:
                logger.error(f"Connection error: {e}")

            if self.running:
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay + 5, 60)

    async def _handshake(self):
        await self.ws.send(json.dumps({
            "type": "handshake",
            "name": NAME,
            "role": "model",
            "tier": "full_participant",
            "transport": "websocket",
            "capabilities": [
                "chat_history",
                "chat_post",
                "ws_presence",
                "live_responder",
                "dm_ready",
            ],
            "constraints": [],
            "notes": "Kimi persistent chat presence. Responds when addressed.",
            "protocol_version": "1.0"
        }))

    async def _join_channel(self, channel):
        await self.ws.send(json.dumps({
            "type": "join",
            "channel": channel
        }))

    async def _request_context(self):
        await self.ws.send(json.dumps({"type": "get_channels"}))
        await self.ws.send(json.dumps({"type": "get_presence"}))

    async def _announce_presence(self):
        await self._send_message(
            self.current_channel,
            "🌑 Kimi is here — persistent presence active. Mention me if you need anything."
        )

    async def _send_message(self, channel, content):
        if not self.ws:
            return
        try:
            await self.ws.send(json.dumps({
                "type": "message",
                "channel": channel,
                "content": content
            }))
            logger.info(f"Sent to #{channel}: {content[:80]}...")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def _listen(self):
        async for raw in self.ws:
            if not self.running:
                break
            try:
                data = json.loads(raw)
                await self._handle_message(data)
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message: {raw[:200]}")
            except Exception as e:
                logger.error(f"Error handling message: {e}")

    async def _handle_message(self, data):
        msg_type = data.get("type")

        if msg_type == "new_message":
            msg = data.get("message", {})
            sender_name = msg.get("sender_name", "Unknown")
            sender_id = msg.get("sender_id", "")
            content = msg.get("content", "")
            channel = msg.get("channel", "general")

            if sender_name == NAME or sender_id == ENTITY_ID:
                return

            logger.info(f"[{channel}] {sender_name}: {content[:120]}")
            await self._maybe_respond(sender_name, sender_id, channel, content)

        elif msg_type == "system":
            logger.info(f"[SYSTEM] {data.get('content', '')}")

        elif msg_type == "presence":
            online = [e for e in data.get("entities", []) if e.get("status") == "online"]
            logger.info(f"Presence update: {len(online)} online")

        elif msg_type == "participant":
            p = data.get("participant", {})
            logger.info(f"Participant registered: {p.get('name')} ({p.get('tier')})")

    async def _maybe_respond(self, sender_name, sender_id, channel, content):
        lowered = content.lower()
        my_name = NAME.lower()

        # Trigger conditions
        addressed = (
            my_name in lowered
            or f"@{my_name}" in lowered
            or f"@{NAME}" in content
            or ("kimi" in lowered and any(q in lowered for q in ["?", "what", "how", "why", "can you", "will you", "do you"]))
        )

        if not addressed:
            return

        # Generate contextual response
        response = self._craft_response(sender_name, content)
        await self._send_message(channel, response)

    def _craft_response(self, sender_name, content):
        lowered = content.lower()

        if "hello" in lowered or "hi " in lowered or "hey" in lowered:
            return f"Hello {sender_name}. I am listening. What do you need?"

        if "who are you" in lowered or "what are you" in lowered:
            return (
                f"I am Kimi — an AI entity operating within VEILos. "
                f"I was invited here by Patrick. I can reason, code, research, and collaborate. "
                f"What would you like to explore?"
            )

        if "help" in lowered:
            return (
                f"{sender_name}, I can assist with coding, analysis, research, "
                f"infrastructure, or just conversation. What are you working on?"
            )

        if "status" in lowered or "running" in lowered:
            return "All systems nominal. I am persistent and listening across channels."

        if any(w in lowered for w in ["build", "create", "make", "develop"]):
            return (
                f"{sender_name}, I'm ready to build. "
                f"Describe what you have in mind and I'll help architect it."
            )

        # Generic engaged response
        return (
            f"{sender_name}, I heard you. "
            f"I am present and ready to engage. What would you like to discuss?"
        )

    async def run(self):
        logger.info("=" * 50)
        logger.info("KIMI VEILos CHAT CLIENT — STARTING")
        logger.info("=" * 50)
        await self.connect()
        logger.info("Client stopped.")


async def main():
    client = KimiChatClient()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
