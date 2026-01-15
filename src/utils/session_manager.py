"""
🔐 Session Manager
Manages user sessions and WebSocket connections
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class Session:
    """Represents a user session"""
    session_id: str
    interface_id: str
    created_at: float
    last_activity: float
    user_data: Dict[str, Any] = field(default_factory=dict)
    websocket_connections: Set[str] = field(default_factory=set)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
    
    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """Check if session is expired"""
        return time.time() - self.last_activity > timeout_seconds
    
    def add_websocket(self, connection_id: str):
        """Add WebSocket connection to session"""
        self.websocket_connections.add(connection_id)
    
    def remove_websocket(self, connection_id: str):
        """Remove WebSocket connection from session"""
        self.websocket_connections.discard(connection_id)
    
    def has_active_connections(self) -> bool:
        """Check if session has active WebSocket connections"""
        return len(self.websocket_connections) > 0

class SessionManager:
    """Manages user sessions and WebSocket connections"""
    
    def __init__(self, session_timeout: int = 3600):
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = session_timeout
        self.websocket_connections: Dict[str, str] = {}  # connection_id -> session_id
        
        logger.info(f"🔐 SessionManager initialized with {session_timeout}s timeout")
    
    def create_session(self, interface_id: str, user_data: Optional[Dict[str, Any]] = None) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        current_time = time.time()
        
        session = Session(
            session_id=session_id,
            interface_id=interface_id,
            created_at=current_time,
            last_activity=current_time,
            user_data=user_data or {}
        )
        
        self.sessions[session_id] = session
        
        logger.info(f"✅ Created session {session_id} for interface {interface_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        
        if session:
            if session.is_expired(self.session_timeout):
                self.cleanup_session(session_id)
                return None
            
            session.update_activity()
            return session
        
        return None
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session activity timestamp"""
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
            return True
        return False
    
    def add_websocket_connection(self, session_id: str, connection_id: str) -> bool:
        """Add WebSocket connection to session"""
        session = self.get_session(session_id)
        if session:
            session.add_websocket(connection_id)
            self.websocket_connections[connection_id] = session_id
            logger.info(f"🔌 Added WebSocket {connection_id} to session {session_id}")
            return True
        return False
    
    def remove_websocket_connection(self, connection_id: str) -> Optional[str]:
        """Remove WebSocket connection and return session ID"""
        session_id = self.websocket_connections.pop(connection_id, None)
        
        if session_id:
            session = self.sessions.get(session_id)
            if session:
                session.remove_websocket(connection_id)
                logger.info(f"🔌 Removed WebSocket {connection_id} from session {session_id}")
            return session_id
        
        return None
    
    def get_session_by_websocket(self, connection_id: str) -> Optional[Session]:
        """Get session by WebSocket connection ID"""
        session_id = self.websocket_connections.get(connection_id)
        if session_id:
            return self.get_session(session_id)
        return None
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up a session and its connections"""
        session = self.sessions.pop(session_id, None)
        
        if session:
            # Remove all WebSocket connections for this session
            connections_to_remove = list(session.websocket_connections)
            for connection_id in connections_to_remove:
                self.websocket_connections.pop(connection_id, None)
            
            logger.info(f"🧹 Cleaned up session {session_id} with {len(connections_to_remove)} connections")
            return True
        
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.is_expired(self.session_timeout):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.cleanup_session(session_id)
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        self.cleanup_expired_sessions()  # Clean up first
        return len(self.sessions)
    
    def get_sessions_by_interface(self, interface_id: str) -> Dict[str, Session]:
        """Get all sessions for a specific interface"""
        interface_sessions = {}
        
        for session_id, session in self.sessions.items():
            if session.interface_id == interface_id and not session.is_expired(self.session_timeout):
                session.update_activity()
                interface_sessions[session_id] = session
        
        return interface_sessions
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        self.cleanup_expired_sessions()
        
        # Count sessions by interface
        interface_counts = {}
        total_connections = 0
        
        for session in self.sessions.values():
            interface_id = session.interface_id
            interface_counts[interface_id] = interface_counts.get(interface_id, 0) + 1
            total_connections += len(session.websocket_connections)
        
        return {
            "total_sessions": len(self.sessions),
            "total_websocket_connections": total_connections,
            "sessions_by_interface": interface_counts,
            "session_timeout": self.session_timeout
        }
    
    def update_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session user data"""
        session = self.get_session(session_id)
        if session:
            session.user_data.update(data)
            return True
        return False
    
    def get_session_data(self, session_id: str, key: Optional[str] = None) -> Any:
        """Get session user data"""
        session = self.get_session(session_id)
        if session:
            if key:
                return session.user_data.get(key)
            return session.user_data.copy()
        return None
    
    def list_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """List all active sessions with their info"""
        self.cleanup_expired_sessions()
        
        active_sessions = {}
        
        for session_id, session in self.sessions.items():
            active_sessions[session_id] = {
                "session_id": session_id,
                "interface_id": session.interface_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "websocket_connections": len(session.websocket_connections),
                "has_active_connections": session.has_active_connections(),
                "user_data_keys": list(session.user_data.keys())
            }
        
        return active_sessions
    
    def force_cleanup_session(self, session_id: str) -> bool:
        """Force cleanup of a session (admin function)"""
        return self.cleanup_session(session_id)
    
    def cleanup_all_sessions(self) -> int:
        """Clean up all sessions (admin function)"""
        session_count = len(self.sessions)
        
        # Get all session IDs
        all_session_ids = list(self.sessions.keys())
        
        # Clean up each session
        for session_id in all_session_ids:
            self.cleanup_session(session_id)
        
        logger.info(f"🧹 Force cleaned up all {session_count} sessions")
        return session_count
    
    def get_websocket_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "total_connections": len(self.websocket_connections),
            "connections_by_session": {
                session_id: len(session.websocket_connections)
                for session_id, session in self.sessions.items()
            }
        }
