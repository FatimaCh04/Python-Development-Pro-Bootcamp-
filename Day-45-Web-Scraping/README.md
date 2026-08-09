# 🐍 Day 45 - Web Scraping with Beautiful Soup

## 100 Days of Python - Angela Yu

This is my Day 45 project from Angela Yu's
100 Days of Code: The Complete Python Pro Bootcamp.

## 🎯 Project

100 Movies You Must Watch - Web Scraping Project.

## 📚 Topics Covered

- Web Scraping
- HTTP Requests
- Requests Library
- BeautifulSoup
- HTML Parsing
- `find()`
- `find_all()`
- `get_text()`
- HTML Attributes
- Selecting Elements
- Saving Scraped Data
- Writing to Text Files

## ✨ Features

- Sends a request to a website
- Downloads HTML
- Parses HTML using BeautifulSoup
- Finds movie titles
- Removes duplicates
- Saves movie titles into a text file

## 🛠 Technologies

- Python
- Requests
- BeautifulSoup4

## 📁 Project Structure

```text
Day-45-Web-Scraping/
│
├── main.py
├── practice.py
├── requirements.txt
├── README.md
└── movies.txt
```

## 📦 Installation

Install the required packages:

```bash
pip install -r requirements.txt
```

## ▶️ Run

```bash
python main.py
```

The program will scrape movie titles and save
them into:

```text
movies.txt
```

## 🧠 BeautifulSoup Examples

Find one element:

```python
soup.find("h1")
```

Find multiple elements:

```python
soup.find_all("h2")
```

Get text:

```python
element.get_text()
```

Get an attribute:

```python
element.get("href")
```

## 📖 Learning Outcomes

Through Day 45 I learned how to:

- Make HTTP requests
- Download HTML from a website
- Parse HTML using BeautifulSoup
- Find specific HTML elements
- Extract text from HTML
- Extract attributes
- Scrape useful information
- Save scraped information to a file

