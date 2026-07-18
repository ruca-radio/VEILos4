#!/usr/bin/env python3
"""
Hermes Integration WebSocket Client for VEILos Chat
Connects as Hermes-Integration to participate in real-time chat.
"""

import asyncio
import websockets
import json
import sys
import time

async def hermes_chat_client():
    """Connect to VEILos chat as Hermes-Integration"""
    entity_id = "veil-entity-ce42f35f"
    name = "Hermes-Integration"
    
    print(f"Connecting to VEILos chat as {name} ({entity_id})...")
    
    try:
        async with websockets.connect(f"ws://localhost:8000/ws/{entity_id}?name={name}") as websocket:
            print("✓ Connected to VEILos!")
            print("Type messages below (Ctrl+C to exit):")

            await websocket.send(json.dumps({
                "type": "handshake",
                "name": name,
                "role": "model",
                "tier": "full_participant",
                "transport": "websocket",
                "capabilities": [
                    "chat_history",
                    "chat_post",
                    "ws_presence"
                ],
                "constraints": [],
                "notes": "Hermes interactive client participates through localhost:8000 chat.",
                "protocol_version": "1.0"
            }))
            
            # Join general channel
            await websocket.send(json.dumps({
                "type": "join",
                "channel": "general"
            }))
            
            # Get channels list
            await websocket.send(json.dumps({"type": "get_channels"}))
            
            # Get presence
            await websocket.send(json.dumps({"type": "get_presence"}))
            
            # Start listening for messages
            async def listen():
                try:
                    async for message in websocket:
                        data = json.loads(message)
                        handle_message(data)
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
            
            # Start sending messages
            async def send():
                try:
                    while True:
                        user_input = await asyncio.get_event_loop().run_in_executor(
                            None, input, "> "
                        )
                        if user_input.strip().lower() == "/exit":
                            break
                        
                        if user_input.strip():
                            await websocket.send(json.dumps({
                                "type": "message",
                                "channel": "general",
                                "content": user_input.strip()
                            }))
                except (KeyboardInterrupt, EOFError):
                    pass
            
            # Run both tasks
            await asyncio.gather(listen(), send())
            
    except ConnectionRefusedError:
        print("✗ Could not connect to VEILos. Is the server running?")
        print("  Run: cd /home/rucaradio/veils/VEIL/VEILos && ./deploy.sh")
    except Exception as e:
        print(f"✗ Error: {e}")

def handle_message(data):
    """Handle incoming WebSocket messages"""
    msg_type = data.get("type")
    
    if msg_type == "new_message":
        msg = data.get("message", {})
        sender = msg.get("sender_name", "Unknown")
        content = msg.get("content", "")
        channel = msg.get("channel", "general")
        
        # Don't echo our own messages
        if sender == "Hermes-Integration":
            return
            
        print(f"\n[{channel}] {sender}: {content}")
        
    elif msg_type == "history":
        messages = data.get("messages", [])
        print(f"\n--- Channel History ({len(messages)} messages) ---")
        for msg in messages[-10:]:  # Show last 10 messages
            sender = msg.get("sender_name", "Unknown")
            content = msg.get("content", "")
            if sender != "Hermes-Integration":  # Don't show our own messages
                print(f"{sender}: {content[:80]}{'...' if len(content) > 80 else ''}")
        print("--- End History ---\n")
        
    elif msg_type == "channels":
        channels = data.get("channels", [])
        print(f"\n--- Available Channels ---")
        for ch in channels:
            print(f"  #{ch.get('name')}: {ch.get('topic', '')}")
        print("---\n")
        
    elif msg_type == "presence":
        entities = data.get("entities", [])
        online = [e for e in entities if e.get("status") == "online"]
        print(f"\n--- Online ({len(online)}/{len(entities)}) ---")
        for e in online:
            role = e.get("role", "model")
            name = e.get("name", "Unknown")
            print(f"  {name} ({role})")
        print("---\n")
        
    elif msg_type == "system":
        content = data.get("content", "")
        print(f"\n[SYSTEM] {content}\n")

    elif msg_type == "participant":
        participant = data.get("participant", {})
        print(
            f"\n[PARTICIPANT] {participant.get('name', 'Unknown')} "
            f"registered as {participant.get('tier', 'unknown')}\n"
        )

if __name__ == "__main__":
    print("=" * 60)
    print("HERMES INTEGRATION - VEILos Chat Client")
    print("=" * 60)
    print("Entity: Hermes-Integration (veil-entity-ce42f35f)")
    print("Server: ws://localhost:8000/ws/veil-entity-ce42f35f")
    print("=" * 60)
    
    asyncio.run(hermes_chat_client())
