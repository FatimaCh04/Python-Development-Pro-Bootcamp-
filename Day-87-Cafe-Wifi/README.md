# ☕ Day 87 — Café & WiFi Website

A full-featured **Café & WiFi Directory Web Application** built with **Python and Flask**.

The application allows users to discover cafés based on important work-friendly features such as **coffee quality, WiFi strength, power availability, seating capacity, opening hours, and price**. It also provides functionality to add and remove cafés using a CSV-based data store.

This project is part of my **100 Days of Python** journey and focuses on building practical web applications with Flask.

---

## 🚀 Project Overview

Finding a suitable café for studying, working, or relaxing often requires knowing more than just its name and location.

The **Café & WiFi Website** provides a centralized directory where users can explore cafés and quickly compare their facilities.

Each café includes information such as:

* ☕ Coffee rating
* 📶 WiFi strength
* 🔌 Power socket availability
* 💺 Seating capacity
* 🕐 Opening and closing times
* 💰 Coffee price
* 📍 Location/map link

The application uses **Flask for the web server** and **CSV for lightweight data storage**.

---

## ✨ Features

### ☕ Café Directory

Browse a collection of cafés with useful information for students, developers, remote workers, and coffee lovers.

### 📶 WiFi Information

View WiFi strength for each café to identify suitable locations for working or studying.

### 🔌 Power Availability

Check the availability of power outlets before visiting.

### 💺 Seating Information

View the approximate seating capacity of each café.

### 🕐 Opening Hours

Display café opening and closing times.

### 💰 Price Information

View the approximate price of coffee.

### 📍 Map Integration

Each café can include a Google Maps URL for easy location access.

### ➕ Add New Café

Users can submit a new café through a dedicated form.

### 🗑️ Delete Café

Cafés can be removed from the directory when required.

### 💾 CSV Data Storage

Café information is stored in a simple CSV file, making the application easy to understand and manage.

### 📱 Responsive Design

The interface is designed to work across desktop, tablet, and mobile screens.

---

## 🛠️ Technologies Used

| Technology      | Purpose                   |
| --------------- | ------------------------- |
| **Python**      | Core programming language |
| **Flask**       | Web application framework |
| **CSV**         | Data storage              |
| **Jinja2**      | Dynamic HTML templates    |
| **HTML5**       | Page structure            |
| **CSS3**        | Custom styling            |
| **Bootstrap 5** | Responsive components     |

---

## 🏗️ Application Architecture

```text
                    User
                     │
                     ▼
              Flask Web App
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
      Jinja2 Templates       Flask Routes
          │                     │
          │                     ▼
          │                CSV Data
          │                     │
          └──────────┬──────────┘
                     ▼
               Web Interface
```

---

## 📁 Project Structure

```text
Day-87-Cafe-Wifi/
│
├── main.py
├── cafe-data.csv
├── requirements.txt
│
├── static/
│   └── css/
│       └── styles.css
│
└── templates/
    ├── base.html
    ├── index.html
    ├── cafes.html
    └── add.html
```

---

## 📊 Café Data

The application stores café information using the following fields:

| Field       | Description                  |
| ----------- | ---------------------------- |
| `Cafe Name` | Name of the café             |
| `Location`  | City/location                |
| `Open`      | Opening time                 |
| `Close`     | Closing time                 |
| `Coffee`    | Coffee quality rating        |
| `Wifi`      | WiFi strength rating         |
| `Power`     | Power availability           |
| `Seats`     | Approximate seating capacity |
| `Price`     | Coffee price                 |
| `Map URL`   | Google Maps location         |

---

## 🔄 Application Workflow

```text
User Visits Website
        ↓
Flask Receives Request
        ↓
Read Café Data
        ↓
CSV File
        ↓
Process Data
        ↓
Jinja2 Template
        ↓
Render Web Page
```

### Adding a Café

```text
Add Café Form
      ↓
POST Request
      ↓
Flask
      ↓
Validate Form Data
      ↓
Write to CSV
      ↓
Redirect to Café Directory
```

---

## 🌐 Application Pages

### 🏠 Home

Provides an introduction to the platform and highlights featured cafés.

### ☕ Cafés

Displays the complete café directory in a structured table.

### ➕ Add Café

Provides a form for adding a new café to the directory.

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day-87-Cafe-Wifi
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

Start the Flask development server:

```bash
python main.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

## 🧪 Testing the Application

After launching the application, test the following:

### Test 1 — View Cafés

Open:

```text
/cafes
```

Verify that the café records are displayed correctly.

### Test 2 — Add Café

Open:

```text
/add
```

Complete the form and submit it.

The new café should appear in the directory and be saved to:

```text
cafe-data.csv
```

### Test 3 — Delete Café

Click the **Delete** button for a café and verify that the record is removed from the CSV file.

### Test 4 — Map

Click the **Map** button and verify that the provided location link opens correctly.

---

## 🧠 Key Concepts Practiced

This project strengthened my understanding of:

* Flask application structure
* Flask routing
* GET and POST requests
* HTML forms
* Jinja2 templating
* Template inheritance
* CSV file handling
* Python dictionaries
* CRUD-style operations
* Form data processing
* HTTP redirects
* URL generation with `url_for()`
* Static files
* Responsive web design

---

## 🎯 Learning Outcomes

Through this project, I learned how to build a complete Flask application that connects:

```text
Frontend
   ↓
HTML Forms
   ↓
Flask Routes
   ↓
Python Logic
   ↓
CSV Storage
   ↓
Dynamic Web Pages
```

The project demonstrates how Python can be used to create practical web applications rather than standalone scripts.

---

## 🔐 Data Handling

The application uses a CSV file as a lightweight data source.

This approach is useful for learning and small projects because it requires no database server or external database configuration.

For a production application, the CSV storage could later be replaced with:

* SQLite
* PostgreSQL
* MySQL
* MongoDB

---

## 🔮 Future Improvements

Possible future enhancements include:

* 🔎 Café search functionality
* 📍 Location-based filtering
* ⭐ User reviews and ratings
* ❤️ Favorite cafés
* 🔐 User authentication
* 🗄️ Database integration
* 📷 Café images
* 🗺️ Interactive maps
* 📱 Progressive Web App support
* 🌙 Dark mode
* 📊 Café comparison
* 🔍 Advanced filtering by WiFi, power, seats, and price

---

## 📚 What I Learned

The most important takeaway from this project was understanding how different components of a web application work together:

```text
Python
  +
Flask
  +
Jinja2
  +
HTML/CSS
  +
CSV
  =
Complete Web Application
```

It was a valuable step toward developing more advanced **Python web applications and backend systems**.

---

## 🐍 100 Days of Python

### Day 87 / 100 — Completed ✅

This project is part of my **100 Days of Python** journey.

Day 87 focused on building a practical **Flask-based Café & WiFi Directory**, working with forms, templates, routes, and CSV data storage.

---

## 👩‍💻 Author

**Fatima Ch**

---

## 📌 Project Status

**Completed — Day 87/100 🚀**

Continuing the journey of learning, building, and improving one Python project at a time.

---

⭐ **If you find this project useful, consider giving the repository a star!**
