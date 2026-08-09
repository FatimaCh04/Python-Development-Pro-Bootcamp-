import sqlite3
import os
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class DatabaseService:
    """Handles all SQLite interactions."""
    
    def __init__(self, db_path):
        self.db_path = db_path

    def get_connection(self):
        """Returns a connected SQLite instance."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            return None

    def initialize_database(self):
        """Creates the database and schema if they don't exist."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = self.get_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    room TEXT NOT NULL,
                    message TEXT NOT NULL,
                    color TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize schema: {e}")
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def save_message(self, username, room, message, color):
        """Persists a new message and returns its saved dictionary."""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                return None
                
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (username, room, message, color)
                VALUES (?, ?, ?, ?)
            ''', (username, room, message, color))
            
            msg_id = cursor.lastrowid
            conn.commit()
            
            cursor.execute('SELECT * FROM messages WHERE id = ?', (msg_id,))
            saved_msg = cursor.fetchone()
            
            return dict(saved_msg) if saved_msg else None
        except sqlite3.Error as e:
            logger.error(f"Error saving message: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def get_room_history(self, room, limit=100):
        """Fetches the latest messages for a room."""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            # Order DESC to get latest, then reverse back to ASC
            cursor.execute('''
                SELECT * FROM (
                    SELECT id, username, room, message, color, timestamp 
                    FROM messages 
                    WHERE room = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ) ORDER BY timestamp ASC
            ''', (room, limit))
            
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching history: {e}")
            return []
        finally:
            if conn:
                conn.close()
