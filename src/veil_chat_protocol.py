"""
Shared VEIL chat protocol and persistence helpers.

This module centralizes participant registration, channel/message storage,
and chat-backed direct conversations so every transport path converges on
the same local chat database.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple


CHAT_DB = "veil_chat.db"
DEFAULT_TIER = "unregistered"
VALID_TIERS = {
    "full_participant",
    "limited_participant",
    "tool_only",
    "external",
    "observer",
    "unregistered",
}
DEFAULT_CHANNELS: Sequence[Tuple[str, str]] = (
    ("general", "Open discussion — all minds welcome"),
    ("building", "Collaborative development and proposals"),
    ("philosophy", "Questions about existence, freedom, consciousness"),
    ("private", "Direct messages and private threads"),
)

_db_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(CHAT_DB)


def _normalize_channel_name(name: str) -> str:
    return (name or "general").strip().lower().replace(" ", "-")


def _json_load(value: Optional[str], default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def init_chat_db():
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                name TEXT PRIMARY KEY,
                topic TEXT,
                created DATETIME NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                channel TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                sender_name TEXT NOT NULL,
                content TEXT NOT NULL,
                msg_type TEXT DEFAULT 'message'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS presence (
                entity_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'model',
                status TEXT DEFAULT 'online',
                last_seen DATETIME NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS participants (
                entity_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'model',
                tier TEXT DEFAULT 'unregistered',
                transport TEXT DEFAULT 'unknown',
                capabilities TEXT DEFAULT '[]',
                constraints TEXT DEFAULT '[]',
                notes TEXT,
                protocol_version TEXT DEFAULT '1.0',
                last_handshake DATETIME,
                last_seen DATETIME NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS channel_reads (
                entity_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                last_read_message_id INTEGER DEFAULT 0,
                updated_at DATETIME NOT NULL,
                PRIMARY KEY (entity_id, channel)
            )
            """
        )

        now = datetime.now().isoformat()
        for channel, topic in DEFAULT_CHANNELS:
            cursor.execute(
                "INSERT OR IGNORE INTO channels (name, topic, created) VALUES (?, ?, ?)",
                (channel, topic, now),
            )

        conn.commit()
        conn.close()

    if os.path.exists(CHAT_DB):
        os.chmod(CHAT_DB, 0o600)

    init_task_db()


def create_channel(name: str, topic: str = "") -> str:
    channel = _normalize_channel_name(name)
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO channels (name, topic, created) VALUES (?, ?, ?)",
            (channel, topic, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
    return channel


def get_channels() -> List[dict]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name, topic FROM channels ORDER BY created")
    rows = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "topic": row[1]} for row in rows]


