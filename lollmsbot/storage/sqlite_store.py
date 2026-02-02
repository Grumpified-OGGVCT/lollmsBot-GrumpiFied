"""
SQLite storage backend for LollmsBot.

Provides persistent storage using SQLite with async support via aiosqlite.
Implements conversation history and agent state persistence.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from lollmsbot.storage import BaseStorage


class SqliteStore(BaseStorage):
    """SQLite-based storage backend.
    
    Implements BaseStorage interface using SQLite for persistence.
    Supports async operations and JSON serialization for complex data.
    
    Attributes:
        db_path: Path to the SQLite database file.
        _connection: Async database connection (initialized in _init_db).
    """
    
    backend_name: str = "sqlite"
    
    def __init__(self, db_path: str = "lollmsbot.db") -> None:
        """Initialize SqliteStore with database path.
        
        Args:
            db_path: Path to SQLite database file. Defaults to 'lollmsbot.db'.
        """
        self.db_path: str = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def _init_db(self) -> None:
        """Initialize database connection and create tables.
        
        Creates required tables if they don't exist:
        - conversations: Stores conversation metadata
        - messages: Stores individual messages with foreign key to conversations
        - agent_states: Stores serialized agent state
        """
        self._connection = await aiosqlite.connect(self.db_path)
        
        # Enable foreign keys
        await self._connection.execute("PRAGMA foreign_keys = ON")
        
        # Create conversations table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create messages table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        
        # Create agent_states table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS agent_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL UNIQUE,
                state_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_states_agent_id ON agent_states(agent_id)
        """)
        
        await self._connection.commit()
    
    async def _ensure_initialized(self) -> aiosqlite.Connection:
        """Ensure database is initialized and return connection.
        
        Returns:
            Active database connection.
        """
        if self._connection is None:
            await self._init_db()
        return self._connection
    
    async def save_conversation(self, user_id: str, messages: List[Dict[str, Any]]) -> bool:
        """Save or append conversation messages for a user.
        
        Creates a new conversation entry and stores all messages.
        Previous conversations for the user are preserved.
        
        Args:
            user_id: Unique identifier for the user.
            messages: List of message dictionaries with 'role', 'content', 'timestamp' keys.
            
        Returns:
            True if save was successful, False otherwise.
        """
        try:
            conn = await self._ensure_initialized()
            
            async with conn.cursor() as cursor:
                # Insert conversation record
                await cursor.execute(
                    "INSERT INTO conversations (user_id, created_at) VALUES (?, ?)",
                    (user_id, datetime.now().isoformat())
                )
                conversation_id = cursor.lastrowid
                
                # Insert all messages
                for msg in messages:
                    timestamp = msg.get("timestamp")
                    if isinstance(timestamp, datetime):
                        timestamp = timestamp.isoformat()
                    elif timestamp is None:
                        timestamp = datetime.now().isoformat()
                    
                    await cursor.execute(
                        "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                        (conversation_id, msg.get("role", "unknown"), msg.get("content", ""), timestamp)
                    )
                
                await conn.commit()
                return True
                
        except Exception:
            return False
    
    async def get_conversation(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a user.
        
        Returns messages from the most recent conversation for the user.
        
        Args:
            user_id: Unique identifier for the user.
            limit: Maximum number of recent messages to retrieve (None for all).
            
        Returns:
            List of message dictionaries ordered chronologically.
        """
        try:
            conn = await self._ensure_initialized()
            
            async with conn.cursor() as cursor:
                # Find the most recent conversation for this user
                await cursor.execute(
                    "SELECT id FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                    (user_id,)
                )
                row = await cursor.fetchone()
                
                if row is None:
                    return []
                
                conversation_id = row[0]
                
                # Build query with optional limit
                query = """
                    SELECT role, content, timestamp 
                    FROM messages 
                    WHERE conversation_id = ? 
                    ORDER BY timestamp ASC
                """
                params: List[Any] = [conversation_id]
                
                if limit is not None:
                    query = f"""
                        SELECT role, content, timestamp 
                        FROM messages 
                        WHERE conversation_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """
                    params.append(limit)
                
                await cursor.execute(query, params)
                rows = await cursor.fetchall()
                
                # Reverse if we used DESC with limit to get chronological order
                if limit is not None:
                    rows = list(reversed(rows))
                
                messages = []
                for role, content, timestamp in rows:
                    msg: Dict[str, Any] = {
                        "role": role,
                        "content": content,
                    }
                    if timestamp:
                        msg["timestamp"] = timestamp
                    messages.append(msg)
                
                return messages
                
        except Exception:
            return []
    
    async def save_agent_state(self, agent_id: str, state: Dict[str, Any]) -> bool:
        """Serialize and save agent state for later resumption.
        
        Args:
            agent_id: Unique identifier for the agent.
            state: Dictionary containing all serializable agent state.
            
        Returns:
            True if save was successful, False otherwise.
        """
        try:
            conn = await self._ensure_initialized()
            
            # Serialize state to JSON
            state_json = json.dumps(state, default=str)
            
            async with conn.cursor() as cursor:
                # Use UPSERT pattern for SQLite
                await cursor.execute("""
                    INSERT INTO agent_states (agent_id, state_json, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(agent_id) DO UPDATE SET
                        state_json = excluded.state_json,
                        updated_at = excluded.updated_at
                """, (agent_id, state_json, datetime.now().isoformat()))
                
                await conn.commit()
                return True
                
        except Exception:
            return False
    
    async def load_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load previously saved agent state.
        
        Args:
            agent_id: Unique identifier for the agent.
            
        Returns:
            State dictionary if found, None otherwise.
        """
        try:
            conn = await self._ensure_initialized()
            
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT state_json FROM agent_states WHERE agent_id = ?",
                    (agent_id,)
                )
                row = await cursor.fetchone()
                
                if row is None:
                    return None
                
                # Deserialize JSON
                state: Dict[str, Any] = json.loads(row[0])
                return state
                
        except Exception:
            return None
    
    async def delete_conversation(self, user_id: str) -> bool:
        """Delete all conversation history for a user.
        
        Args:
            user_id: Unique identifier for the user.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            conn = await self._ensure_initialized()
            
            async with conn.cursor() as cursor:
                # Delete conversations (cascades to messages via foreign key)
                await cursor.execute(
                    "DELETE FROM conversations WHERE user_id = ?",
                    (user_id,)
                )
                await conn.commit()
                return True
                
        except Exception:
            return False
    
    async def delete_agent_state(self, agent_id: str) -> bool:
        """Delete saved state for an agent.
        
        Args:
            agent_id: Unique identifier for the agent.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            conn = await self._ensure_initialized()
            
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM agent_states WHERE agent_id = ?",
                    (agent_id,)
                )
                await conn.commit()
                return cursor.rowcount > 0
                
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close storage connections and cleanup resources."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None