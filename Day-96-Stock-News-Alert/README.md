# 🚀 Day 94 — Space Invaders

A classic **Space Invaders-style arcade game** developed in Python using **Pygame** as part of Angela Yu's **100 Days of Code: The Complete Python Pro Bootcamp**.

The project demonstrates object-oriented programming, game loops, keyboard controls, collision detection, enemy movement, shooting mechanics, scoring, lives, levels, and game-state management.

---

## 🎮 Project Overview

The player controls a spaceship at the bottom of the screen and must destroy waves of incoming enemies before they reach the player's position.

Each destroyed enemy increases the score. Once an entire wave has been cleared, a new level begins with more challenging gameplay.

---

## ✨ Features

* 🚀 Player spaceship
* 👾 Multiple enemy formations
* 🔫 Player shooting
* 💥 Bullet collision detection
* 👾 Enemy shooting
* ❤️ Three-player-life system
* 🏆 Score tracking
* 📈 Level progression
* ⏸️ Pause functionality
* 🔄 Restart after Game Over
* ⭐ Increasing difficulty
* 🌌 Space-themed background
* ⌨️ Keyboard controls
* 🖥️ 60 FPS gameplay

---

## 🛠️ Technologies Used

| Technology     | Purpose                    |
| -------------- | -------------------------- |
| Python         | Core programming language  |
| Pygame         | Game development framework |
| OOP            | Game objects and structure |
| Rect Collision | Collision detection        |

---

## 📂 Project Structure

```text
Day-94-Space-Invaders/
│
├── main.py
├── game.py
├── player.py
├── enemy.py
├── bullet.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### 1. Create a Virtual Environment

Windows:

```powershell
python -m venv venv
```

### 2. Activate the Environment

```powershell
venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## ▶️ Run the Game

```powershell
python main.py
```

The game window will open automatically.

---

## 🎮 Controls

| Key   | Action                  |
| ----- | ----------------------- |
| ←     | Move left               |
| →     | Move right              |
| Space | Shoot                   |
| P     | Pause / Resume          |
| R     | Restart after Game Over |
| ESC   | Exit                    |

---

## 🧠 Game Mechanics

### Player Movement

The player can move horizontally using the left and right arrow keys.

The spaceship is restricted to the game window so it cannot move outside the screen.

### Shooting

Pressing **Space** launches a bullet from the player's spaceship.

The game limits the number of active bullets to keep gameplay balanced.

### Enemy Movement

Enemies move horizontally across the screen.

When they reach an edge, they reverse direction and move downward.

### Collision Detection

Pygame rectangles are used to detect collisions between bullets and enemies:

```python
if bullet.rect.colliderect(enemy.rect):
    ...
```

When a bullet hits an enemy:

* The enemy is removed.
* The bullet is removed.
* The player's score increases.

### Lives

The player starts with:

```text
❤️ 3 Lives
```

When an enemy bullet hits the player, one life is lost.

The game ends when all lives are lost.

### Levels

After all enemies are destroyed, the next level begins.

The game increases the enemy difficulty as the level increases.

---

## 🧱 Object-Oriented Design

The project is divided into separate classes.

### `Player`

Responsible for:

* Player position
* Player movement
* Player lives
* Player rendering

### `Enemy`

Responsible for:

* Enemy position
* Enemy movement
* Enemy rendering

### `Bullet`

Responsible for:

* Bullet position
* Bullet movement
* Bullet rendering
* Screen-bound checking

### `Game`

Responsible for:

* Game loop
* Event handling
* Collision detection
* Score
* Levels
* Game states
* Rendering

---

## 📚 Learning Objectives

This project helped strengthen my understanding of:

* Python classes
* Object-oriented programming
* Constructors
* Methods
* Objects
* Pygame
* Game loops
* Keyboard events
* Collision detection
* Rectangles
* Lists of objects
* Random number generation
* Game states
* Timers
* Score systems
* Level progression
* Modular Python development

---

## 🔄 Game Flow

```text
Start Game
    ↓
Create Player
    ↓
Create Enemy Formation
    ↓
Start Game Loop
    ↓
Read Keyboard Input
    ↓
Move Player
    ↓
Fire Bullets
    ↓
Move Enemies
    ↓
Move Bullets
    ↓
Check Collisions
    ↓
Update Score / Lives
    ↓
Enemies Destroyed?
   ↙       ↘
 YES       NO
 ↓          ↓
New Level   Continue
 ↓
Game Over?
 ↓
Restart / Exit
```

---

## 🚀 Future Improvements

Possible future enhancements include:

* 🔊 Sound effects
* 🎵 Background music
* 🏅 High-score system
* 👾 Different enemy types
* 🛡️ Player shields
* 💥 Explosion animations
* ❤️ More advanced health system
* 🌟 Power-ups
* 🎯 Boss enemies
* 🥇 Persistent leaderboard
* 🎨 Sprite-based graphics

---

## 📌 Project Status

**Completed ✅**

The project is fully playable locally and requires only Python and Pygame.

---

## 📚 100 Days of Python

**Day 94 / 100 ✅**

This project is part of my ongoing **100 Days of Python** journey and focuses on game development and object-oriented programming with Pygame.

---

## 👩‍💻 Author

**Fatima Ch**

**100 Days of Python — Day 94/100**

> Learn • Build • Practice • Improve 🚀
