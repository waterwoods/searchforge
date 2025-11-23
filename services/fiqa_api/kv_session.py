"""
KV Session Management

Provides logical KV-cache behavior based on session_id, maintaining conversation
context for multi-turn dialogues. This is NOT GPU-level KV-cache, but rather
a service-side message history cache with hit rate statistics.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except Exception:
    pass


# Constants for session management
MAX_TURNS_PER_SESSION = 8
MAX_SESSION_TOKENS = 8000


@dataclass
class KVSession:
    """Represents a KV-cache session with conversation history."""
    session_id: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    total_tokens: int = 0
    num_turns: int = 0

    def add_turn(self, user_message: Dict[str, str], assistant_message: Dict[str, str], tokens_delta: int = 0):
        """Add a conversation turn (user + assistant messages)."""
        self.messages.append(user_message)
        self.messages.append(assistant_message)
        self.total_tokens += tokens_delta
        self.num_turns += 1
        self.last_used_at = time.time()

    def truncate_if_needed(self):
        """Truncate oldest messages if session exceeds limits."""
        # Truncate by turns
        while self.num_turns > MAX_TURNS_PER_SESSION and len(self.messages) >= 2:
            # Remove oldest turn (user + assistant)
            if len(self.messages) >= 2:
                self.messages.pop(0)  # Remove user message
                self.messages.pop(0)  # Remove assistant message
                self.num_turns -= 1
        
        # Truncate by tokens (rough heuristic: assume ~100 tokens per message)
        # This is a simple approximation; in production, you'd want actual token counting
        estimated_tokens = len(self.messages) * 100
        while estimated_tokens > MAX_SESSION_TOKENS and len(self.messages) >= 2:
            self.messages.pop(0)
            self.messages.pop(0)
            self.num_turns = max(0, self.num_turns - 1)
            estimated_tokens = len(self.messages) * 100


class KVSessionStore:
    """In-memory store for KV sessions."""
    
    def __init__(self):
        self._sessions: Dict[str, KVSession] = {}
    
    def get_or_create(self, session_id: str) -> KVSession:
        """Get existing session or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = KVSession(session_id=session_id)
        session = self._sessions[session_id]
        session.last_used_at = time.time()
        return session
    
    def get(self, session_id: str) -> Optional[KVSession]:
        """Get session by ID, or None if not found."""
        return self._sessions.get(session_id)
    
    def update(
        self,
        session_id: str,
        user_message: Dict[str, str],
        assistant_message: Dict[str, str],
        tokens_delta: int = 0,
    ) -> KVSession:
        """Update session with a new conversation turn."""
        session = self.get_or_create(session_id)
        session.add_turn(user_message, assistant_message, tokens_delta)
        session.truncate_if_needed()
        return session
    
    def drop(self, session_id: str) -> None:
        """Remove a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def clear(self) -> None:
        """Clear all sessions."""
        self._sessions.clear()
    
    def size(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)


# Module-level singleton
_SESSION_STORE: Optional[KVSessionStore] = None


def get_kv_session_store() -> KVSessionStore:
    """Get the singleton KV session store."""
    global _SESSION_STORE
    if _SESSION_STORE is None:
        _SESSION_STORE = KVSessionStore()
    return _SESSION_STORE

