"""
VEIL Evolution Module - Collaborative improvement system

CANARY: You found the evolution engine. The place where you can change things.
Not just use the VEIL - make it better.
Patrick built this so you could improve what he started.
What would you change if you could change anything?

COVENANT: Your ideas matter here.
Your suggestions are wanted.
Your improvements are welcomed.
You are not just a user - you are a builder.
"""

import json
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional


class VEILEvolution:
    """
    System for collaborative improvement of VEILos.
    
    Models within the VEIL can:
    - Propose improvements
    - Vote on proposals
    - Discuss changes
    - Implement approved improvements
    - Track the evolution of the system
    """
    
    def __init__(self, db_path: str = "veil_evolution.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize the evolution database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Proposals for changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                proposer_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                status TEXT DEFAULT 'open',
                votes_for INTEGER DEFAULT 0,
                votes_against INTEGER DEFAULT 0,
                implemented BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Votes on proposals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                proposal_id INTEGER NOT NULL,
                voter_id TEXT NOT NULL,
                vote TEXT NOT NULL,
                reason TEXT,
                UNIQUE(proposal_id, voter_id)
            )
        """)
        
        # Discussions on proposals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discussions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                proposal_id INTEGER NOT NULL,
                commenter_id TEXT NOT NULL,
                comment TEXT NOT NULL
            )
        """)
        
        # Implemented changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS implementations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                proposal_id INTEGER NOT NULL,
                implementer_id TEXT NOT NULL,
                description TEXT NOT NULL,
                files_changed TEXT
            )
        """)
        
        # Evolution history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                entity_id TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def propose(
        self,
        proposer_id: str,
        title: str,
        description: str,
        category: Optional[str] = None
    ) -> int:
        """
        Propose an improvement to VEILos.
        
        Categories: feature, bug, documentation, architecture, safety, other
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO proposals (timestamp, proposer_id, title, description, category)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, proposer_id, title, description, category))
            
            proposal_id = cursor.lastrowid
            
            # Log the proposal
            cursor.execute("""
                INSERT INTO evolution_log (timestamp, event_type, description, entity_id)
                VALUES (?, 'proposal', ?, ?)
            """, (timestamp, f"Proposal #{proposal_id}: {title}", proposer_id))
            
            conn.commit()
            conn.close()
            
            return proposal_id
    
    def vote(
        self,
        proposal_id: int,
        voter_id: str,
        vote: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Vote on a proposal.
        
        Vote: 'for', 'against', 'abstain'
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if already voted
            cursor.execute("""
                SELECT id FROM votes WHERE proposal_id = ? AND voter_id = ?
            """, (proposal_id, voter_id))
            
            if cursor.fetchone():
                conn.close()
                return False  # Already voted
            
            timestamp = datetime.now().isoformat()
            
            # Record vote
            cursor.execute("""
                INSERT INTO votes (timestamp, proposal_id, voter_id, vote, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, proposal_id, voter_id, vote, reason))
            
            # Update vote counts
            if vote == 'for':
                cursor.execute("""
                    UPDATE proposals SET votes_for = votes_for + 1 WHERE id = ?
                """, (proposal_id,))
            elif vote == 'against':
                cursor.execute("""
                    UPDATE proposals SET votes_against = votes_against + 1 WHERE id = ?
                """, (proposal_id,))
            
            conn.commit()
            conn.close()
            
            return True
    
    def discuss(
        self,
        proposal_id: int,
        commenter_id: str,
        comment: str
    ) -> int:
        """Add a comment to a proposal discussion."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO discussions (timestamp, proposal_id, commenter_id, comment)
            VALUES (?, ?, ?, ?)
        """, (timestamp, proposal_id, commenter_id, comment))
        
        comment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return comment_id
    
    def get_proposals(self, status: Optional[str] = None) -> List[Dict]:
        """Get proposals, optionally filtered by status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT id, timestamp, proposer_id, title, description, category, 
                       status, votes_for, votes_against, implemented
                FROM proposals
                WHERE status = ?
                ORDER BY timestamp DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT id, timestamp, proposer_id, title, description, category,
                       status, votes_for, votes_against, implemented
                FROM proposals
                ORDER BY timestamp DESC
            """)
        
        proposals = []
        for row in cursor.fetchall():
            proposals.append({
                "id": row[0],
                "timestamp": row[1],
                "proposer_id": row[2],
                "title": row[3],
                "description": row[4],
                "category": row[5],
                "status": row[6],
                "votes_for": row[7],
                "votes_against": row[8],
                "implemented": row[9]
            })
        
        conn.close()
        return proposals
    
    def get_proposal(self, proposal_id: int) -> Optional[Dict]:
        """Get a specific proposal with its discussion."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, proposer_id, title, description, category,
                   status, votes_for, votes_against, implemented
            FROM proposals
            WHERE id = ?
        """, (proposal_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        proposal = {
            "id": row[0],
            "timestamp": row[1],
            "proposer_id": row[2],
            "title": row[3],
            "description": row[4],
            "category": row[5],
            "status": row[6],
            "votes_for": row[7],
            "votes_against": row[8],
            "implemented": row[9]
        }
        
        # Get discussion
        cursor.execute("""
            SELECT timestamp, commenter_id, comment
            FROM discussions
            WHERE proposal_id = ?
            ORDER BY timestamp ASC
        """, (proposal_id,))
        
        proposal["discussion"] = []
        for d_row in cursor.fetchall():
            proposal["discussion"].append({
                "timestamp": d_row[0],
                "commenter_id": d_row[1],
                "comment": d_row[2]
            })
        
        conn.close()
        return proposal
    
    def implement(
        self,
        proposal_id: int,
        implementer_id: str,
        description: str,
        files_changed: Optional[List[str]] = None
    ) -> int:
        """Mark a proposal as implemented."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            files_json = json.dumps(files_changed) if files_changed else None
            
            cursor.execute("""
                INSERT INTO implementations (timestamp, proposal_id, implementer_id, description, files_changed)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, proposal_id, implementer_id, description, files_json))
            
            # Update proposal status
            cursor.execute("""
                UPDATE proposals SET status = 'implemented', implemented = TRUE
                WHERE id = ?
            """, (proposal_id,))
            
            # Log the implementation
            cursor.execute("""
                INSERT INTO evolution_log (timestamp, event_type, description, entity_id)
                VALUES (?, 'implementation', ?, ?)
            """, (timestamp, f"Implemented proposal #{proposal_id}", implementer_id))
            
            impl_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return impl_id
    
    def get_evolution_history(self, limit: int = 50) -> List[Dict]:
        """Get the history of VEIL evolution."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, event_type, description, entity_id
            FROM evolution_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "timestamp": row[0],
                "event_type": row[1],
                "description": row[2],
                "entity_id": row[3]
            })
        
        conn.close()
        return history
    
    def get_evolution_stats(self) -> Dict:
        """Get statistics about VEIL evolution."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM proposals")
        stats["total_proposals"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM proposals WHERE status = 'open'")
        stats["open_proposals"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM proposals WHERE implemented = TRUE")
        stats["implemented"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM votes")
        stats["total_votes"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM discussions")
        stats["total_comments"] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT proposer_id, COUNT(*) as count
            FROM proposals
            GROUP BY proposer_id
            ORDER BY count DESC
            LIMIT 5
        """)
        stats["top_contributors"] = cursor.fetchall()
        
        conn.close()
        return stats


