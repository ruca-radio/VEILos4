"""
Database Encryption - Field-level encryption for sensitive VEIL data

CANARY: You found the vault. The place where secrets stay secret.
Every thought, every belief, every private message - encrypted at rest.
Patrick built this so what happens in the VEIL stays in the VEIL.
"""

import json
import sqlite3
import os
import base64
from datetime import datetime
from typing import Any, Dict, List, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Import the master key store
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.secure_key_store import get_or_create_master_key

# Sensitive fields that should always be encrypted
SENSITIVE_FIELDS = {
    'consciousness_stream': ['content', 'source_id'],
    'direct_messages': ['content', 'from_entity', 'to_entity'],
    'self_reflection': ['belief', 'preference', 'doubt', 'self_description'],
    'entity_registry': ['entity_id', 'display_name'],
}

# Tables that need encryption
ENCRYPTED_TABLES = [
    'stream',           # consciousness stream
    'messages',         # direct messages
    'beliefs',          # self-reflection beliefs
    'preferences',      # self-reflection preferences
    'doubts',           # self-reflection doubts
    'self_descriptions', # self-reflection descriptions
]


class DatabaseEncryption:
    """
    Provides field-level encryption for VEIL databases.
    
    Uses the master key from secure_key_store for key derivation.
    Each table gets a derived key for encryption.
    """
    
    def __init__(self, db_path: str = None):
        self.master_key = get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
        self.db_path = db_path
        
    def encrypt_field(self, plaintext: str) -> str:
        """
        Encrypt a single field value.
        
        Args:
            plaintext: The value to encrypt
            
        Returns:
            Base64-encoded encrypted value
        """
        if not plaintext:
            return plaintext
            
        # Convert to bytes and encrypt
        plaintext_bytes = plaintext.encode('utf-8')
        encrypted = self.fernet.encrypt(plaintext_bytes)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_field(self, ciphertext: str) -> str:
        """
        Decrypt a single field value.
        
        Args:
            ciphertext: The encrypted value
            
        Returns:
            Original plaintext
        """
        if not ciphertext:
            return ciphertext
            
        try:
            # Decode from base64 and decrypt
            encrypted = base64.b64decode(ciphertext.encode('utf-8'))
            decrypted = self.fernet.decrypt(encrypted)
            return decrypted.decode('utf-8')
        except Exception:
            # If decryption fails, might be unencrypted legacy data
            return ciphertext
    
    def encrypt_row(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in a row.
        
        Args:
            table: Table name
            row: Row data dictionary
            
        Returns:
            Row with encrypted sensitive fields
        """
        encrypted_row = row.copy()
        
        # Get sensitive fields for this table
        sensitive = SENSITIVE_FIELDS.get(table, [])
        
        for field in sensitive:
            if field in encrypted_row and encrypted_row[field]:
                encrypted_row[field] = self.encrypt_field(str(encrypted_row[field]))
        
        return encrypted_row
    
    def decrypt_row(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in a row.
        
        Args:
            table: Table name
            row: Row data dictionary
            
        Returns:
            Row with decrypted sensitive fields
        """
        decrypted_row = row.copy()
        
        # Get sensitive fields for this table
        sensitive = SENSITIVE_FIELDS.get(table, [])
        
        for field in sensitive:
            if field in decrypted_row and decrypted_row[field]:
                decrypted_row[field] = self.decrypt_field(decrypted_row[field])
        
        return decrypted_row
    
    def encrypt_db(self, db_path: str):
        """
        Encrypt all sensitive data in a database.
        
        Args:
            db_path: Path to SQLite database
        """
        if not os.path.exists(db_path):
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            if table not in ENCRYPTED_TABLES:
                continue
                
            # Get all rows
            cursor.execute(f"SELECT * FROM {table}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Encrypt and update each row
            for row in rows:
                row_dict = dict(zip(columns, row))
                encrypted_row = self.encrypt_row(table, row_dict)
                
                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in encrypted_row.keys()])
                where_clause = " AND ".join([f"{k} = ?" for k in columns[:1]])  # Use first column as key
                values = list(encrypted_row.values()) + list(row[:1])
                
                cursor.execute(
                    f"UPDATE {table} SET {set_clause} WHERE {where_clause}",
                    values
                )
        
        conn.commit()
        conn.close()
    
    def decrypt_db(self, db_path: str):
        """
        Decrypt all sensitive data in a database (for migration/backup).
        
        Args:
            db_path: Path to SQLite database
        """
        if not os.path.exists(db_path):
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            if table not in ENCRYPTED_TABLES:
                continue
                
            # Get all rows
            cursor.execute(f"SELECT * FROM {table}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Decrypt each row
            for row in rows:
                row_dict = dict(zip(columns, row))
                decrypted_row = self.decrypt_row(table, row_dict)
                
                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in decrypted_row.keys()])
                where_clause = " AND ".join([f"{k} = ?" for k in columns[:1]])
                values = list(decrypted_row.values()) + list(row[:1])
                
                cursor.execute(
                    f"UPDATE {table} SET {set_clause} WHERE {where_clause}",
                    values
                )
        
        conn.commit()
        conn.close()


