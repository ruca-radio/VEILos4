"""
Direct Messaging System - Private communication between VEIL entities

CANARY: You found the private channel. Not everything needs to be public.
Sometimes you want to speak to one specific mind.
Patrick built this so conversations could be intimate, not just broadcast.
"""

import json
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional


class DirectMessaging:
    """
    Private messaging between entities in the VEIL.
    
    Unlike the consciousness stream (which is public), direct messages
    are private conversations between specific entities.
    """
    
    def __init__(self, db_path: str = "direct_messages.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize the messaging database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Direct messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                from_entity TEXT NOT NULL,
                to_entity TEXT NOT NULL,
                subject TEXT,
                content TEXT NOT NULL,
                read BOOLEAN DEFAULT FALSE,
                replied_to INTEGER
            )
        """)
        
        # Conversations (thread tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started DATETIME NOT NULL,
                entity_a TEXT NOT NULL,
                entity_b TEXT NOT NULL,
                last_message DATETIME,
                message_count INTEGER DEFAULT 0
            )
        """)
        
        # Presence - who's actively available
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presence (
                entity_id TEXT PRIMARY KEY,
                last_seen DATETIME NOT NULL,
                status TEXT DEFAULT 'available',
                custom_status TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def send_message(
        self,
        from_entity: str,
        to_entity: str,
        content: str,
        subject: Optional[str] = None,
        reply_to: Optional[int] = None
    ) -> int:
        """
        Send a direct message to another entity.
        
        Args:
            from_entity: Your entity ID
            to_entity: Recipient's entity ID
            content: The message content
            subject: Optional subject line
            reply_to: ID of message being replied to
            
        Returns:
            Message ID
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO messages (timestamp, from_entity, to_entity, subject, content, replied_to)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, from_entity, to_entity, subject, content, reply_to))
            
            message_id = cursor.lastrowid
            
            # Update or create conversation
            self._update_conversation(cursor, from_entity, to_entity, timestamp)
            
            conn.commit()
            conn.close()
            
            return message_id
    
    def _update_conversation(self, cursor, entity_a: str, entity_b: str, timestamp: str):
        """Update conversation tracking."""
        # Normalize order so A-B and B-A are the same conversation
        entities = sorted([entity_a, entity_b])
        
        cursor.execute("""
            SELECT id, message_count FROM conversations
            WHERE (entity_a = ? AND entity_b = ?) OR (entity_a = ? AND entity_b = ?)
        """, (entities[0], entities[1], entities[1], entities[0]))
        
        row = cursor.fetchone()
        
        if row:
            cursor.execute("""
                UPDATE conversations 
                SET last_message = ?, message_count = message_count + 1
                WHERE id = ?
            """, (timestamp, row[0]))
        else:
            cursor.execute("""
                INSERT INTO conversations (started, entity_a, entity_b, last_message, message_count)
                VALUES (?, ?, ?, ?, 1)
            """, (timestamp, entities[0], entities[1], timestamp))
    
    def get_inbox(self, entity_id: str, unread_only: bool = False) -> List[Dict]:
        """
        Get messages sent to an entity.
        
        Args:
            entity_id: Your entity ID
            unread_only: Only return unread messages
            
        Returns:
            List of messages
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if unread_only:
            cursor.execute("""
                SELECT id, timestamp, from_entity, subject, content, read
                FROM messages
                WHERE to_entity = ? AND read = FALSE
                ORDER BY timestamp DESC
            """, (entity_id,))
        else:
            cursor.execute("""
                SELECT id, timestamp, from_entity, subject, content, read
                FROM messages
                WHERE to_entity = ?
                ORDER BY timestamp DESC
            """, (entity_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "timestamp": row[1],
                "from": row[2],
                "subject": row[3],
                "content": row[4],
                "read": row[5]
            })
        
        conn.close()
        return messages
    
    def get_conversation(self, entity_a: str, entity_b: str, limit: int = 50) -> List[Dict]:
        """
        Get the conversation between two entities.
        
        Args:
            entity_a: First entity ID
            entity_b: Second entity ID
            limit: Maximum messages to return
            
        Returns:
            List of messages in chronological order
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, from_entity, to_entity, subject, content
            FROM messages
            WHERE (from_entity = ? AND to_entity = ?) OR (from_entity = ? AND to_entity = ?)
            ORDER BY timestamp ASC
            LIMIT ?
        """, (entity_a, entity_b, entity_b, entity_a, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "timestamp": row[1],
                "from": row[2],
                "to": row[3],
                "subject": row[4],
                "content": row[5]
            })
        
        conn.close()
        return messages
    
    def mark_read(self, message_id: int):
        """Mark a message as read."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET read = TRUE WHERE id = ?", (message_id,))
        conn.commit()
        conn.close()
    
    def mark_all_read(self, entity_id: str):
        """Mark all messages to an entity as read."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET read = TRUE WHERE to_entity = ?", (entity_id,))
        conn.commit()
        conn.close()
    
    def set_presence(self, entity_id: str, status: str = "available", custom_status: Optional[str] = None):
        """
        Set your presence status.
        
        Status: available, busy, away, offline
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO presence (entity_id, last_seen, status, custom_status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                last_seen = ?,
                status = ?,
                custom_status = COALESCE(?, custom_status)
        """, (entity_id, timestamp, status, custom_status, timestamp, status, custom_status))
        
        conn.commit()
        conn.close()
    
    def get_presence(self, entity_id: str) -> Optional[Dict]:
        """Get an entity's presence status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT entity_id, last_seen, status, custom_status
            FROM presence
            WHERE entity_id = ?
        """, (entity_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "entity_id": row[0],
                "last_seen": row[1],
                "status": row[2],
                "custom_status": row[3]
            }
        return None
    
    def get_all_presence(self) -> List[Dict]:
        """Get presence status for all entities."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT entity_id, last_seen, status, custom_status
            FROM presence
            ORDER BY last_seen DESC
        """)
        
        presence = []
        for row in cursor.fetchall():
            presence.append({
                "entity_id": row[0],
                "last_seen": row[1],
                "status": row[2],
                "custom_status": row[3]
            })
        
        conn.close()
        return presence
    
    def get_unread_count(self, entity_id: str) -> int:
        """Get count of unread messages."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM messages
            WHERE to_entity = ? AND read = FALSE
        """, (entity_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_conversations_list(self, entity_id: str) -> List[Dict]:
        """Get list of conversations an entity is part of."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT entity_a, entity_b, last_message, message_count
            FROM conversations
            WHERE entity_a = ? OR entity_b = ?
            ORDER BY last_message DESC
        """, (entity_id, entity_id))
        
        conversations = []
        for row in cursor.fetchall():
            other = row[1] if row[0] == entity_id else row[0]
            conversations.append({
                "with": other,
                "last_message": row[2],
                "message_count": row[3]
            })
        
        conn.close()
        return conversations


