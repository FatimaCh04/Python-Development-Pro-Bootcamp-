# 🐍 Day 77 - Habit Tracker

## 📊 Habit Tracking with Pixela API

This project is part of **Day 77** of Angela Yu's **100 Days of Code: The Complete Python Pro Bootcamp**.

In this project, I built a **Habit Tracker** using the **Pixela API**.

The application allows me to track a daily habit by sending data to an online graph through API requests.

For this project, the tracked habit can be coding hours.

---

## 🎯 Project Goal

The main goal of this project is to learn how Python applications communicate with external web services through APIs.

Instead of storing the habit data only inside the Python program, the application sends the data to the Pixela API and stores it online.

---

## 🧠 What I Learned

During this project, I practiced:

- Working with APIs
- Sending HTTP requests
- Using the `requests` library
- POST requests
- PUT requests
- DELETE requests
- API endpoints
- HTTP headers
- JSON data
- API authentication
- Working with dates
- Formatting dates using `strftime()`
- Sending data to an external service

---

## 🔌 HTTP Requests Used

### POST

POST requests are used to create resources and add new data.

Examples:

- Creating a Pixela user
- Creating a graph
- Adding a daily pixel

```python
requests.post(
    url=pixel_endpoint,
    json=pixel_data,
    headers=headers
)