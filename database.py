"""
SQLite database module for WhosOn Discord Bot

This module handles all database operations using SQLite for persistent storage.
"""

import sqlite3
import asyncio
import aiosqlite
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import asynccontextmanager

logger = logging.getLogger('WhosOn.Database')

# Database configuration
DATABASE_FILE = 'whoson.db'
DATABASE_VERSION = 1

# SQL Schema
SCHEMA = """
-- Version tracking table
CREATE TABLE IF NOT EXISTS db_version (
    version INTEGER PRIMARY KEY,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main servers table
CREATE TABLE IF NOT EXISTS tracked_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    server_key TEXT NOT NULL,
    address TEXT NOT NULL,
    nickname TEXT,
    server_type TEXT NOT NULL CHECK(server_type IN ('java', 'bedrock')),
    voice_channel_id TEXT NOT NULL,
    text_channel_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, server_key)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_guild_id ON tracked_servers(guild_id);
CREATE INDEX IF NOT EXISTS idx_server_key ON tracked_servers(server_key);

-- Trigger to update the updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_tracked_servers_timestamp 
AFTER UPDATE ON tracked_servers
BEGIN
    UPDATE tracked_servers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""


class Database:
    """Async SQLite database handler for WhosOn bot"""
    
    def __init__(self, db_path: str = DATABASE_FILE):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        
    @asynccontextmanager
    async def _get_connection(self):
        """Get a database connection with proper error handling"""
        async with aiosqlite.connect(self.db_path) as conn:
            # Enable foreign keys
            await conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            
    async def init_database(self):
        """Initialize the database with schema"""
        async with self._lock:
            async with self._get_connection() as conn:
                # Create schema
                await conn.executescript(SCHEMA)
                
                # Check and update version
                cursor = await conn.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
                row = await cursor.fetchone()
                
                if row is None or row[0] < DATABASE_VERSION:
                    await conn.execute(
                        "INSERT INTO db_version (version) VALUES (?)",
                        (DATABASE_VERSION,)
                    )
                    logger.info(f"Database initialized to version {DATABASE_VERSION}")
                
                await conn.commit()
                
    async def add_server(self, guild_id: str, server_key: str, server_data: Dict[str, Any]) -> bool:
        """Add a new server to track"""
        async with self._lock:
            try:
                async with self._get_connection() as conn:
                    await conn.execute("""
                        INSERT INTO tracked_servers 
                        (guild_id, server_key, address, nickname, server_type, 
                         voice_channel_id, text_channel_id, message_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        guild_id,
                        server_key,
                        server_data['address'],
                        server_data.get('nickname'),
                        server_data['type'],
                        str(server_data['voice_channel_id']),
                        str(server_data['text_channel_id']),
                        str(server_data['message_id'])
                    ))
                    await conn.commit()
                    logger.info(f"Added server {server_data['address']} for guild {guild_id}")
                    return True
            except sqlite3.IntegrityError:
                logger.error(f"Server {server_key} already exists for guild {guild_id}")
                return False
            except Exception as e:
                logger.error(f"Error adding server: {e}")
                return False
                
    async def remove_server(self, guild_id: str, server_key: str) -> bool:
        """Remove a tracked server"""
        async with self._lock:
            try:
                async with self._get_connection() as conn:
                    cursor = await conn.execute(
                        "DELETE FROM tracked_servers WHERE guild_id = ? AND server_key = ?",
                        (guild_id, server_key)
                    )
                    await conn.commit()
                    
                    if cursor.rowcount > 0:
                        logger.info(f"Removed server {server_key} from guild {guild_id}")
                        return True
                    else:
                        logger.warning(f"Server {server_key} not found in guild {guild_id}")
                        return False
            except Exception as e:
                logger.error(f"Error removing server: {e}")
                return False
                
    async def get_server(self, guild_id: str, server_key: str) -> Optional[Dict[str, Any]]:
        """Get a specific server's data"""
        async with self._get_connection() as conn:
            cursor = await conn.execute("""
                SELECT address, nickname, server_type, voice_channel_id, 
                       text_channel_id, message_id, created_at, updated_at
                FROM tracked_servers
                WHERE guild_id = ? AND server_key = ?
            """, (guild_id, server_key))
            
            row = await cursor.fetchone()
            if row:
                return {
                    'address': row[0],
                    'nickname': row[1],
                    'type': row[2],
                    'voice_channel_id': int(row[3]),
                    'text_channel_id': int(row[4]),
                    'message_id': int(row[5]),
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            return None
            
    async def get_guild_servers(self, guild_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all servers for a guild"""
        servers = {}
        async with self._get_connection() as conn:
            cursor = await conn.execute("""
                SELECT server_key, address, nickname, server_type, 
                       voice_channel_id, text_channel_id, message_id
                FROM tracked_servers
                WHERE guild_id = ?
                ORDER BY created_at
            """, (guild_id,))
            
            async for row in cursor:
                servers[row[0]] = {
                    'address': row[1],
                    'nickname': row[2],
                    'type': row[3],
                    'voice_channel_id': int(row[4]),
                    'text_channel_id': int(row[5]),
                    'message_id': int(row[6])
                }
                
        return servers
        
    async def get_all_guilds_servers(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all servers for all guilds (for background updates)"""
        guilds_data = {}
        async with self._get_connection() as conn:
            cursor = await conn.execute("""
                SELECT guild_id, server_key, address, nickname, server_type,
                       voice_channel_id, text_channel_id, message_id
                FROM tracked_servers
                ORDER BY guild_id, created_at
            """)
            
            async for row in cursor:
                guild_id = row[0]
                if guild_id not in guilds_data:
                    guilds_data[guild_id] = {}
                    
                guilds_data[guild_id][row[1]] = {
                    'address': row[2],
                    'nickname': row[3],
                    'type': row[4],
                    'voice_channel_id': int(row[5]),
                    'text_channel_id': int(row[6]),
                    'message_id': int(row[7])
                }
                
        return guilds_data
        
    async def update_message_id(self, guild_id: str, server_key: str, message_id: int) -> bool:
        """Update the message ID for a server"""
        async with self._lock:
            try:
                async with self._get_connection() as conn:
                    await conn.execute(
                        "UPDATE tracked_servers SET message_id = ? WHERE guild_id = ? AND server_key = ?",
                        (str(message_id), guild_id, server_key)
                    )
                    await conn.commit()
                    return True
            except Exception as e:
                logger.error(f"Error updating message ID: {e}")
                return False
                
    async def remove_guild_servers(self, guild_id: str) -> int:
        """Remove all servers for a guild (when bot is removed)"""
        async with self._lock:
            try:
                async with self._get_connection() as conn:
                    cursor = await conn.execute(
                        "DELETE FROM tracked_servers WHERE guild_id = ?",
                        (guild_id,)
                    )
                    await conn.commit()
                    
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        logger.info(f"Removed {deleted_count} servers from guild {guild_id}")
                    return deleted_count
            except Exception as e:
                logger.error(f"Error removing guild servers: {e}")
                return 0
                
    async def get_guild_count(self) -> int:
        """Get the number of guilds with tracked servers"""
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(DISTINCT guild_id) FROM tracked_servers"
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
            
    async def get_total_server_count(self) -> int:
        """Get the total number of tracked servers"""
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM tracked_servers"
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
            
    async def get_server_stats(self) -> Dict[str, int]:
        """Get statistics about tracked servers"""
        stats = {
            'total_servers': 0,
            'java_servers': 0,
            'bedrock_servers': 0,
            'guilds': 0
        }
        
        async with self._get_connection() as conn:
            # Total servers
            cursor = await conn.execute("SELECT COUNT(*) FROM tracked_servers")
            row = await cursor.fetchone()
            stats['total_servers'] = row[0] if row else 0
            
            # Java servers
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM tracked_servers WHERE server_type = 'java'"
            )
            row = await cursor.fetchone()
            stats['java_servers'] = row[0] if row else 0
            
            # Bedrock servers
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM tracked_servers WHERE server_type = 'bedrock'"
            )
            row = await cursor.fetchone()
            stats['bedrock_servers'] = row[0] if row else 0
            
            # Unique guilds
            cursor = await conn.execute(
                "SELECT COUNT(DISTINCT guild_id) FROM tracked_servers"
            )
            row = await cursor.fetchone()
            stats['guilds'] = row[0] if row else 0
            
        return stats
        
    async def cleanup_orphaned_servers(self, valid_guild_ids: List[str]) -> int:
        """Remove servers from guilds the bot is no longer in"""
        async with self._lock:
            try:
                async with self._get_connection() as conn:
                    # Get guild IDs that have servers but aren't in the valid list
                    cursor = await conn.execute(
                        "SELECT DISTINCT guild_id FROM tracked_servers"
                    )
                    all_guild_ids = [row[0] for row in await cursor.fetchall()]
                    
                    orphaned_guilds = [gid for gid in all_guild_ids if gid not in valid_guild_ids]
                    
                    if not orphaned_guilds:
                        return 0
                        
                    # Delete orphaned servers
                    placeholders = ','.join('?' * len(orphaned_guilds))
                    cursor = await conn.execute(
                        f"DELETE FROM tracked_servers WHERE guild_id IN ({placeholders})",
                        orphaned_guilds
                    )
                    await conn.commit()
                    
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        logger.info(f"Cleaned up {deleted_count} orphaned servers from {len(orphaned_guilds)} guilds")
                    
                    return deleted_count
            except Exception as e:
                logger.error(f"Error cleaning up orphaned servers: {e}")
                return 0


# Global database instance
db = Database()