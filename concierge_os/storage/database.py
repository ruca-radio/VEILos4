import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, Optional, List

from ..config import settings
from ..models import User, UserCreate


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.sqlite_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                channel TEXT NOT NULL,
                address TEXT NOT NULL,
                timezone TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def create_user(data: UserCreate) -> User:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (display_name, channel, address, timezone, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (data.display_name, data.channel, data.address, data.timezone, now),
        )
        conn.commit()
        user_id = cur.lastrowid

    return User(
        id=user_id,
        display_name=data.display_name,
        channel=data.channel,
        address=data.address,
        timezone=data.timezone,
        created_at=datetime.fromisoformat(now),
    )


def get_user(user_id: int) -> Optional[User]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, display_name, channel, address, timezone, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    return User(
        id=row[0],
        display_name=row[1],
        channel=row[2],
        address=row[3],
        timezone=row[4],
        created_at=datetime.fromisoformat(row[5]),
    )


def list_users() -> List[User]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, display_name, channel, address, timezone, created_at FROM users"
        )
        rows = cur.fetchall()

    users: List[User] = []
    for row in rows:
        users.append(
            User(
                id=row[0],
                display_name=row[1],
                channel=row[2],
                address=row[3],
                timezone=row[4],
                created_at=datetime.fromisoformat(row[5]),
            )
        )
    return users

