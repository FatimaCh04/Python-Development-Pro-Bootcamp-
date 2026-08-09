document.addEventListener('DOMContentLoaded', () => {
    // Connect to Socket.IO with automatic reconnection
    const socket = io({
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000
    });

    // --- DOM Elements ---
    const screens = {
        join: document.getElementById('join-screen'),
        chat: document.getElementById('chat-screen')
    };

    const joinUI = {
        form: document.getElementById('join-form'),
        username: document.getElementById('username'),
        room: document.getElementById('room'),
        btn: document.getElementById('join-btn'),
        btnText: document.querySelector('.btn-text'),
        spinner: document.querySelector('.spinner')
    };

    const chatUI = {
        messages: document.getElementById('messages-container'),
        form: document.getElementById('chat-form'),
        input: document.getElementById('message-input'),
        sendBtn: document.getElementById('send-btn'),
        emptyState: document.getElementById('empty-state'),
        typing: document.getElementById('typing-indicator'),
        mainRoomName: document.getElementById('main-room-name'),
        connStatusText: document.querySelector('#connection-status .status-text'),
        connStatusDot: document.querySelector('#connection-status .status-dot'),
    };

    const sidebarUI = {
        sidebar: document.getElementById('sidebar'),
        overlay: document.getElementById('sidebar-overlay'),
        mobileOpen: document.getElementById('mobile-menu-btn'),
        mobileClose: document.getElementById('mobile-close-btn'),
        roomName: document.getElementById('sidebar-room-name'),
        onlineCount: document.getElementById('online-count'),
        usersList: document.getElementById('users-list'),
        currentUsername: document.getElementById('current-username'),
        currentUserAvatar: document.getElementById('current-user-avatar'),
        leaveBtn: document.getElementById('leave-btn')
    };

    // --- State Variables ---
    let currentUser = '';
    let currentRoom = '';
    let isTyping = false;
    let typingTimer = null;
    let activeTypers = new Set();
    let hasLoadedHistory = false;
    // hasJoinedRoom tracks whether the user has completed the join flow at least once.
    // It stays true across Socket.IO reconnects so that reconnects do not re-render history.
    let hasJoinedRoom = false;

    // --- Utilities ---
    const stringToColor = (str) => {
        if (!str) return 'hsl(0, 70%, 45%)';
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = (str.charCodeAt(i) + ((hash << 5) - hash)) | 0;
        }
        const h = Math.abs(hash) % 360;
        return `hsl(${h}, 70%, 45%)`;
    };

    const getInitials = (name) => {
        return name.substring(0, 2).toUpperCase();
    };

    const escapeHTML = (str) => {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };

    const formatTime = (timestamp) => {
        const date = timestamp ? new Date(timestamp + 'Z') : new Date();
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const scrollToBottom = () => {
        chatUI.messages.scrollTop = chatUI.messages.scrollHeight;
    };

    const setInvalid = (input, isInvalid) => {
        if (isInvalid) input.classList.add('is-invalid');
        else input.classList.remove('is-invalid');
    };

    const toggleEmptyState = () => {
        // Check if there are any message elements
        const hasMessages = chatUI.messages.querySelectorAll('.message-wrapper, .system-message, .history-divider').length > 0;
        chatUI.emptyState.style.display = hasMessages ? 'none' : 'flex';
    };

    // --- Mobile Sidebar Logic ---
    const closeSidebar = () => {
        sidebarUI.sidebar.classList.remove('open');
        sidebarUI.overlay.classList.remove('active');
    };
    
    sidebarUI.mobileOpen.addEventListener('click', () => {
        sidebarUI.sidebar.classList.add('open');
        sidebarUI.overlay.classList.add('active');
    });
    sidebarUI.mobileClose.addEventListener('click', closeSidebar);
    sidebarUI.overlay.addEventListener('click', closeSidebar);

    // --- Join Logic ---
    joinUI.form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const username = joinUI.username.value.trim();
        const room = joinUI.room.value.trim();
        let valid = true;
        
        if (!username || username.length > 30) {
            setInvalid(joinUI.username, true);
            valid = false;
        }
        if (!room || room.length > 30) {
            setInvalid(joinUI.room, true);
            valid = false;
        }

        if (valid) {
            // Loading State
            joinUI.btn.disabled = true;
            joinUI.btnText.style.display = 'none';
            joinUI.spinner.style.display = 'inline-block';

            currentUser = username;
            currentRoom = room;
            
            // Populate Sidebar Info
            sidebarUI.roomName.textContent = `#${escapeHTML(room)}`;
            chatUI.mainRoomName.textContent = `#${escapeHTML(room)}`;
            sidebarUI.currentUsername.textContent = escapeHTML(username);
            sidebarUI.currentUserAvatar.textContent = getInitials(username);
            sidebarUI.currentUserAvatar.style.backgroundColor = stringToColor(username);

            // Connect
            socket.emit('join_room', {
                username: currentUser,
                room: currentRoom
            });

            setTimeout(() => {
                screens.join.classList.remove('active');
                screens.chat.classList.add('active');
                chatUI.input.focus();
                hasJoinedRoom = true;
                
                // Reset Join UI
                joinUI.btn.disabled = false;
                joinUI.btnText.style.display = 'inline-block';
                joinUI.spinner.style.display = 'none';
            }, 300);
        }
    });

    joinUI.username.addEventListener('input', () => setInvalid(joinUI.username, false));
    joinUI.room.addEventListener('input', () => setInvalid(joinUI.room, false));

    // --- Leave Logic ---
    sidebarUI.leaveBtn.addEventListener('click', () => {
        socket.emit('leave_room', { username: currentUser, room: currentRoom });
        
        // Reset State
        currentUser = '';
        currentRoom = '';
        hasLoadedHistory = false;
        hasJoinedRoom = false;
        activeTypers.clear();
        updateTypingDisplay();
        
        // Clear DOM
        chatUI.messages.innerHTML = '';
        chatUI.messages.appendChild(chatUI.emptyState);
        sidebarUI.usersList.innerHTML = '';
        sidebarUI.onlineCount.textContent = '0';
        closeSidebar();
        
        screens.chat.classList.remove('active');
        screens.join.classList.add('active');
    });

    // --- Send Message Logic ---
    chatUI.input.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        chatUI.sendBtn.disabled = val.length === 0;

        if (val.length > 0 && !isTyping) {
            isTyping = true;
            socket.emit('typing', { username: currentUser, room: currentRoom });
        } else if (val.length === 0 && isTyping) {
            isTyping = false;
            socket.emit('stop_typing', { username: currentUser, room: currentRoom });
        }

        clearTimeout(typingTimer);
        typingTimer = setTimeout(() => {
            if (isTyping) {
                isTyping = false;
                socket.emit('stop_typing', { username: currentUser, room: currentRoom });
            }
        }, 2000);
    });

    chatUI.form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = chatUI.input.value.trim();
        
        if (text && text.length <= 1000) {
            socket.emit('send_message', {
                username: currentUser,
                room: currentRoom,
                message: text
            });
            
            chatUI.input.value = '';
            chatUI.sendBtn.disabled = true;
            
            if (isTyping) {
                isTyping = false;
                clearTimeout(typingTimer);
                socket.emit('stop_typing', { username: currentUser, room: currentRoom });
            }
        }
    });

    // --- Render Helpers ---
    const appendMessage = (msg) => {
        const isSelf = msg.username === currentUser;
        const color = stringToColor(msg.username);
        
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${isSelf ? 'self' : 'other'}`;
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        if (!isSelf) {
            const sender = document.createElement('span');
            sender.className = 'sender-name';
            sender.style.color = color;
            sender.textContent = msg.username; // Safe because textContent escapes
            header.appendChild(sender);
        }
        
        const time = document.createElement('span');
        time.className = 'message-time';
        time.textContent = formatTime(msg.timestamp);
        header.appendChild(time);
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = msg.message;
        
        wrapper.appendChild(header);
        wrapper.appendChild(bubble);
        
        chatUI.messages.appendChild(wrapper);
        toggleEmptyState();
        scrollToBottom();
    };

    const appendSystemMessage = (text) => {
        const div = document.createElement('div');
        div.className = 'system-message';
        div.textContent = text;
        chatUI.messages.appendChild(div);
        toggleEmptyState();
        scrollToBottom();
    };

    const updateTypingDisplay = () => {
        if (activeTypers.size === 0) {
            chatUI.typing.textContent = '';
        } else if (activeTypers.size === 1) {
            chatUI.typing.textContent = `${Array.from(activeTypers)[0]} is typing...`;
        } else if (activeTypers.size === 2) {
            const arr = Array.from(activeTypers);
            chatUI.typing.textContent = `${arr[0]} and ${arr[1]} are typing...`;
        } else {
            chatUI.typing.textContent = 'Several people are typing...';
        }
    };

    // --- Socket Event Listeners ---
    socket.on('connect', () => {
        chatUI.connStatusText.textContent = 'Connected';
        chatUI.connStatusDot.className = 'status-dot connected';
        
        // Re-join on reconnect so the backend registers this socket in the room.
        // hasLoadedHistory stays true → the message_history event from the server
        // will be ignored client-side (no duplicate history panel).
        if (currentUser && currentRoom && hasJoinedRoom) {
            socket.emit('join_room', { username: currentUser, room: currentRoom });
        }
    });

    socket.on('disconnect', () => {
        chatUI.connStatusText.textContent = 'Reconnecting...';
        chatUI.connStatusDot.className = 'status-dot disconnected';
        if (currentUser) {
            appendSystemMessage('Connection lost. Attempting to reconnect...');
        }
    });

    socket.on('message_history', (data) => {
        // Only render history the very first time we join (not on reconnects).
        // hasLoadedHistory stays true across Socket.IO reconnects.
        if (!hasLoadedHistory) {
            // Clear existing messages except the empty-state element
            Array.from(chatUI.messages.children).forEach(child => {
                if (child.id !== 'empty-state') child.remove();
            });
            
            if (data.messages && data.messages.length > 0) {
                const divider = document.createElement('div');
                divider.className = 'history-divider';
                divider.innerHTML = '<span>Chat History</span>';
                chatUI.messages.appendChild(divider);
                
                data.messages.forEach(msg => appendMessage(msg));
            }
            hasLoadedHistory = true;
            toggleEmptyState();
        }
        // If hasLoadedHistory is already true (reconnect case), ignore silently.
    });

    socket.on('receive_message', (msg) => {
        appendMessage(msg);
    });

    socket.on('system_message', (data) => {
        appendSystemMessage(data.message);
    });

    socket.on('room_users_update', (data) => {
        sidebarUI.usersList.innerHTML = '';
        if (data.users) {
            sidebarUI.onlineCount.textContent = data.users.length;
            data.users.forEach(user => {
                const li = document.createElement('li');
                li.className = 'user-item';
                
                const avatar = document.createElement('div');
                avatar.className = 'user-avatar';
                avatar.style.backgroundColor = stringToColor(user);
                avatar.textContent = getInitials(user);
                
                const name = document.createElement('span');
                name.textContent = user;
                if (user === currentUser) {
                    name.textContent += ' (You)';
                    name.style.fontWeight = '600';
                }
                
                li.appendChild(avatar);
                li.appendChild(name);
                sidebarUI.usersList.appendChild(li);
            });
        }
    });

    socket.on('user_typing', (data) => {
        if (data.username !== currentUser) {
            activeTypers.add(data.username);
            updateTypingDisplay();
        }
    });

    socket.on('user_stop_typing', (data) => {
        activeTypers.delete(data.username);
        updateTypingDisplay();
    });

    socket.on('error', (data) => {
        alert('Server Error: ' + data.message);
    });
});
