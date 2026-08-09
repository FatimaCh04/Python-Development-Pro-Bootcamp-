import redis
import json
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class RedisService:
    """
    Handles active user session and room presence tracking.
    
    IMPORTANT DESIGN: Room membership is tracked by SOCKET_ID, not by username.
    This means:
    - One username with 3 tabs = 3 socket_id entries in the room set
    - Disconnect removes only that socket_id
    - "User left" is only announced when the username has NO remaining sockets in the room
    """
    
    def __init__(self, redis_url):
        self.fallback_sessions = {}   # sid -> {username, room}
        self.fallback_room_sockets = {}  # room -> {sid: username, ...}
        try:
            self.client = redis.from_url(redis_url)
            self.client.ping()
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Using in-memory fallback.")
            self.client = None

    def is_available(self):
        return self.client is not None

    # ------------------------------------------------------------------
    # Session tracking: sid -> {username, room}
    # ------------------------------------------------------------------

    def save_session(self, sid, username, room):
        """Links a socket session ID to a username and room."""
        if self.client:
            try:
                data = {'username': username, 'room': room}
                self.client.set(f'pulse:session:{sid}', json.dumps(data))
                return True
            except redis.RedisError as e:
                logger.warning(f"Redis save_session error: {e}")
        self.fallback_sessions[sid] = {'username': username, 'room': room}
        return True

    def get_session(self, sid):
        """Retrieves session data by socket ID."""
        if self.client:
            try:
                data = self.client.get(f'pulse:session:{sid}')
                return json.loads(data) if data else None
            except redis.RedisError as e:
                logger.warning(f"Redis get_session error: {e}")
        return self.fallback_sessions.get(sid)

    def delete_session(self, sid):
        """Removes a session record."""
        if self.client:
            try:
                self.client.delete(f'pulse:session:{sid}')
                return True
            except redis.RedisError as e:
                logger.warning(f"Redis delete_session error: {e}")
        self.fallback_sessions.pop(sid, None)
        return True

    # ------------------------------------------------------------------
    # Room socket tracking: room -> Hash {sid: username}
    # This lets us track MULTIPLE sockets (tabs) per username.
    # ------------------------------------------------------------------

    def add_socket_to_room(self, room, sid, username):
        """
        Records that socket `sid` (belonging to `username`) is in `room`.
        Multiple sockets from the same username are all individually tracked.
        """
        if self.client:
            try:
                self.client.hset(f'pulse:room_sockets:{room}', sid, username)
                return True
            except redis.RedisError as e:
                logger.warning(f"Redis add_socket_to_room error: {e}")
        # In-memory fallback
        if room not in self.fallback_room_sockets:
            self.fallback_room_sockets[room] = {}
        self.fallback_room_sockets[room][sid] = username
        return True

    def remove_socket_from_room(self, room, sid):
        """
        Removes a single socket from the room.
        Returns True if the username that owned this socket still has OTHER sockets
        remaining in the room (i.e., the user is still present via another tab).
        Returns False if this was the user's last socket (user truly left).
        """
        if self.client:
            try:
                # Get the username for this sid before deleting
                username_bytes = self.client.hget(f'pulse:room_sockets:{room}', sid)
                if not username_bytes:
                    return None, False  # Unknown sid, nothing to do
                username = username_bytes.decode('utf-8')
                
                # Remove this specific socket
                self.client.hdel(f'pulse:room_sockets:{room}', sid)
                
                # Check if username has any remaining sockets in this room
                all_users = self.client.hvals(f'pulse:room_sockets:{room}')
                still_present = any(u.decode('utf-8') == username for u in all_users)
                return username, still_present
            except redis.RedisError as e:
                logger.warning(f"Redis remove_socket_from_room error: {e}")
        
        # In-memory fallback
        room_sockets = self.fallback_room_sockets.get(room, {})
        username = room_sockets.pop(sid, None)
        if username is None:
            return None, False
        
        # Check if any remaining sockets belong to this username
        still_present = any(u == username for u in room_sockets.values())
        return username, still_present

    def get_room_users(self, room):
        """
        Returns the deduplicated, sorted list of active usernames in a room
        (derived from the socket-level tracking).
        """
        if self.client:
            try:
                all_users = self.client.hvals(f'pulse:room_sockets:{room}')
                unique_users = sorted(set(u.decode('utf-8') for u in all_users))
                return unique_users
            except redis.RedisError as e:
                logger.warning(f"Redis get_room_users error: {e}")
        
        # In-memory fallback
        room_sockets = self.fallback_room_sockets.get(room, {})
        return sorted(set(room_sockets.values()))

    def user_has_active_socket_in_room(self, room, username):
        """
        Checks whether a username has at least one active socket in the room.
        Used to suppress duplicate 'joined' announcements on reconnect.
        """
        if self.client:
            try:
                all_users = self.client.hvals(f'pulse:room_sockets:{room}')
                return any(u.decode('utf-8') == username for u in all_users)
            except redis.RedisError as e:
                logger.warning(f"Redis user_has_active_socket error: {e}")
        
        room_sockets = self.fallback_room_sockets.get(room, {})
        return any(u == username for u in room_sockets.values())
