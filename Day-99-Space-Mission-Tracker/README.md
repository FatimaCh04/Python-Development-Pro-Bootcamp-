# 🚀 Day 99 — Space Mission Tracker

A professional **Space Mission Tracker** web application built with **Python, Flask, SQLite, and SQLAlchemy** as part of my **100 Days of Python** journey.

The application provides a centralized dashboard for managing and exploring space missions. Users can search missions, filter them by status, view detailed mission information, add new missions, and remove existing records.

---

## ✨ Features

* 🚀 Space mission dashboard
* 🔎 Search missions by name, agency, or destination
* 🏷️ Filter missions by status
* 📊 Mission statistics dashboard
* 🌍 Destination tracking
* 📅 Launch date management
* ➕ Add new missions
* 🗑️ Delete missions
* 📄 Detailed mission information page
* 💾 SQLite database integration
* 🧩 SQLAlchemy ORM
* 📱 Responsive design
* ✨ Clean and modern user interface

---

## 🛠️ Technologies Used

| Technology       | Purpose                 |
| ---------------- | ----------------------- |
| Python           | Application logic       |
| Flask            | Web framework           |
| Flask-SQLAlchemy | Database integration    |
| SQLite           | Data storage            |
| Jinja2           | HTML templating         |
| HTML5            | Page structure          |
| CSS3             | Responsive styling      |
| JavaScript       | Interactive UI behavior |

---

## 📂 Project Structure

```text
Day-99-Space-Mission-Tracker/
│
├── app.py
├── models.py
├── seed.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── index.html
│   └── mission.html
│
└── static/
    ├── style.css
    └── script.js
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
```

Navigate into the project:

```bash
cd Day-99-Space-Mission-Tracker
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows CMD:**

```cmd
venv\Scripts\activate.bat
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Add sample mission data

```bash
python seed.py
```

### 6. Run the application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## 🗄️ Database

The project uses **SQLite** for lightweight and reliable local data storage.

The `Mission` model stores:

* Mission name
* Space agency
* Destination
* Launch date
* Mission status
* Mission description

The database is automatically created when the Flask application starts.

---

## 🔍 Search & Filtering

The dashboard supports:

* Searching by mission name
* Searching by space agency
* Searching by destination
* Filtering by **Completed**
* Filtering by **Active**
* Filtering by **Upcoming**

This makes it easy to quickly locate specific missions.

---

## 📊 Dashboard

The dashboard provides an overview of the mission database, including:

* Total missions
* Completed missions
* Active missions
* Upcoming missions

This gives users a quick understanding of the current mission database.

---

## 🎯 Learning Objectives

Through this project, I practiced:

* Flask application development
* URL routing
* HTML templating with Jinja2
* CRUD operations
* SQLAlchemy ORM
* SQLite database management
* HTML forms
* GET and POST requests
* Search and filtering
* Responsive web design
* JavaScript DOM manipulation
* Organizing a Python web project

---

## 🚀 Future Improvements

Possible future enhancements include:

* User authentication
* Mission editing functionality
* Pagination
* Mission images
* Real-time space mission APIs
* Advanced analytics
* Interactive charts
* REST API
* Deployment to a cloud platform

---

## 👩‍💻 100 Days of Python

**Day 99** of my Python development journey.

This project represents another step toward building practical Python applications and strengthening my understanding of full-stack development with Flask.

---

## 📜 License

This project is created for educational and learning purposes.
