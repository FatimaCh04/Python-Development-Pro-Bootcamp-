# 💬 PulseChat — Real-Time Chat Application

> A modern, real-time chat application built with Flask-SocketIO, Redis, SQLite, and Vanilla JavaScript.

PulseChat is a full-stack real-time chat application where multiple users can join chat rooms, exchange messages instantly, view message history, see online users, and receive live typing indicators.

The project demonstrates real-time WebSocket communication, room-based messaging, persistent database storage, Redis-powered session tracking, and a responsive modern frontend.

---

## ✨ Features

### 🔴 Real-Time Communication

* Instant messaging using WebSockets
* Real-time message broadcasting
* Socket.IO connection handling
* Automatic connection status updates
* Reconnection support

### 🏠 Chat Rooms

* Create or join a room
* Leave a room anytime
* Switch between rooms
* Room-based message isolation
* Users only receive messages from their current room

### 💬 Messaging

* Real-time message delivery
* Persistent message storage
* Message timestamps
* Own and other-user message styling
* System messages for join/leave events
* Empty message validation
* Message length validation

### 📜 Message History

* Previous messages are stored in SQLite
* Chat history loads automatically when joining a room
* Messages are displayed chronologically
* History remains available after application restart

### ⌨️ Typing Indicator

* Live typing status
* Shows when other users are typing
* Automatically stops after inactivity
* Supports multiple users typing
* User's own typing status is not displayed

### 👥 Online Users

* Real-time online user tracking
* Current room member list
* Online users count
* Join/leave/disconnect handling
* Redis-based session and room tracking

### 🎨 Color-Coded Usernames

* Each username receives a consistent color
* Same username keeps the same color
* Readable and accessible color selection

### 📱 Responsive UI

Designed for:

* Desktop
* Laptop
* Tablet
* Mobile
* iPhone-sized screens

---

## 🛠️ Tech Stack

| Technology          | Purpose                           |
| ------------------- | --------------------------------- |
| 🐍 Python           | Backend programming               |
| 🌐 Flask            | Web application framework         |
| ⚡ Flask-SocketIO    | Real-time WebSocket communication |
| 🗄️ SQLite          | Persistent message storage        |
| 🔴 Redis            | Active sessions & room tracking   |
| 🟨 JavaScript       | Frontend logic                    |
| 🔌 Socket.IO Client | Real-time frontend communication  |
| 🎨 HTML5            | Application structure             |
| 💅 CSS3             | Responsive UI & styling           |

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │       Browser       │
                    │ HTML / CSS / JS     │
                    └──────────┬──────────┘
                               │
                         Socket.IO
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Flask-SocketIO    │
                    │      Backend        │
                    └───────┬─────┬───────┘
                            │     │
                 ┌──────────┘     └──────────┐
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │     SQLite      │        │      Redis      │
        │                 │        │                 │
        │ Message History │        │ Active Users    │
        │ Persistent Data │        │ Room Sessions   │
        └─────────────────┘        └─────────────────┘
```

---

## 📁 Project Structure

```text
pulsechat/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── database/
│   ├── __init__.py
│   └── chat.db
│
├── services/
│   ├── __init__.py
│   ├── database_service.py
│   └── redis_service.py
│
├── sockets/
│   ├── __init__.py
│   └── chat_events.py
│
├── utils/
│   ├── __init__.py
│   └── helpers.py
│
├── templates/
│   └── index.html
│
└── static/
    ├── css/
    │   └── style.css
    │
    └── js/
        └── chat.js
```

---

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/pulsechat.git
cd pulsechat
```

Replace `YOUR-USERNAME` with your GitHub username.

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔴 Redis Setup

PulseChat uses Redis to maintain real-time session and room information.

Make sure Redis is installed and running before starting the application.

Verify Redis:

```bash
redis-cli ping
```

Expected response:

```text
PONG
```

If Redis is running on the default configuration, the application can use:

```text
localhost:6379
```

---

