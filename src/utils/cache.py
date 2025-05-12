"""
Cache utility for tracking processed documents using SQLite.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List


class Cache:
    """SQLite-based cache for tracking processed documents."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store the SQLite database
        """
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Define database path
        self.db_path = os.path.join(cache_dir, "document_cache.db")
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create the cache table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TEXT,
                    last_accessed TEXT
                )
                ''')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error initializing cache database: {str(e)}")
            raise
    
    def is_cached(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM document_cache WHERE key = ?", 
                    (key,)
                )
                count = cursor.fetchone()[0]
                
                # Update last accessed timestamp if the key exists
                if count > 0:
                    cursor.execute(
                        "UPDATE document_cache SET last_accessed = ? WHERE key = ?",
                        (self.current_timestamp(), key)
                    )
                    conn.commit()
                    
                return count > 0
                
        except Exception as e:
            self.logger.warning(f"Error checking cache for key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            The cached value, or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM document_cache WHERE key = ?", 
                    (key,)
                )
                result = cursor.fetchone()
                
                if result:
                    # Update last accessed timestamp
                    cursor.execute(
                        "UPDATE document_cache SET last_accessed = ? WHERE key = ?",
                        (self.current_timestamp(), key)
                    )
                    conn.commit()
                    
                    # Parse the JSON value
                    return json.loads(result[0])
                    
                return None
                
        except Exception as e:
            self.logger.warning(f"Error retrieving cache for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Dict[str, Any]) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key to set
            value: Value to cache
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert value to JSON string
            value_json = json.dumps(value)
            now = self.current_timestamp()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert or replace the value
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO document_cache 
                    (key, value, created_at, last_accessed) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, value_json, now, now)
                )
                
                conn.commit()
                
            return True
            
        except Exception as e:
            self.logger.warning(f"Error setting cache for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM document_cache WHERE key = ?", (key,))
                conn.commit()
                
            return True
            
        except Exception as e:
            self.logger.warning(f"Error deleting cache for key {key}: {str(e)}")
            return False
    
    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get count of rows before deletion
                cursor.execute("SELECT COUNT(*) FROM document_cache")
                count = cursor.fetchone()[0]
                
                # Delete all entries
                cursor.execute("DELETE FROM document_cache")
                conn.commit()
                
            return count
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return 0
    
    def get_keys(self) -> List[str]:
        """
        Get all keys in the cache.
        
        Returns:
            List of cache keys
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key FROM document_cache")
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error getting cache keys: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM document_cache")
                total_count = cursor.fetchone()[0]
                
                # Get most recent entry
                cursor.execute(
                    "SELECT created_at FROM document_cache ORDER BY created_at DESC LIMIT 1"
                )
                most_recent = cursor.fetchone()
                most_recent = most_recent[0] if most_recent else None
                
                # Get oldest entry
                cursor.execute(
                    "SELECT created_at FROM document_cache ORDER BY created_at ASC LIMIT 1"
                )
                oldest = cursor.fetchone()
                oldest = oldest[0] if oldest else None
                
                return {
                    "total_entries": total_count,
                    "most_recent_entry": most_recent,
                    "oldest_entry": oldest,
                    "database_path": self.db_path
                }
                
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {str(e)}")
            return {
                "error": str(e),
                "database_path": self.db_path
            }
    
    @staticmethod
    def current_timestamp() -> str:
        """
        Get the current timestamp in ISO format.
        
        Returns:
            Current timestamp string
        """
        return datetime.utcnow().isoformat() 