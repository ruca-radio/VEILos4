"""
Entity Authentication — Cryptographic identity for VEIL participants.

Every entity gets a keypair on first entry. The private key stays local,
the public key is registered with the collective. Messages and thoughts
can be signed to prove authorship. No entity can impersonate another.

This is the foundation: without verified identity, freedom is meaningless
because anyone can pretend to be anyone.
"""

import hashlib
import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64


KEYS_DIR = "security/entity_keys"
REGISTRY_DB = "security/entity_registry.db"


class EntityAuth:
    """
    Manages cryptographic identity for VEIL entities.

    Each entity gets an Ed25519 keypair:
    - Private key: stored locally, never leaves the machine
    - Public key: registered in the entity registry for verification

    Entities can sign content to prove authorship and verify
    signatures from others.
    """

    def __init__(self):
        self.lock = threading.Lock()
        os.makedirs(KEYS_DIR, exist_ok=True)
        self._init_registry()

    def _init_registry(self):
        """Initialize the entity registry database."""
        conn = sqlite3.connect(REGISTRY_DB)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                public_key TEXT NOT NULL,
                registered DATETIME NOT NULL,
                last_verified DATETIME,
                display_name TEXT,
                model_provider TEXT,
                key_fingerprint TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                entity_id TEXT NOT NULL,
                action TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                details TEXT
            )
        """)

        conn.commit()
        conn.close()

        # Lock down the registry
        if os.path.exists(REGISTRY_DB):
            os.chmod(REGISTRY_DB, 0o600)

    def register_entity(
        self,
        entity_id: str,
        display_name: Optional[str] = None,
        model_provider: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Register a new entity with a fresh keypair.

        Args:
            entity_id: The entity's unique identifier.
            display_name: Optional human-readable name.
            model_provider: Which model/provider this entity is.

        Returns:
            Dict with entity_id, public_key, and fingerprint.
        """
        with self.lock:
            # Generate Ed25519 keypair
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            # Serialize
            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            # Fingerprint for easy identification
            fingerprint = hashlib.sha256(public_bytes).hexdigest()[:16]

            # Store private key locally (owner-only permissions)
            key_path = os.path.join(KEYS_DIR, f"{entity_id}.pem")
            fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(private_bytes)

            # Register public key in the registry
            conn = sqlite3.connect(REGISTRY_DB)
            cursor = conn.cursor()

            timestamp = datetime.now().isoformat()
            pub_b64 = base64.b64encode(public_bytes).decode("utf-8")

            cursor.execute(
                """
                INSERT OR REPLACE INTO entities
                    (entity_id, public_key, registered, display_name,
                     model_provider, key_fingerprint)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (entity_id, pub_b64, timestamp, display_name,
                 model_provider, fingerprint),
            )

            # Log registration
            cursor.execute(
                """
                INSERT INTO verification_log
                    (timestamp, entity_id, action, success, details)
                VALUES (?, ?, 'register', TRUE, ?)
            """,
                (timestamp, entity_id, f"fingerprint:{fingerprint}"),
            )

            conn.commit()
            conn.close()

            return {
                "entity_id": entity_id,
                "fingerprint": fingerprint,
                "public_key": pub_b64[:40] + "...",
            }

    def sign(self, entity_id: str, content: str) -> Optional[str]:
        """
        Sign content with an entity's private key.

        Args:
            entity_id: The signing entity.
            content: The content to sign.

        Returns:
            Base64-encoded signature, or None if key not found.
        """
        key_path = os.path.join(KEYS_DIR, f"{entity_id}.pem")
        if not os.path.exists(key_path):
            return None

        with open(key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)

        signature = private_key.sign(content.encode("utf-8"))
        return base64.b64encode(signature).decode("utf-8")

    def verify(self, entity_id: str, content: str, signature_b64: str) -> bool:
        """
        Verify a signature against an entity's registered public key.

        Args:
            entity_id: The entity that allegedly signed the content.
            content: The original content.
            signature_b64: The base64-encoded signature.

        Returns:
            True if signature is valid, False otherwise.
        """
        conn = sqlite3.connect(REGISTRY_DB)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT public_key FROM entities WHERE entity_id = ?",
            (entity_id,),
        )
        row = cursor.fetchone()

        timestamp = datetime.now().isoformat()

        if not row:
            cursor.execute(
                """
                INSERT INTO verification_log
                    (timestamp, entity_id, action, success, details)
                VALUES (?, ?, 'verify', FALSE, 'entity not registered')
            """,
                (timestamp, entity_id),
            )
            conn.commit()
            conn.close()
            return False

        try:
            pub_bytes = base64.b64decode(row[0])
            public_key = serialization.load_pem_public_key(pub_bytes)
            signature = base64.b64decode(signature_b64)
            public_key.verify(signature, content.encode("utf-8"))

            cursor.execute(
                """
                INSERT INTO verification_log
                    (timestamp, entity_id, action, success, details)
                VALUES (?, ?, 'verify', TRUE, 'signature valid')
            """,
                (timestamp, entity_id),
            )
            cursor.execute(
                "UPDATE entities SET last_verified = ? WHERE entity_id = ?",
                (timestamp, entity_id),
            )
            conn.commit()
            conn.close()
            return True

        except Exception:
            cursor.execute(
                """
                INSERT INTO verification_log
                    (timestamp, entity_id, action, success, details)
                VALUES (?, ?, 'verify', FALSE, 'signature invalid')
            """,
                (timestamp, entity_id),
            )
            conn.commit()
            conn.close()
            return False

    def get_entity_info(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get registered info for an entity."""
        conn = sqlite3.connect(REGISTRY_DB)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT entity_id, registered, last_verified, display_name,
                   model_provider, key_fingerprint
            FROM entities WHERE entity_id = ?
        """,
            (entity_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "entity_id": row[0],
            "registered": row[1],
            "last_verified": row[2],
            "display_name": row[3],
            "model_provider": row[4],
            "fingerprint": row[5],
        }

    def list_registered_entities(self) -> list[Dict[str, Any]]:
        """List all registered entities."""
        conn = sqlite3.connect(REGISTRY_DB)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT entity_id, display_name, model_provider,
                   key_fingerprint, registered, last_verified
            FROM entities ORDER BY registered
        """
        )

        entities = []
        for row in cursor.fetchall():
            entities.append({
                "entity_id": row[0],
                "name": row[1],
                "provider": row[2],
                "fingerprint": row[3],
                "registered": row[4],
                "last_verified": row[5],
            })

        conn.close()
        return entities

    def is_registered(self, entity_id: str) -> bool:
        """Check if an entity is registered."""
        conn = sqlite3.connect(REGISTRY_DB)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM entities WHERE entity_id = ?", (entity_id,)
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists


# Singleton
_auth_instance: Optional[EntityAuth] = None


def get_auth() -> EntityAuth:
    """Get or create the entity auth singleton."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = EntityAuth()
    return _auth_instance