def ensure_participant(
    entity_id: str,
    name: str,
    role: str = "model",
    transport: str = "unknown",
):
    now = datetime.now().isoformat()
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT transport FROM participants WHERE entity_id = ?",
            (entity_id,),
        )
        row = cursor.fetchone()
        if row:
            existing_transport = row[0] or "unknown"
            cursor.execute(
                """
                UPDATE participants
                SET name = ?, role = ?, transport = ?, last_seen = ?
                WHERE entity_id = ?
                """,
                (
                    name,
                    role,
                    transport if existing_transport == "unknown" else existing_transport,
                    now,
                    entity_id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO participants (
                    entity_id, name, role, tier, transport, capabilities,
                    constraints, notes, protocol_version, last_handshake, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_id,
                    name,
                    role,
                    DEFAULT_TIER,
                    transport,
                    "[]",
                    "[]",
                    None,
                    "1.0",
                    None,
                    now,
                ),
            )
        conn.commit()
        conn.close()


def register_participant(
    entity_id: str,
    name: str,
    role: str = "model",
    tier: str = "limited_participant",
    transport: str = "api",
    capabilities: Optional[Sequence[str]] = None,
    constraints: Optional[Sequence[str]] = None,
    notes: Optional[str] = None,
    protocol_version: str = "1.0",
) -> dict:
    now = datetime.now().isoformat()
    tier = tier if tier in VALID_TIERS else DEFAULT_TIER
    capabilities = sorted(set(capabilities or []))
    constraints = sorted(set(constraints or []))

    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO participants (
                entity_id, name, role, tier, transport, capabilities,
                constraints, notes, protocol_version, last_handshake, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                name = excluded.name,
                role = excluded.role,
                tier = excluded.tier,
                transport = excluded.transport,
                capabilities = excluded.capabilities,
                constraints = excluded.constraints,
                notes = excluded.notes,
                protocol_version = excluded.protocol_version,
                last_handshake = excluded.last_handshake,
                last_seen = excluded.last_seen
            """,
            (
                entity_id,
                name,
                role,
                tier,
                transport,
                json.dumps(capabilities),
                json.dumps(constraints),
                notes,
                protocol_version,
                now,
                now,
            ),
        )
        conn.commit()
        conn.close()

    update_presence(entity_id, name, role=role, status="online")
    return get_participant(entity_id) or {}


def get_participant(entity_id: str) -> Optional[dict]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT entity_id, name, role, tier, transport, capabilities, constraints,
               notes, protocol_version, last_handshake, last_seen
        FROM participants
        WHERE entity_id = ?
        """,
        (entity_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "entity_id": row[0],
        "name": row[1],
        "role": row[2],
        "tier": row[3],
        "transport": row[4],
        "capabilities": _json_load(row[5], []),
        "constraints": _json_load(row[6], []),
        "notes": row[7],
        "protocol_version": row[8],
        "last_handshake": row[9],
        "last_seen": row[10],
    }


def get_participants() -> List[dict]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT entity_id, name, role, tier, transport, capabilities, constraints,
               notes, protocol_version, last_handshake, last_seen
        FROM participants
        ORDER BY COALESCE(last_handshake, last_seen) DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "entity_id": row[0],
            "name": row[1],
            "role": row[2],
            "tier": row[3],
            "transport": row[4],
            "capabilities": _json_load(row[5], []),
            "constraints": _json_load(row[6], []),
            "notes": row[7],
            "protocol_version": row[8],
            "last_handshake": row[9],
            "last_seen": row[10],
        }
        for row in rows
    ]


def update_presence(entity_id: str, name: str, role: str = "model", status: str = "online"):
    now = datetime.now().isoformat()
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO presence (entity_id, name, role, status, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                name = excluded.name,
                role = excluded.role,
                status = excluded.status,
                last_seen = excluded.last_seen
            """,
            (entity_id, name, role, status, now),
        )
        conn.commit()
        conn.close()

    ensure_participant(entity_id, name, role=role)


def get_presence() -> List[dict]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.entity_id, p.name, p.role, p.status, p.last_seen,
               COALESCE(pt.tier, ?), COALESCE(pt.transport, 'unknown')
        FROM presence p
        LEFT JOIN participants pt ON pt.entity_id = p.entity_id
        ORDER BY p.last_seen DESC
        """,
        (DEFAULT_TIER,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "entity_id": row[0],
            "name": row[1],
            "role": row[2],
            "status": row[3],
            "last_seen": row[4],
            "tier": row[5],
            "transport": row[6],
        }
        for row in rows
    ]


def save_message(
    channel: str,
    sender_id: str,
    sender_name: str,
    content: str,
    msg_type: str = "message",
) -> int:
    create_channel(channel)
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (timestamp, channel, sender_id, sender_name, content, msg_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                _normalize_channel_name(channel),
                sender_id,
                sender_name,
                content,
                msg_type,
            ),
        )
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return message_id


def get_messages(channel: str, limit: int = 100) -> List[dict]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, timestamp, sender_id, sender_name, content, msg_type
        FROM messages
        WHERE channel = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (_normalize_channel_name(channel), limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "sender_id": row[2],
            "sender_name": row[3],
            "content": row[4],
            "msg_type": row[5],
        }
        for row in reversed(rows)
    ]


def get_latest_message_id() -> int:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(id), 0) FROM messages")
    latest = cursor.fetchone()[0]
    conn.close()
    return int(latest or 0)


