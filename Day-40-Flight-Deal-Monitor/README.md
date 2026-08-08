# ✈️ Day 40 - Automated Flight Deal Monitor

## 📚 Course

100 Days of Python - Day 40 Practice

## 🎯 Topics Covered

- REST APIs
- API Authentication
- HTTP GET Requests
- Query Parameters
- JSON Data
- Environment Variables
- API Error Handling
- Automation Concepts
- Modular Python Programming

## ✨ Features

- Search flights between two airports
- Retrieve flight information from an API
- Display airline information
- Display flight numbers
- Display departure and arrival times
- Display flight status
- Configurable origin and destination
- Configurable target price
- Handle API and network errors

## 🛠 Technologies

- Python 3
- Requests
- REST API
- JSON
- python-dotenv

## 📦 Installation

Install the required packages:

```bash
pip install requests python-dotenv
```

## ⚙️ Configuration

Create a `.env` file:

```env
API_KEY=your_api_key_here
ORIGIN=LHE
DESTINATION=DXB
MAX_PRICE=300
```

Never upload `.env` to GitHub.

## ▶️ Run

```bash
python main.py
```

## 📖 Learning Outcomes

After completing this project, I practiced:

- Working with REST APIs
- Sending authenticated GET requests
- Using query parameters
- Processing JSON responses
- Managing environment variables
- Handling API errors
- Separating configuration from application logic
- Building automation-ready Python programs

## ⚠️ API Note

The project uses flight availability data. The basic Aviationstack
flight endpoint does not provide actual ticket prices, so the price
monitoring portion is structured as an extension point.

For real price alerts, a flight-pricing API should be connected.