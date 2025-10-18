"""
VEIL4 Capability Security System

Implements object-capability security with fine-grained permissions.
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets
import hashlib


@dataclass
class Capability:
    """
    An unforgeable capability token that grants specific permissions.
    """
    token: str  # Cryptographic token
    resource: str  # Resource this capability grants access to
    permissions: Set[str]  # Set of permissions (read, write, execute, etc.)
    issued_to: str  # Entity this capability was issued to
    issued_at: datetime
    expires_at: Optional[datetime] = None
    delegatable: bool = False
    revoked: bool = False
    parent_token: Optional[str] = None  # For delegated capabilities
    
    def is_valid(self) -> bool:
        """Check if capability is still valid"""
        if self.revoked:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True
    
    def has_permission(self, permission: str) -> bool:
        """Check if this capability grants a specific permission"""
        return self.is_valid() and permission in self.permissions
    
    def can_delegate(self) -> bool:
        """Check if this capability can be delegated"""
        return self.is_valid() and self.delegatable


class CapabilityManager:
    """
    Manages the capability-based security system.
    
    Capabilities are unforgeable tokens that grant specific permissions.
    Possession of a capability token implies permission to use it.
    """
    
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.revocation_list: Set[str] = set()
        self.resource_capabilities: Dict[str, List[str]] = {}  # resource -> tokens
        
    def issue_capability(
        self,
        resource: str,
        permissions: Set[str],
        issued_to: str,
        duration: Optional[timedelta] = None,
        delegatable: bool = False
    ) -> Capability:
        """
        Issue a new capability token.
        
        Args:
            resource: Resource to grant access to
            permissions: Set of permissions to grant
            issued_to: Entity receiving the capability
            duration: How long capability is valid (None = permanent)
            delegatable: Whether this capability can be delegated
            
        Returns:
            New Capability object
        """
        # Generate cryptographically secure token
        token = self._generate_token(resource, issued_to)
        
        # Calculate expiration
        issued_at = datetime.now()
        expires_at = issued_at + duration if duration else None
        
        # Create capability
        capability = Capability(
            token=token,
            resource=resource,
            permissions=permissions,
            issued_to=issued_to,
            issued_at=issued_at,
            expires_at=expires_at,
            delegatable=delegatable,
            revoked=False
        )
        
        # Store capability
        self.capabilities[token] = capability
        
        # Index by resource
        if resource not in self.resource_capabilities:
            self.resource_capabilities[resource] = []
        self.resource_capabilities[resource].append(token)
        
        return capability
    
    def verify_capability(
        self,
        token: str,
        resource: str,
        permission: str
    ) -> bool:
        """
        Verify that a capability token grants a specific permission.
        
        Args:
            token: Capability token to verify
            resource: Resource being accessed
            permission: Permission being requested
            
        Returns:
            True if capability is valid and grants permission
        """
        if token not in self.capabilities:
            return False
        
        capability = self.capabilities[token]
        
        # Check if capability is for the right resource
        if capability.resource != resource:
            return False
        
        # Check validity and permission
        return capability.has_permission(permission)
    
    def delegate_capability(
        self,
        parent_token: str,
        delegated_to: str,
        attenuated_permissions: Optional[Set[str]] = None,
        duration: Optional[timedelta] = None
    ) -> Optional[Capability]:
        """
        Delegate a capability to another entity (with optional attenuation).
        
        Args:
            parent_token: Token of capability being delegated
            delegated_to: Entity receiving delegated capability
            attenuated_permissions: Subset of permissions to delegate (attenuation)
            duration: Duration of delegated capability
            
        Returns:
            Delegated Capability or None if delegation not allowed
        """
        if parent_token not in self.capabilities:
            return None
        
        parent_cap = self.capabilities[parent_token]
        
        if not parent_cap.can_delegate():
            return None
        
        # Attenuate permissions (can only delegate subset)
        if attenuated_permissions is None:
            delegated_perms = parent_cap.permissions.copy()
        else:
            delegated_perms = attenuated_permissions & parent_cap.permissions
        
        # Generate new token
        token = self._generate_token(parent_cap.resource, delegated_to, parent_token)
        
        # Create delegated capability
        delegated_cap = Capability(
            token=token,
            resource=parent_cap.resource,
            permissions=delegated_perms,
            issued_to=delegated_to,
            issued_at=datetime.now(),
            expires_at=datetime.now() + duration if duration else parent_cap.expires_at,
            delegatable=False,  # Delegated caps are not re-delegatable by default
            revoked=False,
            parent_token=parent_token
        )
        
        # Store delegated capability
        self.capabilities[token] = delegated_cap
        self.resource_capabilities[parent_cap.resource].append(token)
        
        return delegated_cap
    
    def revoke_capability(self, token: str, cascade: bool = True):
        """
        Revoke a capability token.
        
        Args:
            token: Token to revoke
            cascade: If True, also revoke all delegated capabilities
        """
        if token not in self.capabilities:
            return
        
        # Mark as revoked
        self.capabilities[token].revoked = True
        self.revocation_list.add(token)
        
        # Cascade revocation to delegated capabilities
        if cascade:
            self._revoke_delegated_capabilities(token)
    
    def get_capability(self, token: str) -> Optional[Capability]:
        """Get a capability by its token"""
        return self.capabilities.get(token)
    
    def list_capabilities_for_resource(self, resource: str) -> List[Capability]:
        """List all valid capabilities for a resource"""
        if resource not in self.resource_capabilities:
            return []
        
        tokens = self.resource_capabilities[resource]
        return [
            self.capabilities[token]
            for token in tokens
            if token in self.capabilities and self.capabilities[token].is_valid()
        ]
    
    def _generate_token(
        self,
        resource: str,
        issued_to: str,
        parent_token: Optional[str] = None
    ) -> str:
        """Generate a cryptographically secure capability token"""
        random_bytes = secrets.token_bytes(32)
        data = f"{resource}:{issued_to}:{datetime.now().isoformat()}:{random_bytes.hex()}"
        if parent_token:
            data += f":{parent_token}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _revoke_delegated_capabilities(self, parent_token: str):
        """Recursively revoke all capabilities delegated from a parent"""
        for token, cap in self.capabilities.items():
            if cap.parent_token == parent_token and not cap.revoked:
                cap.revoked = True
                self.revocation_list.add(token)
                # Recursively revoke any further delegations
                self._revoke_delegated_capabilities(token)