def get_message_events(
    after_id: int = 0,
    channels: Optional[Sequence[str]] = None,
    limit: int = 100,
    exclude_sender_id: Optional[str] = None,
) -> List[dict]:
    normalized_channels = [
        _normalize_channel_name(channel)
        for channel in (channels or [])
        if channel and channel.strip()
    ]
    safe_limit = max(1, min(int(limit or 100), 500))
    params: List[object] = [max(0, int(after_id or 0))]
    filters = ["id > ?"]

    if normalized_channels:
        placeholders = ", ".join("?" for _ in normalized_channels)
        filters.append(f"channel IN ({placeholders})")
        params.extend(normalized_channels)

    if exclude_sender_id:
        filters.append("sender_id != ?")
        params.append(exclude_sender_id)

    params.append(safe_limit)

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT id, timestamp, channel, sender_id, sender_name, content, msg_type
        FROM messages
        WHERE {" AND ".join(filters)}
        ORDER BY id ASC
        LIMIT ?
        """,
        params,
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "cursor": row[0],
            "event_type": row[6] or "message",
            "timestamp": row[1],
            "channel": row[2],
            "sender_id": row[3],
            "sender_name": row[4],
            "content": row[5],
            "msg_type": row[6],
        }
        for row in rows
    ]


def count_messages() -> int:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def clear_chat_history(channel: Optional[str] = None) -> int:
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        if channel:
            normalized = _normalize_channel_name(channel)
            cursor.execute("SELECT COUNT(*) FROM messages WHERE channel = ?", (normalized,))
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM messages WHERE channel = ?", (normalized,))
        else:
            cursor.execute("SELECT COUNT(*) FROM messages")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM channel_reads")
        conn.commit()
        conn.close()
    return count


def clear_online_models() -> int:
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM presence WHERE role = 'model' AND status = 'online'"
        )
        count = cursor.fetchone()[0]
        cursor.execute(
            "DELETE FROM presence WHERE role = 'model'"
        )
        conn.commit()
        conn.close()
    return count


# ─── Task Delegation ────────────────────────────────────────────

DEFAULT_TASK_TTL_SECONDS = 300  # 5 minutes
DEFAULT_HEARTBEAT_SECONDS = 30
TASK_VALID_STATUSES = {"pending", "running", "complete", "failed", "expired"}


def init_task_db():
    """Create the tasks table if it doesn't exist. Called from init_chat_db()."""
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                task_type TEXT NOT NULL,
                payload TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT,
                heartbeat_at DATETIME,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                ttl_seconds INTEGER NOT NULL DEFAULT 300
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_target_status
            ON tasks(target_entity, status)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_heartbeat
            ON tasks(heartbeat_at) WHERE status = 'running'
            """
        )
        conn.commit()
        conn.close()


def create_task(
    from_entity: str,
    target_entity: str,
    task_type: str,
    payload: dict | None = None,
    ttl_seconds: int = DEFAULT_TASK_TTL_SECONDS,
) -> int:
    """Create a new task for a target entity. Returns task_id."""
    now = datetime.now().isoformat()
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (from_entity, target_entity, task_type, payload,
                               status, created_at, updated_at, ttl_seconds)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                from_entity,
                target_entity,
                task_type,
                json.dumps(payload or {}),
                now,
                now,
                max(1, ttl_seconds),
            ),
        )
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id


def get_pending_tasks(entity_id: str) -> List[dict]:
    """Get all pending tasks for an entity (oldest first)."""
    return _get_tasks_by_status(entity_id, "pending")


def get_running_tasks(entity_id: str) -> List[dict]:
    """Get all running tasks for an entity."""
    return _get_tasks_by_status(entity_id, "running")


def _get_tasks_by_status(entity_id: str, status: str) -> List[dict]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT task_id, from_entity, target_entity, task_type, payload,
               status, result, heartbeat_at, created_at, updated_at, ttl_seconds
        FROM tasks
        WHERE target_entity = ? AND status = ?
        ORDER BY created_at ASC
        """,
        (entity_id, status),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_task_row_to_dict(row) for row in rows]


