from flask import request
from flask_socketio import emit, join_room, leave_room
from config import Config
from utils.helpers import sanitize_string, setup_logger

logger = setup_logger(__name__)

def register_socket_events(socketio, db_service, redis_service):
    """Registers all chat-related Socket.IO events."""
    
    def broadcast_room_users(room):
        """Fetches the deduplicated user list and broadcasts it to the room."""
        users = redis_service.get_room_users(room)
        emit('room_users_update', {'users': users}, to=room)

    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        emit('connection_established', {'status': 'success'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """
        Handles genuine socket disconnections.
        
        CRITICAL LOGIC:
        - Remove only THIS socket (by sid) from the room.
        - Only broadcast "left the room" if this was the user's LAST socket.
        - If the user still has other tabs open, they remain present silently.
        """
        sid = request.sid
        logger.info(f"Client disconnected: {sid}")
        
        # Retrieve which room/user this socket belonged to
        session = redis_service.get_session(sid)
        if not session:
            return  # Unknown session, nothing to clean up
            
        username = session.get('username')
        room = session.get('room')
        
        if not username or not room:
            redis_service.delete_session(sid)
            return

        # Remove this socket from the room.
        # Returns (username, still_present):
        #   still_present=True  → user has other tabs open → do NOT announce leave
        #   still_present=False → this was the last tab → announce leave
        _, still_present = redis_service.remove_socket_from_room(room, sid)
        redis_service.delete_session(sid)
        
        leave_room(room)
        
        if not still_present:
            # User's last connection is gone — announce departure
            logger.info(f"{username} truly left {room} (last socket disconnected)")
            emit('system_message', {
                'message': f"{username} left the room",
                'type': 'leave'
            }, to=room)
            broadcast_room_users(room)
        else:
            # User still has other tabs open — just quietly update the user list
            logger.info(f"{username} disconnected one tab but is still in {room}")
            broadcast_room_users(room)

    @socketio.on('join_room')
    def handle_join_room(data):
        """
        Handles a user joining a room.
        
        RECONNECTION HANDLING:
        - If the username already has active sockets in this room (e.g., reconnecting tab),
          we silently re-add the socket WITHOUT broadcasting "joined the room".
        - This prevents duplicate join notifications on Socket.IO reconnects.
        """
        raw_username = data.get('username', '')
        raw_room = data.get('room', '')
        
        username = sanitize_string(raw_username, Config.MAX_USERNAME_LEN)
        room = sanitize_string(raw_room, Config.MAX_ROOM_LEN)
        
        if not username or not room:
            emit('error', {'message': 'Invalid username or room.'})
            return
            
        sid = request.sid
        
        # Check if this username is already present in the room via another socket.
        # This is the case during reconnection — the old socket may not have fully
        # cleaned up yet, or the user has another tab open.
        already_present = redis_service.user_has_active_socket_in_room(room, username)
        
        # Register this socket in the room (socket-level tracking)
        join_room(room)
        redis_service.save_session(sid, username, room)
        redis_service.add_socket_to_room(room, sid, username)
        
        # Always send history to this specific socket (private emit, no `to=room`)
        history = db_service.get_room_history(room)
        emit('message_history', {'messages': history})
        
        if not already_present:
            # First connection for this username in this room — announce arrival
            emit('system_message', {
                'message': f"{username} joined the room",
                'type': 'join'
            }, to=room)
        else:
            # Reconnecting or opening a second tab — do not announce again
            logger.info(f"{username} re-joined/reconnected to {room} (already present)")
        
        # Always update the user list (count might change even on silent re-join)
        broadcast_room_users(room)

    @socketio.on('leave_room')
    def handle_leave_room(data):
        """
        Handles explicit 'Leave Room' button clicks.
        Always removes the user completely and announces their departure.
        """
        raw_username = data.get('username', '')
        raw_room = data.get('room', '')
        sid = request.sid
        
        username = sanitize_string(raw_username, Config.MAX_USERNAME_LEN)
        room = sanitize_string(raw_room, Config.MAX_ROOM_LEN)
        
        if not username or not room:
            return
        
        # Remove this socket from the room
        redis_service.remove_socket_from_room(room, sid)
        redis_service.delete_session(sid)
        leave_room(room)
        
        # Explicit leave always announces departure (regardless of other tabs)
        emit('system_message', {
            'message': f"{username} left the room",
            'type': 'leave'
        }, to=room)
        
        broadcast_room_users(room)

    @socketio.on('send_message')
    def handle_send_message(data):
        raw_username = data.get('username', '')
        raw_room = data.get('room', '')
        raw_message = data.get('message', '')
        color = data.get('color', 'hsl(0,0%,50%)')
        
        username = sanitize_string(raw_username, Config.MAX_USERNAME_LEN)
        room = sanitize_string(raw_room, Config.MAX_ROOM_LEN)
        message = sanitize_string(raw_message, Config.MAX_MESSAGE_LEN)
        
        if not username or not room or not message:
            emit('error', {'message': 'Cannot send empty or invalid message.'})
            return
            
        saved_msg = db_service.save_message(username, room, message, color)
        
        if saved_msg:
            emit('receive_message', saved_msg, to=room)
        else:
            emit('error', {'message': 'Failed to save message.'})

    @socketio.on('typing')
    def handle_typing(data):
        room = sanitize_string(data.get('room', ''), Config.MAX_ROOM_LEN)
        username = sanitize_string(data.get('username', ''), Config.MAX_USERNAME_LEN)
        if room and username:
            emit('user_typing', {'username': username}, to=room, include_self=False)

    @socketio.on('stop_typing')
    def handle_stop_typing(data):
        room = sanitize_string(data.get('room', ''), Config.MAX_ROOM_LEN)
        username = sanitize_string(data.get('username', ''), Config.MAX_USERNAME_LEN)
        if room and username:
            emit('user_stop_typing', {'username': username}, to=room, include_self=False)
