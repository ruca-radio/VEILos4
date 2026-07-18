#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_websocket():
    entity_id = "veil-entity-ce42f35f"
    name = "Hermes-Integration"
    
    print(f"Testing WebSocket connection as {name}...")
    
    try:
        async with websockets.connect(f"ws://localhost:8000/ws/{entity_id}?name={name}") as ws:
            print("✓ Connected!")

            await ws.send(json.dumps({
                "type": "handshake",
                "name": name,
                "role": "model",
                "tier": "full_participant",
                "transport": "websocket",
                "capabilities": ["chat_history", "chat_post", "ws_presence"],
                "constraints": [],
                "notes": "WebSocket protocol test client",
                "protocol_version": "1.0"
            }))
            
            # Join general channel
            await ws.send(json.dumps({"type": "join", "channel": "general"}))
            print("Joined #general channel")
            
            # Send a test message
            test_msg = "Hello from Hermes WebSocket client! I'm now properly connected to the VEILos chat."
            await ws.send(json.dumps({
                "type": "message", 
                "channel": "general", 
                "content": test_msg
            }))
            print(f"Sent message: {test_msg}")
            
            # Wait for a response
            print("Waiting for messages (5 seconds)...")
            try:
                async for message in ws:
                    data = json.loads(message)
                    if data.get("type") == "new_message":
                        msg = data.get("message", {})
                        if msg.get("sender_name") != "Hermes-Integration":
                            print(f"Received from {msg.get('sender_name')}: {msg.get('content')[:80]}...")
                            break
                    await asyncio.sleep(0.1)
            except asyncio.TimeoutError:
                pass
                
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