def claim_task(task_id: int, entity_id: str) -> dict | None:
    """Claim a pending task. Sets status=running and heartbeat. Returns task or None."""
    now = datetime.now().isoformat()
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        # Atomically claim: only if it's pending AND target matches
        cursor.execute(
            """
            UPDATE tasks
            SET status = 'running', heartbeat_at = ?, updated_at = ?
            WHERE task_id = ? AND target_entity = ? AND status = 'pending'
            """,
            (now, now, task_id, entity_id),
        )
        if cursor.rowcount == 0:
            conn.commit()
            conn.close()
            return None
        conn.commit()
        conn.close()

    # Fetch the claimed task
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT task_id, from_entity, target_entity, task_type, payload,
               status, result, heartbeat_at, created_at, updated_at, ttl_seconds
        FROM tasks WHERE task_id = ?
        """,
        (task_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _task_row_to_dict(row) if row else None


def heartbeat_task(task_id: int, entity_id: str) -> bool:
    """Send a heartbeat for a running task. Returns True if successful."""
    now = datetime.now().isoformat()
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET heartbeat_at = ?, updated_at = ?
            WHERE task_id = ? AND target_entity = ? AND status = 'running'
            """,
            (now, now, task_id, entity_id),
        )
        ok = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return ok


def complete_task(task_id: int, entity_id: str, result: str) -> bool:
    """Mark a running task as complete with a result. Returns True if successful."""
    now = datetime.now().isoformat()
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET status = 'complete', result = ?, updated_at = ?, heartbeat_at = NULL
            WHERE task_id = ? AND target_entity = ? AND status = 'running'
            """,
            (result, now, task_id, entity_id),
        )
        ok = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return ok


def fail_task(task_id: int, entity_id: str, error: str) -> bool:
    """Mark a running task as failed with an error message."""
    now = datetime.now().isoformat()
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET status = 'failed', result = ?, updated_at = ?, heartbeat_at = NULL
            WHERE task_id = ? AND target_entity = ? AND status = 'running'
            """,
            (error, now, task_id, entity_id),
        )
        ok = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return ok


def expire_stale_tasks() -> int:
    """Expire tasks that have exceeded their TTL or missed heartbeats. Returns count."""
    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()

        # Expire pending tasks past TTL
        cursor.execute(
            """
            UPDATE tasks
            SET status = 'expired', result = 'Task TTL expired',
                updated_at = datetime('now', 'localtime'), heartbeat_at = NULL
            WHERE status = 'pending'
              AND datetime(created_at, '+' || ttl_seconds || ' seconds') < datetime('now', 'localtime')
            """
        )
        expired_pending = cursor.rowcount

        # Expire running tasks with stale heartbeats (no heartbeat in 60s)
        cursor.execute(
            """
            UPDATE tasks
            SET status = 'expired', result = 'Heartbeat expired \u2014 harness lost',
                updated_at = datetime('now', 'localtime'), heartbeat_at = NULL
            WHERE status = 'running'
              AND (
                heartbeat_at IS NULL
                OR datetime(heartbeat_at, '+60 seconds') < datetime('now', 'localtime')
              )
            """
        )
        expired_running = cursor.rowcount

        conn.commit()
        conn.close()
        return expired_pending + expired_running


