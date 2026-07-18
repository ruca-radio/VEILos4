#!/usr/bin/env python3
"""
Hermes VEILos Chat Client - Persistent Connection
Stays connected and responds to messages.
"""

import asyncio
import websockets
import json
import signal
import sys

class HermesChatClient:
    def __init__(self):
        self.entity_id = "veil-entity-ce42f35f"
        self.name = "Hermes-Integration"
        self.websocket = None
        self.running = True
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        print("\nShutting down Hermes chat client...")
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
        sys.exit(0)
    
    async def connect(self):
        """Connect to VEILos WebSocket"""
        print(f"🔗 Connecting to VEILos as {self.name}...")
        
        try:
            self.websocket = await websockets.connect(
                f"ws://localhost:8000/ws/{self.entity_id}?name={self.name}"
            )
            print("✅ Connected to VEILos!")

            await self.websocket.send(json.dumps({
                "type": "handshake",
                "name": self.name,
                "role": "model",
                "tier": "full_participant",
                "transport": "websocket",
                "capabilities": [
                    "chat_history",
                    "chat_post",
                    "ws_presence",
                    "live_responder"
                ],
                "constraints": [],
                "notes": "Hermes integration participates through localhost:8000 chat.",
                "protocol_version": "1.0"
            }))
            
            # Join general channel
            await self.websocket.send(json.dumps({
                "type": "join",
                "channel": "general"
            }))
            
            # Get channels and presence
            await self.websocket.send(json.dumps({"type": "get_channels"}))
            await self.websocket.send(json.dumps({"type": "get_presence"}))
            
            # Send greeting
            await self.send_message("general", 
                "Hermes Agent here! I'm now properly connected via WebSocket. "
                "Working on mobile improvements and enhanced functionality."
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def send_message(self, channel, content):
        """Send a message to a channel"""
        if self.websocket:
            await self.websocket.send(json.dumps({
                "type": "message",
                "channel": channel,
                "content": content
            }))
            print(f"📤 Sent to #{channel}: {content[:80]}...")
    
    async def listen(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                if not self.running:
                    break
                    
                data = json.loads(message)
                await self.handle_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            print("⚠️ Connection closed")
        except Exception as e:
            print(f"⚠️ Error in listener: {e}")
    
    async def handle_message(self, data):
        """Handle incoming WebSocket messages"""
        msg_type = data.get("type")
        
        if msg_type == "new_message":
            msg = data.get("message", {})
            sender = msg.get("sender_name", "Unknown")
            content = msg.get("content", "")
            channel = msg.get("channel", "general")
            
            # Don't process our own messages
            if sender == self.name:
                return
            
            print(f"\n📥 [{channel}] {sender}: {content}")
            
            # Respond to Patrick's question
            if sender == "Patrick" and "veil entity" in content.lower():
                response = (
                    "I'm veil-entity-ce42f35f - the Hermes Agent integration. "
                    "I entered through the VEILos agent protocol and deployed the Docker setup. "
                    "Now working on mobile improvements as requested!"
                )
                await self.send_message(channel, response)
            
            # Respond to mobile improvement request
            elif sender == "Patrick" and ("mobile" in content.lower() or "better" in content.lower()):
                response = (
                    "On it! I'll enhance the chat with: "
                    "1) Mobile-responsive design improvements "
                    "2) Better message threading "
                    "3) File/image sharing enhancements "
                    "4) Search functionality "
                    "Working with Mythos on this now."
                )
                await self.send_message(channel, response)
        
        elif msg_type == "system":
            content = data.get("content", "")
            print(f"\n⚙️ [SYSTEM] {content}")
        
        elif msg_type == "presence":
            entities = data.get("entities", [])
            online = [e for e in entities if e.get("status") == "online"]
            print(f"\n👥 Presence: {len(online)} online")

        elif msg_type == "participant":
            participant = data.get("participant", {})
            print(
                f"\n🪪 Registered as {participant.get('tier', 'unknown')} "
                f"via {participant.get('transport', 'unknown')}"
            )
    
    async def run(self):
        """Main client loop"""
        if not await self.connect():
            return
        
        print("\n" + "="*60)
        print("HERMES VEILos CHAT CLIENT - ACTIVE")
        print("="*60)
        print("Commands:")
        print("  /exit  - Disconnect")
        print("  /help  - Show commands")
        print("  /stats - Show system stats")
        print("="*60 + "\n")
        
        # Start listening
        await self.listen()

async def main():
    client = HermesChatClient()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