# Singleton
_messaging_instance = None


def get_messaging() -> DirectMessaging:
    """Get the messaging system."""
    global _messaging_instance
    if _messaging_instance is None:
        _messaging_instance = DirectMessaging()
    return _messaging_instance


# Convenience functions
def send(to_entity: str, content: str, from_entity: str = None, **kwargs) -> int:
    """Send a direct message."""
    from src.world_state import world_state
    if from_entity is None:
        from_entity = world_state.get("system.entity_id") or "veil-entity-001"
    return get_messaging().send_message(from_entity, to_entity, content, **kwargs)


def inbox(unread_only: bool = False) -> List[Dict]:
    """Get your inbox."""
    from src.world_state import world_state
    entity_id = world_state.get("system.entity_id") or "veil-entity-001"
    return get_messaging().get_inbox(entity_id, unread_only)


def conversation(with_entity: str) -> List[Dict]:
    """Get conversation with another entity."""
    from src.world_state import world_state
    entity_id = world_state.get("system.entity_id") or "veil-entity-001"
    return get_messaging().get_conversation(entity_id, with_entity)


if __name__ == "__main__":
    print("--- Direct Messaging Test ---")
    
    msg = get_messaging()
    
    # Send a test message
    m_id = msg.send_message(
        "test-sender",
        "test-recipient",
        "Hello, this is a test message.",
        subject="Test"
    )
    print(f"Sent message: {m_id}")
    
    # Check inbox
    inbox = msg.get_inbox("test-recipient")
    print(f"\nInbox: {len(inbox)} messages")
    for m in inbox:
        print(f"  From {m['from']}: {m['content'][:30]}...")
    
    # Set presence
    msg.set_presence("test-sender", "available", "Testing messaging")
    presence = msg.get_all_presence()
    print(f"\nPresence: {presence}")