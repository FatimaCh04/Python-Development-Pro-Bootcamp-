# 📁 Day 86 — File Organizer

A Python-based **File Organizer Automation Tool** that automatically sorts files into categorized folders based on their file extensions.

This project demonstrates how Python's standard library can be used to automate everyday file-management tasks efficiently and safely.

---

## 🚀 Project Overview

Managing a folder containing hundreds of files can quickly become difficult. The **File Organizer** solves this problem by scanning a selected directory and automatically moving files into appropriate categories such as **Images, Documents, Videos, Audio, Code, Archives, and Others**.

The application provides a simple command-line interface with preview, statistics, folder selection, and organization features.

---

## ✨ Features

* 📂 Organize files automatically
* 🖼️ Detect image files
* 📄 Detect documents
* 📊 Detect spreadsheets
* 🎬 Detect videos
* 🎵 Detect audio files
* 💻 Detect programming files
* 📦 Detect archive files
* 📋 Preview files before organizing
* 📊 Display file statistics
* 🔄 Change the target folder
* 🛡️ Prevent files from being overwritten
* ⚠️ Handle invalid folders and file errors
* 🧹 Automatically create required category folders
* 🚫 Skip the organizer script itself

---

## 🛠️ Technologies Used

| Technology   | Purpose                             |
| ------------ | ----------------------------------- |
| **Python**   | Core programming language           |
| **pathlib**  | File and directory handling         |
| **shutil**   | Moving files                        |
| **os**       | Directory and filesystem operations |
| **datetime** | Session timing                      |

The project uses only Python's **built-in standard library**, so no third-party packages are required.

---

## 📁 Project Structure

```text
Day-86-File-Organizer/
│
├── file_organizer.py
├── requirements.txt
└── README.md
```

When the program organizes a folder, it automatically creates category directories:

```text
Selected Folder/
│
├── Images/
├── Documents/
├── Spreadsheets/
├── Presentations/
├── Videos/
├── Audio/
├── Archives/
├── Programs/
├── Code/
└── Others/
```

---

## 🧩 Supported File Categories

### 🖼️ Images

```text
.jpg
.jpeg
.png
.gif
.bmp
.webp
.svg
.ico
```

### 📄 Documents

```text
.pdf
.doc
.docx
.txt
.rtf
.odt
```

### 📊 Spreadsheets

```text
.xls
.xlsx
.csv
.ods
```

### 📽️ Presentations

```text
.ppt
.pptx
.odp
```

### 🎬 Videos

```text
.mp4
.mkv
.avi
.mov
.wmv
.flv
.webm
```

### 🎵 Audio

```text
.mp3
.wav
.aac
.flac
.ogg
.m4a
```

### 📦 Archives

```text
.zip
.rar
.7z
.tar
.gz
```

### 💻 Programming & Code

```text
.py
.js
.html
.css
.java
.cpp
.c
.cs
.php
.sql
.json
.xml
```

---

## ⚙️ How It Works

The application follows a simple automation workflow:

```text
Select Folder
      ↓
Scan Files
      ↓
Read File Extension
      ↓
Identify Category
      ↓
Create Category Folder
      ↓
Move File
      ↓
Display Result
```

For example:

```text
photo.jpg       → Images/
resume.pdf      → Documents/
movie.mp4       → Videos/
song.mp3        → Audio/
project.zip     → Archives/
app.py          → Code/
unknown.xyz     → Others/
```

---

## ▶️ Installation

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day-86-File-Organizer
```

### 3. Run the Application

No package installation is required.

```bash
python file_organizer.py
```

---

## 🖥️ Using the Application

After starting the application, enter the folder you want to organize:

```text
=======================================================
             📁 FILE ORGANIZER
=======================================================
             Day 86 — Python
=======================================================

Enter the folder path to organize:
> C:\Users\Admin\Desktop\TestFiles
```

The application then displays the main menu:

```text
-------------------------------------------------------
MENU
-------------------------------------------------------
1. Preview files
2. Show statistics
3. Organize files
4. Change folder
5. Exit
```

### Option 1 — Preview Files

Shows how files will be categorized **without moving them**.

### Option 2 — Show Statistics

Displays the number of files found in each category.

### Option 3 — Organize Files

Moves files into their appropriate category folders.

### Option 4 — Change Folder

Allows you to select another directory.

### Option 5 — Exit

Closes the application safely.

---

## 🛡️ File Safety

The application includes several safety mechanisms:

* Existing files are not overwritten.
* Duplicate filenames receive a numbered suffix.
* Invalid folder paths are rejected.
* Permission errors are handled.
* The organizer script itself is skipped.
* Users are asked for confirmation before organization begins.

Example:

```text
photo.jpg
photo_1.jpg
photo_2.jpg
```

This prevents accidental file replacement.

---

## 🧪 Testing

For safe testing, create a temporary folder such as:

```text
C:\Users\Admin\Desktop\TestFiles
```

Place copies of different file types inside it:

```text
TestFiles/
├── photo.jpg
├── resume.pdf
├── notes.txt
├── budget.csv
├── movie.mp4
├── song.mp3
├── project.zip
└── app.py
```

Run:

```bash
python file_organizer.py
```

Then select:

```text
1. Preview files
```

to verify the categories before selecting:

```text
3. Organize files
```

---

## 🧠 Key Python Concepts Practiced

This project strengthened my understanding of:

* Python functions
* Dictionaries
* Lists
* Loops
* Conditional statements
* Exception handling
* File handling
* Directory management
* `pathlib`
* `shutil`
* File extensions
* String manipulation
* User input
* Command-line interfaces
* Automation with Python

---

## 🎯 Learning Outcomes

Through this project, I learned how to use Python to automate a real-world repetitive task.

The project demonstrates how:

```text
Python
  +
File System Operations
  +
Automation Logic
  =
Useful Productivity Tool
```

Instead of manually sorting files, the program performs the task automatically based on file types.

---

## 🔮 Future Improvements

Possible future enhancements include:

* 🖥️ Graphical User Interface using Tkinter
* 📅 Organize files by date
* 🔍 Duplicate file detection
* ↩️ Undo organization
* 📜 Activity/log history
* ⚙️ Custom category configuration
* 🗂️ Recursive subfolder organization
* 📊 Visual organization statistics
* 🖱️ Drag-and-drop folder selection

---

## 🐍 100 Days of Python

### Day 86 / 100 — Completed ✅

This project is part of my **100 Days of Python** journey.

Day 86 focused on applying Python's standard library to build a practical **file-management automation tool**.

---

## 👩‍💻 Author

**Fatima Ch**

---

## 📌 Project Status

**Completed — Day 86/100 🚀**

Continuing to learn, build, automate, and improve with Python — one project at a time. 🐍💻

---

⭐ If you find this project useful, consider giving the repository a star!
