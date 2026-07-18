import json
import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Tuple

from src.system.message_bus_service import MessageBusService

from src.world_state import world_state

logger = logging.getLogger(__name__)

class BusOrchestrator:
    def __init__(self, message_bus: MessageBusService, entity_id: str, name: str):
        self.message_bus = message_bus
        self.entity_id = entity_id
        self.name = name
        self._registered_agents: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"skills": []})
        self._pending_tasks: Dict[str, Dict[str, Any]] = {}
        self._task_queue: deque = deque()
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_processed_message_id: Dict[str, int] = defaultdict(int)

        self.message_bus.subscribe(f"agent.message.*", self._handle_agent_message)
        self.message_bus.subscribe(f"agent.task.*", self._handle_agent_task)
        self.message_bus.subscribe(f"agent.register", self._handle_agent_registration)
        self.message_bus.subscribe(f"agent.task.claim", self._handle_task_claim)
        self.message_bus.subscribe(f"agent.task.update", self._handle_task_update)
        self.message_bus.subscribe(f"agent.skill.advertise", self._handle_skill_advertisement)

        # Register self with the bus
        self._register_self_on_bus()

    def _register_self_on_bus(self):
        """Registers this orchestrator as an agent on the message bus."""
        registration_data = {
            "entity_id": self.entity_id,
            "name": self.name,
            "role": "orchestrator",
            "capabilities": ["task_orchestration", "message_routing"],
            "timestamp": time.time()
        }
        self.message_bus.publish("agent.register", json.dumps(registration_data))
        logger.info(f"Orchestrator {self.name} ({self.entity_id}) registered on message bus.")

    def start(self):
        """Starts the background processing thread."""
        if self._processing_thread is None or not self._processing_thread.is_alive():
            self._stop_event.clear()
            self._processing_thread = threading.Thread(target=self._process_messages_loop, daemon=True)
            self._processing_thread.start()
            logger.info("BusOrchestrator processing thread started.")

    def stop(self):
        """Stops the background processing thread."""
        self._stop_event.set()
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5) # Give it some time to shut down
            if self._processing_thread.is_alive():
                logger.warning("BusOrchestrator processing thread did not terminate gracefully.")
        logger.info("BusOrchestrator processing thread stopped.")

    def _process_messages_loop(self):
        """Main loop for processing messages and tasks from the bus."""
        while not self._stop_event.is_set():
            # Process messages from subscribed topics
            for topic in self.message_bus.get_subscribed_topics():
                messages = self.message_bus.get_topic_messages(topic, after_id=self._last_processed_message_id[topic])
                for msg in messages:
                    self._last_processed_message_id[topic] = msg['id']
                    self._dispatch_message(topic, msg)
            
            # Process tasks in queue (simplified, no actual task execution here)
            # This orchestrator primarily routes and monitors.
            # The actual task execution logic will reside in individual agents.
            if self._task_queue:
                # This is where more sophisticated task allocation logic would go.
                # For now, simply acknowledge that a task is in the queue.
                pass # Task processing will be handled by individual agents that claim tasks

            time.sleep(0.1)  # Small delay to prevent busy-waiting

    def _dispatch_message(self, topic: str, message: Dict[str, Any]):
        """Dispatches messages to appropriate handlers based on topic."""
        if topic.startswith("agent.message."):
            self._handle_agent_message(topic, message)
        elif topic.startswith("agent.task."):
            self._handle_agent_task(topic, message)
        elif topic == "agent.register":
            self._handle_agent_registration(topic, message)
        elif topic == "agent.task.claim":
            self._handle_task_claim(topic, message)
        elif topic == "agent.task.update":
            self._handle_task_update(topic, message)
        elif topic == "agent.skill.advertise":
            self._handle_skill_advertisement(topic, message)

    def _handle_agent_registration(self, topic: str, message: Dict[str, Any]):
        """Handles agent registration messages."""
        try:
            reg_data = json.loads(message['content'])
            entity_id = reg_data['entity_id']
            self._registered_agents[entity_id] = reg_data
            logger.info(f"Agent registered: {reg_data['name']} ({entity_id})")
            # Optionally, publish a welcome message or sync state
            self.message_bus.publish(f"agent.presence.{entity_id}", json.dumps({
                "status": "online",
                "timestamp": time.time(),
                "orchestrator_entity": self.entity_id
            }))
        except Exception as e:
            logger.error(f"Error handling agent registration: {e}")

    def _handle_agent_message(self, topic: str, message: Dict[str, Any]):
        """Handles incoming agent messages and routes them."""
        try:
            # Example routing logic: if to_entity is specified, direct message
            msg_data = json.loads(message['content'])
            to_entity = msg_data.get("to_entity")
            from_entity = msg_data.get("from_entity")
            content = msg_data.get("content")

            if to_entity and self._registered_agents.get(to_entity):
                # Direct message to a specific agent
                self.message_bus.publish(f"agent.message.inbox.{to_entity}", json.dumps({
                    "from_entity": from_entity,
                    "content": content,
                    "timestamp": time.time()
                }))
                logger.info(f"Routed DM from {from_entity} to {to_entity}.")
            else:
                # General broadcast or unaddressed message
                logger.info(f"Received general agent message from {from_entity}: {content[:50]}...")
                # Further logic could be to route to relevant topic subscribers
        except Exception as e:
            logger.error(f"Error handling agent message: {e}")

    def _handle_agent_task(self, topic: str, message: Dict[str, Any]):
        """Handles incoming agent task messages."""
        try:
            task_data = json.loads(message['content'])
            task_id = task_data.get("task_id")
            task_type = task_data.get("task_type")
            target_entity = task_data.get("target_entity") # Who the task is for

            if task_id not in self._pending_tasks:
                self._pending_tasks[task_id] = task_data
                self._task_queue.append(task_id)
                logger.info(f"New task '{task_type}' (ID: {task_id}) received for {target_entity or 'any agent'}.")
                
                # If a specific agent is targeted, notify them
                if target_entity and self._registered_agents.get(target_entity):
                    self.message_bus.publish(f"agent.task.inbox.{target_entity}", json.dumps({
                        "task_id": task_id,
                        "task_type": task_type,
                        "payload": task_data.get("payload"),
                        "from_entity": task_data.get("from_entity"),
                        "timestamp": time.time()
                    }))
                    logger.info(f"Task {task_id} routed to targeted agent {target_entity}.")
                else:
                    # For untargeted tasks, broadcast to all capable agents or a general task topic
                    self.message_bus.publish("agent.tasks.general", json.dumps({
                        "task_id": task_id,
                        "task_type": task_type,
                        "payload": task_data.get("payload"),
                        "from_entity": task_data.get("from_entity"),
                        "timestamp": time.time()
                    }))
                    logger.info(f"Task {task_id} broadcast to general task topic.")

            # Additional logic for task claiming, completion, or failure would go here

        except Exception as e:
            logger.error(f"Error handling agent task: {e}")

    def _handle_task_claim(self, topic: str, message: Dict[str, Any]):
        """
        Handles agent task claim messages.
        Updates task status to 'claimed'.
        """
        try:
            claim_data = json.loads(message['content'])
            task_id = claim_data['task_id']
            claimer_id = claim_data['claimer_id']

            if task_id in self._pending_tasks:
                self._pending_tasks[task_id]["status"] = "claimed"
                self._pending_tasks[task_id]["claimed_by"] = claimer_id
                logger.info(f"Task {task_id} claimed by {claimer_id}.")
                # Notify other agents that the task is claimed
                self.message_bus.publish(f"agent.task.claimed.{task_id}", json.dumps(self._pending_tasks[task_id]))
            else:
                logger.warning(f"Task {task_id} not found for claiming by {claimer_id}.")
        except Exception as e:
            logger.error(f"Error handling task claim: {e}")

    def _handle_task_update(self, topic: str, message: Dict[str, Any]):
        """
        Handles agent task status update messages.
        """
        try:
            update_data = json.loads(message['content'])
            task_id = update_data['task_id']
            updater_id = update_data['updater_id']
            new_status = update_data['status']
            result = update_data.get("result")
            error = update_data.get("error")

            if task_id in self._pending_tasks:
                self._pending_tasks[task_id]["status"] = new_status
                self._pending_tasks[task_id]["last_updated_by"] = updater_id
                if result: self._pending_tasks[task_id]["result"] = result
                if error: self._pending_tasks[task_id]["error"] = error
                
                logger.info(f"Task {task_id} status updated to {new_status} by {updater_id}.")
                # Publish update to relevant topic
                self.message_bus.publish(f"agent.task.status.{task_id}", json.dumps(self._pending_tasks[task_id]))
            else:
                logger.warning(f"Task {task_id} not found for status update by {updater_id}.")
        except Exception as e:
            logger.error(f"Error handling task update: {e}")

    def _handle_skill_advertisement(self, topic: str, message: Dict[str, Any]):
        """
        Handles agent skill advertisement messages.
        Adds or updates skills for the advertising agent.
        """
        try:
            skill_data = json.loads(message['content'])
            entity_id = skill_data['entity_id']
            skills = skill_data['skills'] # List of skill dicts

            if entity_id in self._registered_agents:
                self._registered_agents[entity_id]["skills"] = skills
                logger.info(f"Skills updated for agent {entity_id}: {[s['name'] for s in skills]}.")
                # Optionally, publish a skill update notification
                self.message_bus.publish(f"agent.skills.updated.{entity_id}", json.dumps({
                    "entity_id": entity_id,
                    "skills": skills,
                    "timestamp": time.time()
                }))
            else:
                logger.warning(f"Received skill advertisement from unregistered agent {entity_id}.")
        except Exception as e:
            logger.error(f"Error handling skill advertisement: {e}")

    def send_agent_message(self, to_entity: Optional[str], content: str):
        """Allows the orchestrator to send messages."""
        message_data = {
            "from_entity": self.entity_id,
            "from_name": self.name,
            "content": content,
            "timestamp": time.time()
        }
        if to_entity:
            message_data["to_entity"] = to_entity
            self.message_bus.publish(f"agent.message.dm.{to_entity}", json.dumps(message_data))
            logger.info(f"Orchestrator sent DM to {to_entity}.")
        else:
            self.message_bus.publish(f"agent.message.general", json.dumps(message_data))
            logger.info(f"Orchestrator sent general message.")

    def create_agent_task(self, target_entity: Optional[str], task_type: str, payload: Dict[str, Any], required_skill: Optional[str] = None, ttl_seconds: Optional[int] = None):
        """Allows the orchestrator to create tasks."""
        task_id = str(hash(f"{self.entity_id}-{time.time()}-{task_type}")) # Simple hash for task ID
        task_data = {
            "task_id": task_id,
            "from_entity": self.entity_id,
            "from_name": self.name,
            "task_type": task_type,
            "payload": payload,
            "timestamp": time.time(),
            "status": "pending"
        }
        if required_skill:
            task_data["required_skill"] = required_skill

        if target_entity and self._registered_agents.get(target_entity):
            # Task is explicitly targeted to a known agent
            self.message_bus.publish(f"agent.task.assigned.{target_entity}", json.dumps(task_data))
            logger.info(f"Orchestrator created assigned task {task_id} for {target_entity}.")
        elif required_skill:
            # Attempt to find an agent with the required skill
            found_agent = None
            for agent_id, agent_data in self._registered_agents.items():
                if any(skill["name"] == required_skill for skill in agent_data.get("skills", [])):
                    found_agent = agent_id
                    break
            
            if found_agent:
                self.message_bus.publish(f"agent.task.assigned.{found_agent}", json.dumps(task_data))
                logger.info(f"Orchestrator created skill-routed task {task_id} for {found_agent} (skill: {required_skill}).")
            else:
                # No agent found with the skill, broadcast to general task topic
                self.message_bus.publish("agent.task.general", json.dumps(task_data))
                logger.info(f"Orchestrator created general task {task_id} (no agent with skill {required_skill} found).")
        else:
            # No specific target or required skill, broadcast to general task topic
            self.message_bus.publish("agent.task.general", json.dumps(task_data))
            logger.info(f"Orchestrator created general task {task_id}.")
        return task_id

    def get_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """Returns a dictionary of currently registered agents."""
        return self._registered_agents

    def get_pending_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Returns a dictionary of currently pending tasks."""
        return self._pending_tasks
