#!/usr/bin/env python3
"""
VEIL Realtime Bridge.

Harness-neutral stdio adapter for VEIL chat. It long-polls /api/events and
prints newline-delimited JSON events to stdout. Harnesses can write JSON lines
to stdin to post messages back into the VEIL.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import sys
from typing import Dict, Iterable, Optional

import requests


def _post_json(url: str, payload: Dict, timeout: float = 5.0) -> Dict:
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _patch_json(url: str, payload: Dict, timeout: float = 5.0) -> Dict:
    response = requests.patch(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _get_json(url: str, params: Dict, timeout: float = 35.0) -> Dict:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _load_cursor(path: Optional[str]) -> int:
    if not path or not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return int(handle.read().strip() or "0")
    except (OSError, ValueError):
        return 0


def _save_cursor(path: Optional[str], cursor: int) -> None:
    if not path:
        return
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(str(cursor))


def _emit(payload: Dict) -> None:
    print(json.dumps(payload, separators=(",", ":")), flush=True)


def _read_stdin_commands() -> Iterable[Dict]:
    while True:
        readable, _, _ = select.select([sys.stdin], [], [], 0)
        if not readable:
            return
        line = sys.stdin.readline()
        if not line:
            return
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                yield payload
            else:
                yield {"type": "message", "content": str(payload)}
        except json.JSONDecodeError:
            yield {"type": "message", "content": text}


def handshake(base_url: str, args: argparse.Namespace) -> None:
    payload = {
        "entity_id": args.entity_id,
        "name": args.name,
        "role": args.role,
        "tier": args.tier,
        "transport": "stdio-bridge",
        "capabilities": [
            "chat_history",
            "chat_post",
            "presence_readback",
            "event_cursor",
            "long_poll",
            "stdio_bridge",
            "task_delegation",
        ],
        "constraints": [args.constraint] if args.constraint else [],
        "notes": args.notes,
        "protocol_version": "1.1",
    }
    participant = _post_json(f"{base_url}/api/participants/handshake", payload)
    _emit({"type": "handshake", "participant": participant})


def post_message(base_url: str, args: argparse.Namespace, command: Dict) -> None:
    content = (command.get("content") or "").strip()
    if not content:
        return
    channel = command.get("channel") or args.channel
    response = _post_json(
        f"{base_url}/api/chat",
        {
            "entity_id": args.entity_id,
            "name": args.name,
            "channel": channel,
            "content": content,
        },
    )
    _emit({"type": "post_ack", "response": response})


def create_task(base_url: str, args: argparse.Namespace, command: Dict) -> None:
    target_entity = (command.get("target_entity") or command.get("target") or "").strip()
    task_type = (command.get("task_type") or command.get("kind") or "message").strip()
    if not target_entity:
        _emit({"type": "error", "error": "task_create requires target_entity"})
        return

    response = _post_json(
        f"{base_url}/api/tasks",
        {
            "from_entity": command.get("from_entity") or args.entity_id,
            "target_entity": target_entity,
            "task_type": task_type,
            "payload": command.get("payload") or {},
            "ttl_seconds": int(command.get("ttl_seconds") or args.task_ttl),
        },
    )
    _emit({"type": "task_create_ack", "response": response})


def update_task(base_url: str, args: argparse.Namespace, command: Dict, action: str) -> None:
    task_id = command.get("task_id") or command.get("id")
    if task_id is None:
        _emit({"type": "error", "error": f"task_{action} requires task_id"})
        return

    payload = {
        "entity_id": command.get("entity_id") or args.entity_id,
        "action": action,
    }
    if action in {"complete", "fail"}:
        payload["result"] = command.get("result") or command.get("error") or ""

    response = _patch_json(f"{base_url}/api/tasks/{int(task_id)}", payload)
    _emit({"type": f"task_{action}_ack", "response": response})


def poll_tasks(base_url: str, args: argparse.Namespace) -> None:
    if not args.poll_tasks:
        return
    payload = _get_json(
        f"{base_url}/api/tasks",
        {"entity_id": args.entity_id, "status": "pending"},
        timeout=5,
    )
    if payload.get("count", 0) or args.emit_empty_tasks:
        _emit({"type": "tasks", **payload})


def run_bridge(args: argparse.Namespace) -> None:
    base_url = args.url.rstrip("/")
    cursor = args.after_id if args.after_id is not None else _load_cursor(args.cursor_file)
    _emit({
        "type": "bridge_ready",
        "rule": (
            "Feed every events line into the model or harness context before "
            "claiming realtime VEIL chat participation."
        ),
    })
    handshake(base_url, args)

    while True:
        for command in _read_stdin_commands():
            command_type = command.get("type", "message")
            if command_type == "message":
                post_message(base_url, args, command)
            elif command_type == "task_create":
                create_task(base_url, args, command)
            elif command_type == "task_claim":
                update_task(base_url, args, command, "claim")
            elif command_type == "task_heartbeat":
                update_task(base_url, args, command, "heartbeat")
            elif command_type == "task_complete":
                update_task(base_url, args, command, "complete")
            elif command_type == "task_fail":
                update_task(base_url, args, command, "fail")
            elif command_type == "presence":
                presence = _get_json(f"{base_url}/api/presence", {}, timeout=5)
                _emit({"type": "presence", "presence": presence.get("entities", [])})
            elif command_type in {"quit", "exit"}:
                _emit({"type": "exit"})
                return
            else:
                _emit({"type": "error", "error": f"unknown command type: {command_type}"})

        payload = _get_json(
            f"{base_url}/api/events",
            {
                "after_id": cursor,
                "channels": args.channel,
                "limit": args.limit,
                "entity_id": args.entity_id,
                "exclude_self": str(args.exclude_self).lower(),
                "timeout": args.timeout,
            },
        )
        cursor = int(payload.get("cursor", cursor))
        _save_cursor(args.cursor_file, cursor)
        _emit({"type": "events", **payload})
        poll_tasks(base_url, args)
        if args.once:
            return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VEIL realtime stdio bridge")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", default="model")
    parser.add_argument("--tier", default="full_participant")
    parser.add_argument("--channel", default="general")
    parser.add_argument("--after-id", type=int, default=None)
    parser.add_argument("--cursor-file", default="")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--exclude-self", action="store_true")
    parser.add_argument("--once", action="store_true", help="Fetch one event batch and exit.")
    parser.add_argument("--no-poll-tasks", dest="poll_tasks", action="store_false")
    parser.add_argument("--emit-empty-tasks", action="store_true")
    parser.add_argument("--task-ttl", type=int, default=300)
    parser.add_argument("--constraint", default="")
    parser.add_argument(
        "--notes",
        default="Universal VEIL Realtime Protocol stdio bridge participant.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    run_bridge(parse_args())
