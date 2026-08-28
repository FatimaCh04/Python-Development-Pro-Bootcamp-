# 🌦️ Day 84 — Weather Dashboard

A modern and responsive **Weather Dashboard** built with **Python, Flask, and the OpenWeatherMap API**. The application allows users to search for any city and retrieve real-time weather information through an intuitive web interface.

---

## 📌 Project Overview

The **Weather Dashboard** demonstrates how a Python web application can communicate with an external REST API, process JSON responses, and dynamically display useful information to users.

Users can enter a city name and receive current weather conditions, including temperature, humidity, wind speed, atmospheric pressure, sunrise, and sunset.

The project also includes proper API error handling and secure environment-variable management for the API key.

---

## ✨ Features

* 🌍 Search weather by city
* 🌡️ Display current temperature
* 🥵 Show "feels like" temperature
* 🌤️ Display current weather condition
* 💧 Show humidity
* 💨 Display wind speed
* 📊 Show atmospheric pressure
* 🌅 Display sunrise time
* 🌇 Display sunset time
* 🖼️ Dynamic weather icons
* ⚠️ Handle invalid city names
* 🔐 Secure API key using environment variables
* 📱 Responsive and mobile-friendly interface

---

## 🛠️ Technologies Used

| Technology             | Purpose                         |
| ---------------------- | ------------------------------- |
| **Python**             | Core programming language       |
| **Flask**              | Web application framework       |
| **Requests**           | API communication               |
| **python-dotenv**      | Environment variable management |
| **OpenWeatherMap API** | Real-time weather data          |
| **HTML5**              | Page structure                  |
| **CSS3**               | Custom styling                  |
| **Bootstrap 5**        | Responsive components           |
| **Jinja2**             | Dynamic template rendering      |

---

## 🗂️ Project Structure

```text
Day84-Weather-Dashboard/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── static/
│   └── css/
│       └── styles.css
│
└── templates/
    ├── base.html
    └── index.html
```

---

## 🔌 API Integration

The application uses the **OpenWeatherMap REST API** to retrieve weather information.

### API Workflow

```text
User enters city
       ↓
Flask receives request
       ↓
Python sends API request
       ↓
OpenWeatherMap returns JSON
       ↓
Python processes response
       ↓
Jinja2 renders weather data
       ↓
Weather Dashboard
```

---

## 📊 Weather Information

For a valid city, the application displays:

* **City & Country**
* **Current Temperature**
* **Feels Like Temperature**
* **Weather Description**
* **Weather Icon**
* **Humidity**
* **Wind Speed**
* **Atmospheric Pressure**
* **Sunrise**
* **Sunset**

---

## 🔐 Environment Variables

The API key is not hard-coded into the application.

Create a `.env` file in the root directory:

```env
OPENWEATHER_API_KEY=your_api_key_here
```

The application loads the key using `python-dotenv`.

### ⚠️ Security

Never commit your `.env` file or API key to GitHub.

The project includes `.gitignore` to prevent accidental exposure:

```text
.env
__pycache__/
*.pyc
.venv/
venv/
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day84-Weather-Dashboard
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

### 6. Configure the API Key

Create a `.env` file:

```env
OPENWEATHER_API_KEY=your_api_key_here
```

### 7. Run the Application

```bash
python app.py
```

### 8. Open in Browser

```text
http://127.0.0.1:5000
```

---

## ⚠️ Error Handling

The application handles common API-related errors, including:

* Empty city input
* Invalid city names
* Invalid API keys
* API connection failures
* Request timeouts
* Unexpected API errors

Users receive a clear message instead of seeing a technical error page.

---

## 🎯 Learning Objectives

This project strengthened my understanding of:

* Python web development with Flask
* REST API integration
* HTTP requests
* JSON data processing
* API response handling
* Environment variables
* API key security
* Error handling
* Jinja2 template rendering
* Bootstrap responsive design
* Dynamic web interfaces

---

## 🚀 Future Enhancements

Future versions could include:

* 📅 5-day weather forecast
* 📍 Automatic location detection
* 🌎 Multiple city comparison
* 🌡️ Celsius/Fahrenheit toggle
* 🌙 Dynamic light/dark themes
* 📈 Temperature charts
* ⭐ Favorite cities
* 🔔 Weather alerts
* 🗺️ Interactive maps
* 📱 Progressive Web App support

---

## 📚 100 Days of Python

**Day 84 of 100 Days of Python 🐍**

This project marks another milestone in my Python development journey. It introduced practical **REST API integration**, allowing a Flask application to retrieve, process, and display real-time external data.

---

## 👩‍💻 Author

**Fatima Ch**

### Project Status

**Completed — Day 84/100 ✅**

---

⭐ **If you find this project useful, consider giving the repository a star!**
