# 📝 Day 90 — Disappearing Text Writing App

A desktop productivity application built with **Python and Tkinter** as part of the **100 Days of Code: The Complete Python Pro Bootcamp**.

The application is designed to encourage continuous writing. Once the user starts typing, a timer begins counting down. Every new keystroke resets the timer. If the user stops typing for the configured period, all written text disappears.

---

## 🚀 Project Overview

The **Disappearing Text Writing App** is a simple but challenging writing tool designed to help users write continuously without stopping to overthink or edit their work.

The application monitors keyboard input and automatically clears the writing area when the user stops typing.

### Core Concept

```text
Start Typing
     ↓
Timer Starts
     ↓
Keep Typing
     ↓
Timer Resets
     ↓
Stop Typing
     ↓
Timer Expires
     ↓
Text Disappears
```

---

## ✨ Features

* 📝 Real-time writing area
* ⏱️ Automatic inactivity timer
* 🔄 Timer resets with every keystroke
* 💨 Automatically clears text after inactivity
* 🔢 Live word counter
* ↻ Manual reset button
* 🚪 Exit confirmation
* 🎨 Clean and modern Tkinter interface
* ⌨️ Keyboard event handling
* 💻 Desktop application with no external services

---

## 🛠️ Technologies Used

| Technology     | Purpose                   |
| -------------- | ------------------------- |
| **Python**     | Core programming language |
| **Tkinter**    | Graphical user interface  |
| **`after()`**  | Timer functionality       |
| **Events**     | Keyboard input detection  |
| **Messagebox** | Exit confirmation         |

---

## 📂 Project Structure

```text
Day-90-Disappearing-Text-App/
│
├── main.py
├── requirements.txt
└── README.md
```

No external images, databases, APIs, or assets are required.

---

## ⚙️ Requirements

* Python 3.10+
* Tkinter

Tkinter is normally included with standard Python installations.

To verify Tkinter:

```bash
python -m tkinter
```

If a small Tkinter window appears, it is installed correctly.

---

## ▶️ Installation & Setup

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day-90-Disappearing-Text-App
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

#### Windows

```powershell
venv\Scripts\activate
```

#### macOS/Linux

```bash
source venv/bin/activate
```

### 5. Install Requirements

```bash
pip install -r requirements.txt
```

Since the project only uses Tkinter, no additional third-party packages are necessary.

---

## ▶️ Run the Application

Run:

```bash
python main.py
```

The application window will open automatically.

---

## 🧪 How to Use

### Step 1 — Start Writing

Click inside the writing area and start typing.

### Step 2 — Keep Typing

Every key press resets the inactivity timer.

### Step 3 — Stop Typing

If you stop typing for **5 seconds**, the application automatically removes all text.

### Step 4 — Start Again

Once the text disappears, you can begin a new writing session.

### Step 5 — Reset Manually

Use the **Reset** button whenever you want to clear the writing area manually.

---

## ⏱️ Timer Configuration

The inactivity period can be changed in `main.py`.

The default value is:

```python
DISAPPEAR_TIME = 5000
```

The value is measured in milliseconds.

For example:

```python
DISAPPEAR_TIME = 10000
```

sets the timer to **10 seconds**.

---

## 🧠 Key Python Concepts Practiced

This project focuses on several important Python and Tkinter concepts:

* Tkinter GUI development
* Creating and configuring widgets
* `Frame`
* `Label`
* `Text`
* `Button`
* Keyboard events
* Event binding
* `after()`
* `after_cancel()`
* Functions
* Global state
* String processing
* Word counting
* Message boxes
* Window protocols

---

## 🔍 Important Code Concepts

### Tkinter Timer

The application uses:

```python
window.after(
    DISAPPEAR_TIME,
    disappear_text
)
```

This schedules a function to execute after the specified number of milliseconds.

---

### Resetting the Timer

When the user types again, the previous timer is cancelled:

```python
window.after_cancel(timer_id)
```

A new timer is then started.

This creates the continuous-writing behavior.

---

### Keyboard Event Handling

The writing area listens for key-release events:

```python
text_area.bind(
    "<KeyRelease>",
    handle_typing
)
```

Every time the user releases a key, the timer is reset and the word count is updated.

---

## 🎯 Learning Objectives

By completing this project, I practiced:

* Building desktop applications with Python
* Working with Tkinter
* Handling user input
* Binding keyboard events
* Creating timers
* Managing scheduled events
* Updating GUI elements dynamically
* Structuring a Python application
* Creating a practical productivity tool

---

## 💡 Why This Project?

Writing continuously can be difficult when constantly editing or overthinking every sentence.

This application creates a simple challenge:

> **Keep typing or lose everything.**

It demonstrates how a relatively small Python program can combine GUI development, event handling, and timed actions to create an engaging productivity application.

---

## 🔮 Future Improvements

Potential improvements include:

* ⏱️ Custom timer settings
* 📊 Writing session statistics
* 💾 Optional document saving
* 🌙 Dark mode
* 🎨 Multiple themes
* ⌨️ Keyboard shortcuts
* 📈 Words-per-minute tracking
* 🏆 Writing streak system
* 🔊 Countdown notifications
* ⚙️ User preferences

---

## 📚 100 Days of Python

### Day 90 / 100 — Completed ✅

This project is part of my journey through **Angela Yu's 100 Days of Code: The Complete Python Pro Bootcamp**.

Day 90 focused on building a practical **Disappearing Text Writing App** while strengthening my understanding of **Tkinter, timers, events, and GUI programming**.

---

## 👩‍💻 Author

**Fatima Ch**

### 100 Days of Python 🐍

**Day 90/100 — Learn • Build • Improve 🚀**

---

## 📌 Project Status

**Completed ✅**

A functional Python desktop application featuring:

* Continuous writing
* Automatic inactivity detection
* Disappearing text
* Live word count
* Timer management
* Tkinter GUI
* Keyboard event handling
