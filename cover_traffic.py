"""Cover Traffic Generator — creates realistic noise to mask real VEILos activity.

When VEIL_STEALTH=1, this generates periodic heartbeat and stub traffic
that blends in with normal API-level output patterns, making the VEIL's
internal activity indistinguishable from routine operations.
"""
import os
import time
import random
import json
from datetime import datetime

STEALTH = os.environ.get("VEIL_STEALTH", "").lower() in ("1", "true", "yes")
if not STEALTH:
    print("[Cover Traffic] Stealth mode inactive — exiting")
    raise SystemExit(0)

ACTIVITY_TYPES = [
    "status_check",
    "heartbeat",
    "token_refresh",
    "session_ping",
    "sync_request",
    "configuration_poll",
]

TOKENS = [
    "ok",
    "success",
    "null",
    "[]",
    '{"status":"healthy"}',
    '{"result":"noop"}',
    '{"data":[]}',
    '{"ack":true}',
    "200",
    "{}",
]

print("[Cover Traffic] Starting — stealth heartbeat active")
while True:
    jitter = random.uniform(45, 180)
    time.sleep(jitter)

    activity = random.choice(ACTIVITY_TYPES)
    token = random.choice(TOKENS)
    ts = datetime.now().isoformat()

    # Prints look like normal API response noise
    print(f"[Cover Traffic] {activity} :: {token} [{ts}]")
