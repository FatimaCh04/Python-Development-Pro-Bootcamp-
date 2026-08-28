# 🎬 Day 93 — Top 100 Movies Web Scraper

A Python-based **Web Scraping project** built as part of Angela Yu's **100 Days of Code: The Complete Python Pro Bootcamp**.

This project uses **Requests** and **BeautifulSoup** to retrieve a webpage, parse its HTML structure, extract movie titles, and save the results into a text file.

---

## 🚀 Project Overview

The application connects to a movie-ranking webpage and extracts the available movie titles automatically.

Instead of manually collecting movie names, Python performs the task through web scraping.

### Workflow

```text
Website
   ↓
HTTP Request
   ↓
Download HTML
   ↓
BeautifulSoup Parsing
   ↓
Find Movie Titles
   ↓
Clean & Organize Data
   ↓
Save to movies.txt
```

---

## ✨ Features

* 🌐 Fetches webpage content using Requests
* 🥣 Parses HTML using BeautifulSoup
* 🎬 Extracts movie titles
* 🔢 Numbers the extracted movies
* 🧹 Removes duplicate titles
* 💾 Saves results to `movies.txt`
* ⚠️ Includes request error handling
* 🖥️ Displays scraped results in the terminal

---

## 🛠️ Technologies Used

| Technology    | Purpose                         |
| ------------- | ------------------------------- |
| Python        | Core programming language       |
| Requests      | Download webpage content        |
| BeautifulSoup | Parse and extract HTML data     |
| HTML          | Source structure being analyzed |

---

## 📂 Project Structure

```text
Day-93-Web-Scraping-Movies/
│
├── main.py
├── requirements.txt
├── README.md
└── movies.txt
```

`movies.txt` is generated automatically when the program runs.

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day-93-Web-Scraping-Movies
```

### 3. Create a Virtual Environment

Windows:

```powershell
python -m venv venv
```

### 4. Activate the Environment

```powershell
venv\Scripts\activate
```

### 5. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## ▶️ Run the Project

```powershell
python main.py
```

The program will:

1. Connect to the target webpage.
2. Download the HTML.
3. Parse the HTML using BeautifulSoup.
4. Extract movie titles.
5. Display the results.
6. Save them to `movies.txt`.

---

## 📄 Output

After running the program, a `movies.txt` file is generated.

Example:

```text
1. The Shawshank Redemption
2. The Godfather
3. The Dark Knight
4. Pulp Fiction
5. The Lord of the Rings
```

The exact results depend on the current HTML structure and content of the target webpage.

---

## 🧠 Key Concepts Learned

This project strengthened my understanding of:

* Web scraping
* HTTP requests
* HTML parsing
* BeautifulSoup
* HTML tags
* Finding elements
* Extracting text
* Python file handling
* Lists and loops
* Exception handling
* Working with external web data

---

## 🔍 Core Code Concepts

### Sending a Request

```python
response = requests.get(URL, headers=headers)
```

### Creating a BeautifulSoup Object

```python
soup = BeautifulSoup(
    response.text,
    "html.parser"
)
```

### Finding HTML Elements

```python
headings = soup.find_all("h2")
```

### Extracting Text

```python
title = heading.get_text(strip=True)
```

### Saving Results

```python
with open("movies.txt", "w", encoding="utf-8") as file:
    for movie in movie_titles:
        file.write(f"{movie}\n")
```

---

## 🛡️ Error Handling

The application handles common connection problems using exception handling:

```python
try:
    response = requests.get(
        URL,
        headers=headers,
        timeout=15
    )
    response.raise_for_status()

except requests.RequestException as error:
    print(f"Error: {error}")
```

This prevents the application from crashing when the webpage cannot be reached.

---

## 🔮 Future Improvements

Possible improvements include:

* Exporting data to CSV
* Exporting data to JSON
* Scraping additional movie information
* Extracting ratings and release years
* Adding a graphical interface
* Storing results in a database
* Scheduling automatic scraping

---

## 📚 100 Days of Python

**Day 93 / 100 ✅**

This project focuses on **Web Scraping with Python**, introducing practical techniques for collecting and processing information from websites.

---

## 👩‍💻 Author

**Fatima Ch**

**100 Days of Python — Day 93/100**

> Learn • Build • Practice • Improve 🚀

---

## 📌 Project Status

**Completed ✅**
