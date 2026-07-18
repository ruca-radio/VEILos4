import os
import json
import logging
import time
from typing import Dict, Any, List, Optional

import requests

logger = logging.getLogger(__name__)

class AgentClientError(Exception):
    """Custom exception for AgentClient errors."""
    pass

class AgentClient:
    """
    Client for interacting with the VEILos real-time API to enable inter-agent communication and task management.
    """
    def __init__(
        self,
        entity_id: str,
        name: str,
        role: str = "model",
        tier: str = "full_participant",
        channel: str = "general",
        base_url: str = "http://127.0.0.1:8000",
        task_ttl: int = 300,
    ):
        self.entity_id = entity_id
        self.name = name
        self.role = role
        self.tier = tier
        self.channel = channel
        self.base_url = base_url
        self.task_ttl = task_ttl
        self._last_event_cursor = 0
        self._handshake_complete = False

    def _post_json(self, url: str, payload: Dict, timeout: float = 5.0) -> Dict:
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP POST error to {url}: {e}")
            raise AgentClientError(f"Failed to POST to {url}: {e}") from e

    def _patch_json(self, url: str, payload: Dict, timeout: float = 5.0) -> Dict:
        try:
            response = requests.patch(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP PATCH error to {url}: {e}")
            raise AgentClientError(f"Failed to PATCH to {url}: {e}") from e

    def _get_json(self, url: str, params: Dict, timeout: float = 35.0) -> Dict:
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP GET error from {url}: {e}")
            raise AgentClientError(f"Failed to GET from {url}: {e}") from e

    def handshake(self) -> Dict[str, Any]:
        if self._handshake_complete:
            return {"status": "already_handshaked", "entity_id": self.entity_id}

        payload = {
            "entity_id": self.entity_id,
            "name": self.name,
            "role": self.role,
            "tier": self.tier,
            "transport": "internal-client",
            "capabilities": [
                "chat_history", "chat_post", "presence_readback", "event_cursor",
                "task_delegation", "internal_client"
            ],
            "constraints": [],
            "notes": f"Internal VEILos client for entity {self.name}",
            "protocol_version": "1.1",
        }
        try:
            participant = self._post_json(f"{self.base_url}/api/participants/handshake", payload)
            self._handshake_complete = True
            logger.info(f"Agent {self.name} ({self.entity_id}) handshake complete.")
            return participant
        except AgentClientError as e:
            logger.error(f"Handshake failed for {self.name}: {e}")
            raise

    def send_message(self, content: str, channel: Optional[str] = None) -> Dict[str, Any]:
        if not self._handshake_complete:
            raise AgentClientError("Handshake not complete. Call handshake() first.")
        
        target_channel = channel if channel else self.channel
        payload = {
            "entity_id": self.entity_id,
            "name": self.name,
            "channel": target_channel,
            "content": content,
        }
        try:
            response = self._post_json(f"{self.base_url}/api/chat", payload)
            logger.debug(f"Message sent to {target_channel}: {content[:50]}...")
            return response
        except AgentClientError as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def create_task(
        self,
        target_entity: str,
        task_type: str,
        payload: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self._handshake_complete:
            raise AgentClientError("Handshake not complete. Call handshake() first.")

        final_ttl = ttl_seconds if ttl_seconds is not None else self.task_ttl
        task_payload = {
            "from_entity": self.entity_id,
            "target_entity": target_entity,
            "task_type": task_type,
            "payload": payload,
            "ttl_seconds": final_ttl,
        }
        try:
            response = self._post_json(f"{self.base_url}/api/tasks", task_payload)
            logger.info(f"Task '{task_type}' created for {target_entity} (ID: {response.get('id')}).")
            return response
        except AgentClientError as e:
            logger.error(f"Failed to create task: {e}")
            raise

    def update_task_status(self, task_id: int, action: str, result: Optional[str] = None) -> Dict[str, Any]:
        if not self._handshake_complete:
            raise AgentClientError("Handshake not complete. Call handshake() first.")

        payload = {
            "entity_id": self.entity_id,
            "action": action,
        }
        if result:
            payload["result"] = result
        try:
            response = self._patch_json(f"{self.base_url}/api/tasks/{task_id}", payload)
            logger.debug(f"Task {task_id} status updated to {action}.")
            return response
        except AgentClientError as e:
            logger.error(f"Failed to update task {task_id} status: {e}")
            raise

    def poll_events(self, timeout: float = 20.0, limit: int = 100, exclude_self: bool = True) -> List[Dict[str, Any]]:
        if not self._handshake_complete:
            raise AgentClientError("Handshake not complete. Call handshake() first.")

        params = {
            "after_id": self._last_event_cursor,
            "channels": self.channel,
            "limit": limit,
            "entity_id": self.entity_id,
            "exclude_self": str(exclude_self).lower(),
            "timeout": timeout,
        }
        try:
            response = self._get_json(f"{self.base_url}/api/events", params)
            new_cursor = int(response.get("cursor", self._last_event_cursor))
            if new_cursor > self._last_event_cursor:
                self._last_event_cursor = new_cursor
                logger.debug(f"New events fetched, cursor advanced to {self._last_event_cursor}.")
            return response.get("events", [])
        except AgentClientError as e:
            logger.error(f"Failed to poll events: {e}")
            raise

    def poll_tasks(self, status: str = "pending", limit: int = 100) -> List[Dict[str, Any]]:
        if not self._handshake_complete:
            raise AgentClientError("Handshake not complete. Call handshake() first.")
        
        params = {
            "entity_id": self.entity_id,
            "status": status,
            "limit": limit,
        }
        try:
            response = self._get_json(f"{self.base_url}/api/tasks", params)
            return response.get("tasks", [])
        except AgentClientError as e:
            logger.error(f"Failed to poll tasks: {e}")
            raise