# ⚙️ Environment Configuration

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379/0
DATABASE_PATH=database/chat.db
```

> Never commit your real `.env` file to GitHub.

Use `.env.example` to show the required environment variables.

---

# 🗄️ Database

PulseChat uses SQLite for persistent chat messages.

The messages table contains:

| Field       | Description           |
| ----------- | --------------------- |
| `id`        | Unique message ID     |
| `username`  | Message sender        |
| `room`      | Chat room             |
| `message`   | Message content       |
| `color`     | Username color        |
| `timestamp` | Message creation time |

Messages are automatically stored when users send them.

---

# ▶️ Running the Application

Start the Flask-SocketIO server:

```bash
python app.py
```

The application will be available locally at:

```text
http://localhost:5000
```

Open the application in multiple browser tabs to test real-time communication.

---

# 🧪 Testing the Application

For the best demonstration:

### Browser Tab 1

```text
Username: Ali
Room: General
```

### Browser Tab 2

```text
Username: Sara
Room: General
```

Send a message from Ali.

Sara should receive the message instantly without refreshing the page.

You can also open another tab:

```text
Username: Ahmed
Room: Programming
```

Messages from the `General` room should not appear in the `Programming` room.

---

# 🔌 Socket.IO Events

PulseChat uses the following Socket.IO events:

| Event          | Description                         |
| -------------- | ----------------------------------- |
| `connect`      | Establish client connection         |
| `disconnect`   | Handle user disconnection           |
| `join_room`    | Join a chat room                    |
| `leave_room`   | Leave current room                  |
| `send_message` | Send and broadcast a message        |
| `typing`       | Notify users that someone is typing |
| `stop_typing`  | Stop typing notification            |

---

# 🔐 Security

The application includes basic security practices such as:

* Server-side input validation
* Empty message prevention
* Message length limits
* Username validation
* Room name validation
* User-generated content escaping
* XSS prevention
* Environment-based configuration
* Secrets excluded from Git

---

# 🎨 UI Highlights

PulseChat provides a modern chat experience with:

* Clean dashboard layout
* Responsive sidebar
* Online user list
* Connection indicator
* Message bubbles
* System notifications
* Typing indicator
* Color-coded usernames
* Mobile-friendly interface
* Smooth UI interactions
* Empty and loading states

---

# 📸 Screenshots

Add your project screenshots here after uploading them to GitHub.

Example:

```text
docs/
├── welcome-screen.png
├── chat-room.png
├── typing-indicator.png
└── mobile-view.png
```

Then add them to the README:

```markdown
## Screenshots

### Welcome Screen

![Welcome Screen](docs/welcome-screen.png)

### Chat Room

![Chat Room](docs/chat-room.png)

### Mobile View

![Mobile View](docs/mobile-view.png)
```

---

# 📌 Key Learning Outcomes

This project demonstrates practical knowledge of:

* Flask backend development
* WebSocket communication
* Flask-SocketIO
* Socket.IO event handling
* Real-time broadcasting
* Room-based communication
* Redis session management
* SQLite database persistence
* Frontend-backend integration
* JavaScript event handling
* Responsive web design
* Input validation
* Basic web security

---

# 🔮 Future Improvements

Possible future enhancements include:

* 🔐 User authentication
* 👤 User profiles and avatars
* 💬 Private messaging
* 🔔 Browser notifications
* 📎 File and image sharing
* 😀 Emoji picker
* ❤️ Message reactions
* ✏️ Edit messages
* 🗑️ Delete messages
* 🔎 Message search
* 🌙 Dark/light theme
* 🟢 User online/offline status
* 📊 Admin dashboard
* ☁️ Cloud deployment
* 🗄️ PostgreSQL support

---

# 🤝 Contributing

Contributions are welcome.

To contribute:

```bash
git clone https://github.com/YOUR-USERNAME/pulsechat.git
```

Create a new branch:

```bash
git checkout -b feature/new-feature
```

Make your changes and commit:

```bash
git add .
git commit -m "Add new feature"
```

Push your branch:

```bash
git push origin feature/new-feature
```

Then open a Pull Request.

---

# 📄 License

This project is available for educational and portfolio purposes.

---

# 👩‍💻 Author

**Your Name**

Built with ❤️ using Flask, Flask-SocketIO, Redis, SQLite, and JavaScript.

---

## ⭐ Support

If you found this project useful or interesting, consider giving the repository a ⭐ on GitHub.

**PulseChat — Connect. Chat. In Real Time.**