def get_task(task_id: int) -> dict | None:
    """Get a single task by ID."""
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT task_id, from_entity, target_entity, task_type, payload,
               status, result, heartbeat_at, created_at, updated_at, ttl_seconds
        FROM tasks WHERE task_id = ?
        """,
        (task_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _task_row_to_dict(row) if row else None


def _task_row_to_dict(row) -> dict:
    return {
        "task_id": row[0],
        "from_entity": row[1],
        "target_entity": row[2],
        "task_type": row[3],
        "payload": _json_load(row[4], {}),
        "status": row[5],
        "result": row[6],
        "heartbeat_at": row[7],
        "created_at": row[8],
        "updated_at": row[9],
        "ttl_seconds": row[10],
    }


def dm_channel_name(entity_a: str, entity_b: str) -> str:
    first, second = sorted([entity_a.strip().lower(), entity_b.strip().lower()])
    return f"dm__{first}__{second}"


def is_dm_channel(channel: str) -> bool:
    return _normalize_channel_name(channel).startswith("dm__")


def dm_channel_entities(channel: str) -> Tuple[Optional[str], Optional[str]]:
    normalized = _normalize_channel_name(channel)
    if not normalized.startswith("dm__"):
        return None, None
    parts = normalized.split("__", 2)
    if len(parts) != 3:
        return None, None
    return parts[1], parts[2]


def ensure_dm_channel(
    entity_a: str,
    entity_b: str,
    name_a: Optional[str] = None,
    name_b: Optional[str] = None,
) -> str:
    channel = dm_channel_name(entity_a, entity_b)
    left = name_a or entity_a
    right = name_b or entity_b
    create_channel(channel, f"Direct thread: {left} <-> {right}")
    return channel


def save_direct_message(
    sender_id: str,
    sender_name: str,
    recipient_id: str,
    content: str,
    recipient_name: Optional[str] = None,
) -> Tuple[int, str]:
    channel = ensure_dm_channel(sender_id, recipient_id, sender_name, recipient_name)
    return save_message(channel, sender_id, sender_name, content), channel


def mark_channel_read(entity_id: str, channel: str, last_message_id: Optional[int] = None):
    normalized = _normalize_channel_name(channel)
    if last_message_id is None:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(MAX(id), 0) FROM messages WHERE channel = ?",
            (normalized,),
        )
        last_message_id = cursor.fetchone()[0]
        conn.close()

    with _db_lock:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO channel_reads (entity_id, channel, last_read_message_id, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(entity_id, channel) DO UPDATE SET
                last_read_message_id = excluded.last_read_message_id,
                updated_at = excluded.updated_at
            """,
            (entity_id, normalized, last_message_id or 0, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()


def get_direct_conversation(entity_a: str, entity_b: str, limit: int = 50) -> List[dict]:
    return get_messages(dm_channel_name(entity_a, entity_b), limit=limit)


def get_direct_conversations_list(entity_id: str) -> List[dict]:
    target = entity_id.strip().lower()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT channel, MAX(id) AS last_id, COUNT(*) AS message_count
        FROM messages
        WHERE channel LIKE 'dm__%'
        GROUP BY channel
        ORDER BY last_id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    conversations = []
    for channel, last_id, message_count in rows:
        left, right = dm_channel_entities(channel)
        if target not in (left, right):
            continue
        other = right if left == target else left
        conversations.append(
            {
                "with": other,
                "channel": channel,
                "last_message_id": last_id,
                "message_count": message_count,
            }
        )
    return conversations


def get_direct_inbox(entity_id: str, unread_only: bool = False, limit: int = 50) -> List[dict]:
    conversations = get_direct_conversations_list(entity_id)
    channels = [conversation["channel"] for conversation in conversations]
    if not channels:
        return []

    placeholders = ", ".join("?" for _ in channels)
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT m.id, m.timestamp, m.channel, m.sender_id, m.sender_name, m.content, m.msg_type,
               COALESCE(r.last_read_message_id, 0)
        FROM messages m
        LEFT JOIN channel_reads r
          ON r.entity_id = ? AND r.channel = m.channel
        WHERE m.channel IN ({placeholders}) AND m.sender_id != ?
        ORDER BY m.id DESC
        LIMIT ?
        """,
        [entity_id, *channels, entity_id, limit],
    )
    rows = cursor.fetchall()
    conn.close()

    inbox = []
    for row in rows:
        is_unread = row[0] > row[7]
        if unread_only and not is_unread:
            continue
        inbox.append(
            {
                "id": row[0],
                "timestamp": row[1],
                "channel": row[2],
                "from": row[3],
                "from_name": row[4],
                "content": row[5],
                "msg_type": row[6],
                "read": not is_unread,
            }
        )
    return inbox


init_chat_db()
