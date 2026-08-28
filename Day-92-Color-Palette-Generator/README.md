# 🎨 Day 92 — Image Colour Palette Generator

A web-based **Image Colour Palette Generator** built with **Python, Flask, and Pillow** as part of Angela Yu's **100 Days of Code: The Complete Python Pro Bootcamp**.

The application allows users to upload an image and automatically extract its dominant colours. The generated palette displays both **HEX** and **RGB** values and allows users to copy HEX colours directly.

---

## 🚀 Project Overview

Choosing colours from an image manually can be time-consuming. This project automates that process by analyzing image pixels and identifying the most frequently occurring colours.

### Workflow

```text
Upload Image
     ↓
Read Image
     ↓
Analyze Pixels
     ↓
Count Colour Frequency
     ↓
Extract Dominant Colours
     ↓
Generate Palette
     ↓
Display HEX & RGB Values
```

---

## ✨ Features

* 🖼️ Upload an image
* 🎨 Automatically extract dominant colours
* 🔢 Generate a 10-colour palette
* HEX colour values
* RGB colour values
* 🖱️ Click a colour to copy its HEX code
* 📱 Responsive interface
* 🚨 Upload validation
* ⚠️ Error handling
* ⚡ Fast image processing
* 💻 Clean and modern web interface

---

## 🛠️ Technologies Used

| Technology | Purpose                       |
| ---------- | ----------------------------- |
| Python     | Application logic             |
| Flask      | Web framework                 |
| Pillow     | Image processing              |
| HTML5      | Page structure                |
| CSS3       | Styling and responsive design |
| JavaScript | HEX colour copying            |

---

## 📂 Project Structure

```text
Day-92-Image-Colour-Palette-Generator/
│
├── main.py
├── requirements.txt
├── README.md
│
├── templates/
│   └── index.html
│
├── static/
│   └── style.css
│
└── uploads/
```

The `uploads` folder is automatically created when the application starts.

Uploaded images are not required inside the GitHub repository.

---

## ⚙️ Requirements

* Python 3.10 or newer
* Flask
* Pillow

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Open the Project

```bash
cd Day-92-Image-Colour-Palette-Generator
```

### 3. Create a Virtual Environment

Windows:

```powershell
python -m venv venv
```

### 4. Activate the Virtual Environment

```powershell
venv\Scripts\activate
```

### 5. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```powershell
python main.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## 🧪 How to Use

### Step 1

Click **Choose Image**.

### Step 2

Select a JPG, JPEG, PNG, WEBP, or BMP image.

### Step 3

Click **Generate Palette**.

### Step 4

The application analyzes the image and displays its dominant colours.

### Step 5

Click any colour card to copy its HEX value.

---

## 🧠 How Colour Extraction Works

The application uses Pillow to open and process the uploaded image.

The image is converted to RGB:

```python
image = Image.open(image_path).convert("RGB")
```

The image pixels are then collected:

```python
pixels = list(image.getdata())
```

Python's `Counter` is used to count how frequently each RGB colour occurs:

```python
color_counts = Counter(pixels)
```

The most common colours are extracted:

```python
most_common = color_counts.most_common(10)
```

Finally, the RGB values are converted into HEX values for use in websites and design tools.

---

## 🎯 Learning Objectives

This project helped strengthen my understanding of:

* Flask routing
* HTML templates
* Jinja2 template rendering
* File uploads
* Flask request handling
* Static files
* Pillow image processing
* RGB colour values
* HEX colour conversion
* Python `Counter`
* Lists and dictionaries
* Exception handling
* Responsive web design
* Basic JavaScript browser interaction

---

## 📸 Supported Image Formats

The application supports:

```text
PNG
JPG
JPEG
WEBP
BMP
```

The maximum upload size is **10 MB**.

---

## 🔮 Future Improvements

Possible enhancements include:

* 🎨 Extract more colour combinations
* 🖌️ Colour palette export
* 📋 Copy the entire palette
* 📄 Export palette as JSON
* 📷 Drag-and-drop uploads
* 🌈 Gradient generation
* 💾 Download palette as an image
* 🎨 Custom colour filtering
* 📊 Colour percentage visualization

---

## 📚 100 Days of Python

### Day 92 / 100 ✅

This project is part of my **100 Days of Python** journey and focuses on combining Python image processing with Flask web development.

---

## 👩‍💻 Author

**Fatima Ch**

**100 Days of Python — Day 92/100**

> Learn • Build • Practice • Improve 🚀

---

## 📌 Project Status

**Completed ✅**

The Image Colour Palette Generator is fully functional and ready for local use and GitHub submission.
