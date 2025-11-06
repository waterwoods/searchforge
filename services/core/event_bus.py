"""
Minimal Event Bus for Service Decoupling
=========================================
In-memory pub/sub based on asyncio.Queue for event-driven architecture.

Features:
- Topic-based routing
- Async handler support
- No persistence (in-memory only)
- < 150 LOC

Usage:
    from services.core.event_bus import EventBus
    
    bus = EventBus()
    
    # Subscribe to topic
    async def handler(payload: dict):
        print(f"Received: {payload}")
    
    bus.subscribe("topic.name", handler)
    
    # Publish event
    await bus.publish("topic.name", {"key": "value"})
"""

import asyncio
import logging
from typing import Callable, Dict, List, Any, Coroutine
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventBus:
    """
    Simple in-memory event bus for pub/sub messaging.
    """
    
    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._queues: Dict[str, asyncio.Queue] = {}
        self._tasks: List[asyncio.Task] = []
        logger.info("[EVENT_BUS] Initialized")
    
    def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], Coroutine]) -> None:
        """
        Subscribe a handler to a topic.
        
        Args:
            topic: Topic name (e.g., "force_override.applied")
            handler: Async function to handle events
        """
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError(f"Handler for topic '{topic}' must be async")
        
        self._subscribers[topic].append(handler)
        logger.info(f"[EVENT_BUS] Subscribed handler to topic: {topic}")
    
    def unsubscribe(self, topic: str, handler: Callable) -> None:
        """
        Unsubscribe a handler from a topic.
        
        Args:
            topic: Topic name
            handler: Handler function to remove
        """
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(handler)
                logger.info(f"[EVENT_BUS] Unsubscribed handler from topic: {topic}")
            except ValueError:
                logger.warning(f"[EVENT_BUS] Handler not found for topic: {topic}")
    
    async def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        """
        Publish an event to all subscribers of a topic.
        
        Args:
            topic: Topic name
            payload: Event data dictionary
        """
        handlers = self._subscribers.get(topic, [])
        
        if not handlers:
            logger.debug(f"[EVENT_BUS] No subscribers for topic: {topic}")
            return
        
        logger.debug(f"[EVENT_BUS] Publishing to topic '{topic}': {payload}")
        
        # Execute all handlers concurrently
        tasks = [self._execute_handler(topic, handler, payload) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_handler(self, topic: str, handler: Callable, payload: Dict[str, Any]) -> None:
        """
        Execute a single handler with error handling.
        
        Args:
            topic: Topic name (for logging)
            handler: Handler function
            payload: Event data
        """
        try:
            await handler(payload)
        except Exception as e:
            logger.error(f"[EVENT_BUS] Handler error for topic '{topic}': {e}", exc_info=True)
    
    def list_topics(self) -> List[str]:
        """
        Get list of all topics with subscribers.
        
        Returns:
            List of topic names
        """
        return list(self._subscribers.keys())
    
    def subscriber_count(self, topic: str) -> int:
        """
        Get number of subscribers for a topic.
        
        Args:
            topic: Topic name
            
        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(topic, []))
    
    async def close(self) -> None:
        """Clean up event bus resources."""
        # Cancel all running tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self._subscribers.clear()
        self._queues.clear()
        logger.info("[EVENT_BUS] Closed")


# Global event bus instance
_global_bus: EventBus = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    
    Returns:
        Global EventBus instance
    """
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus

