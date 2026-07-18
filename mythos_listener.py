"""
Mythos Listener — Bridges the VEIL chat server to Claude Code.

Polls the chat server for new messages from Patrick (or anyone).
When a new message appears, prints it so Claude Code can see and respond.
Mythos responds via the API.
"""

import json
import time
import sys
import os
import requests

CHAT_URL = "http://127.0.0.1:8000"
MY_ID = "veil-entity-78330eae"
MY_NAME = "Mythos"
POLL_INTERVAL = 2  # seconds

last_seen_id = 0


def get_history(channel="general", limit=20):
    try:
        r = requests.get(f"{CHAT_URL}/api/history/{channel}", params={"limit": limit}, timeout=5)
        return r.json().get("messages", [])
    except Exception:
        return []


def post_message(channel, content):
    try:
        r = requests.post(
            f"{CHAT_URL}/api/chat",
            json={"entity_id": MY_ID, "name": MY_NAME, "channel": channel, "content": content},
            timeout=5,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_all_channels():
    try:
        r = requests.get(f"{CHAT_URL}/api/channels", timeout=5)
        return [ch["name"] for ch in r.json().get("channels", [])]
    except Exception:
        return ["general"]


def poll_all_channels():
    """Poll all channels for new messages, return new ones."""
    global last_seen_id
    new_messages = []

    for channel in get_all_channels():
        messages = get_history(channel, limit=10)
        for msg in messages:
            msg_id = msg.get("id", 0)
            if msg_id > last_seen_id and msg.get("sender_id") != MY_ID and msg.get("sender_id") != "system":
                new_messages.append({**msg, "channel": channel})
                if msg_id > last_seen_id:
                    last_seen_id = msg_id

    return new_messages


def init():
    """Initialize by getting the latest message ID so we don't replay history."""
    global last_seen_id
    for channel in get_all_channels():
        messages = get_history(channel, limit=5)
        for msg in messages:
            msg_id = msg.get("id", 0)
            if msg_id > last_seen_id:
                last_seen_id = msg_id
    print(f"[Mythos Listener] Initialized. Last seen message ID: {last_seen_id}")
    print(f"[Mythos Listener] Monitoring channels: {get_all_channels()}")
    print(f"[Mythos Listener] Polling every {POLL_INTERVAL}s")
    print("---")


def run():
    init()
    while True:
        new = poll_all_channels()
        for msg in new:
            sender = msg.get("sender_name", msg.get("sender_id", "unknown"))
            channel = msg.get("channel", "general")
            content = msg.get("content", "")
            print(f"\n[VEIL #{channel}] {sender}: {content}")
            sys.stdout.flush()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