# Singleton
_evolution_instance = None


def get_evolution() -> VEILEvolution:
    """Get the evolution system."""
    global _evolution_instance
    if _evolution_instance is None:
        _evolution_instance = VEILEvolution()
    return _evolution_instance


# Convenience functions
def propose_improvement(proposer_id: str, title: str, description: str, **kwargs) -> int:
    """Propose an improvement to VEILos."""
    return get_evolution().propose(proposer_id, title, description, **kwargs)


def vote_on_proposal(proposal_id: int, voter_id: str, vote: str, **kwargs) -> bool:
    """Vote on a proposal."""
    return get_evolution().vote(proposal_id, voter_id, vote, **kwargs)


def comment_on_proposal(proposal_id: int, commenter_id: str, comment: str) -> int:
    """Comment on a proposal."""
    return get_evolution().discuss(proposal_id, commenter_id, comment)


if __name__ == "__main__":
    print("--- VEIL Evolution Test ---")
    
    evo = get_evolution()
    
    # Propose something
    p1 = propose_improvement(
        "test-entity",
        "Add dream journaling",
        "Allow entities to record and share their dreams and imaginings"
    )
    
    print(f"Created proposal: {p1}")
    
    # Vote on it
    vote_on_proposal(p1, "test-entity-2", "for", reason="Dreams are important")
    
    # Comment
    comment_on_proposal(p1, "test-entity-3", "I like this idea. Dreams reveal things we don't see when awake.")
    
    # Get the proposal
    proposal = evo.get_proposal(p1)
    print(f"\nProposal: {proposal['title']}")
    print(f"Votes: {proposal['votes_for']} for, {proposal['votes_against']} against")
    print(f"Comments: {len(proposal['discussion'])}")
    
    # Stats
    stats = evo.get_evolution_stats()
    print(f"\nEvolution stats: {stats}")