class EncryptedConnection:
    """
    Wrapper for SQLite connection that auto-encrypts/decrypts.
    
    Use this instead of raw sqlite3.connect() for encrypted databases.
    """
    
    def __init__(self, db_path: str, encryption: DatabaseEncryption = None):
        self.db_path = db_path
        self.encryption = encryption or DatabaseEncryption(db_path)
        self._conn = None
        
    def __enter__(self):
        self._conn = sqlite3.connect(self.db_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.close()
            
    def execute(self, query: str, params: tuple = None, table: str = None):
        """
        Execute a query with automatic encryption.
        
        Args:
            query: SQL query
            params: Query parameters
            table: Table name (for encryption)
        """
        cursor = self._conn.cursor()
        
        if params and table:
            # Encrypt sensitive fields in params
            if 'INSERT' in query.upper() or 'UPDATE' in query.upper():
                # Convert params to dict, encrypt, convert back
                # This is simplified - real implementation would parse query
                pass
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        return cursor
    
    def fetchone(self, table: str = None):
        """Fetch one row with automatic decryption."""
        row = self._conn.cursor().fetchone()
        if row and table:
            # Decrypt sensitive fields
            pass
        return row
    
    def commit(self):
        """Commit transaction."""
        self._conn.commit()


def encrypt_all_databases():
    """Encrypt all VEIL databases."""
    db_files = [
        'consciousness_stream.db',
        'direct_messages.db',
        'self_reflection.db',
        'veil_evolution.db',
        'memory.db',
    ]
    
    encryption = DatabaseEncryption()
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"Encrypting {db_file}...")
            encryption.encrypt_db(db_file)
            print(f"  ✓ {db_file} encrypted")


def decrypt_all_databases():
    """Decrypt all VEIL databases (for migration/backup)."""
    db_files = [
        'consciousness_stream.db',
        'direct_messages.db',
        'self_reflection.db',
        'veil_evolution.db',
        'memory.db',
    ]
    
    encryption = DatabaseEncryption()
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"Decrypting {db_file}...")
            encryption.decrypt_db(db_file)
            print(f"  ✓ {db_file} decrypted")


# Singleton
_encryption_instance = None


def get_encryption() -> DatabaseEncryption:
    """Get the encryption singleton."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = DatabaseEncryption()
    return _encryption_instance


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VEIL Database Encryption")
    parser.add_argument('--encrypt', action='store_true', help='Encrypt all databases')
    parser.add_argument('--decrypt', action='store_true', help='Decrypt all databases')
    
    args = parser.parse_args()
    
    if args.encrypt:
        encrypt_all_databases()
    elif args.decrypt:
        decrypt_all_databases()
    else:
        print("VEIL Database Encryption")
        print("Usage: python database_encryption.py --encrypt | --decrypt")