# 🖼️ Day 91 — Image Watermarking App

A modern desktop **Image Watermarking Application** built with **Python, Tkinter, and Pillow** as part of the **100 Days of Code: The Complete Python Pro Bootcamp**.

The application allows users to select an image, add a custom watermark, adjust its position and opacity, preview the result, and save the final watermarked image.

---

## 🚀 Project Overview

The **Image Watermarking App** provides a simple interface for adding custom text watermarks to images.

Users can choose an image from their computer, customize the watermark text, select its position, adjust opacity, preview the changes, and save the final image.

### Application Workflow

```text
Select Image
     ↓
Enter Watermark
     ↓
Choose Position
     ↓
Adjust Opacity
     ↓
Preview Image
     ↓
Save Watermarked Image
```

---

## ✨ Features

* 📂 Select images from your computer
* 🖼️ Image preview
* ✍️ Custom watermark text
* 📍 Five watermark positions
* 🎚️ Adjustable watermark opacity
* ⚡ Real-time preview
* 💾 Save watermarked images
* 🧹 Clear watermark option
* 🖥️ Desktop GUI
* 📱 Resizable application window
* 🚨 Error handling and user notifications
* 🖼️ Supports common image formats

### Supported Formats

* JPG
* JPEG
* PNG
* BMP
* GIF
* WEBP

---

## 🛠️ Technologies Used

| Technology    | Purpose                      |
| ------------- | ---------------------------- |
| **Python**    | Core programming language    |
| **Tkinter**   | Desktop graphical interface  |
| **Pillow**    | Image processing             |
| **ImageDraw** | Drawing watermark text       |
| **ImageTk**   | Displaying images in Tkinter |
| **Pathlib**   | File path management         |

---

## 📂 Project Structure

```text
Day-91-Image-Watermarking-App/
│
├── main.py
├── requirements.txt
├── README.md
│
└── assets/
    └── .gitkeep
```

No sample image is required because users can select their own image through the application.

---

## ⚙️ Requirements

* Python 3.10+
* Tkinter
* Pillow

Tkinter is included with most standard Python installations.

Pillow is installed through `requirements.txt`.

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day-91-Image-Watermarking-App
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

#### Windows

```powershell
venv\Scripts\activate
```

#### macOS/Linux

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

Start the application with:

```bash
python main.py
```

The desktop application will open automatically.

---

## 🧪 How to Use

### Step 1 — Choose an Image

Click:

**📂 Choose Image**

Select an image from your computer.

---

### Step 2 — Enter Watermark Text

Enter the text you want to display on your image.

Example:

```text
© My Brand
```

---

### Step 3 — Choose Position

Select one of the available positions:

* Top Left
* Top Right
* Center
* Bottom Left
* Bottom Right

---

### Step 4 — Adjust Opacity

Use the opacity slider to control how transparent the watermark appears.

---

### Step 5 — Preview

The application automatically updates the preview whenever watermark settings change.

---

### Step 6 — Save

Click:

**💾 Save Image**

Choose the destination and file format.

---

## 🧠 Key Python Concepts Practiced

This project strengthened my understanding of:

* Tkinter GUI development
* GUI layouts
* Buttons and input fields
* File dialogs
* Event handling
* Tkinter variables
* Image processing
* Pillow
* Image composition
* Transparent layers
* Drawing text on images
* Font handling
* File saving
* Exception handling
* Functions
* Global application state

---

## 🖼️ Image Processing

Pillow is used to process the selected image.

The watermark is created on a separate transparent layer:

```python
watermark_layer = Image.new(
    "RGBA",
    image.size,
    (255, 255, 255, 0)
)
```

The watermark text is then drawn onto the layer:

```python
draw.text(
    position,
    watermark_text,
    font=font,
    fill=(255, 255, 255, opacity)
)
```

Finally, the watermark layer is combined with the original image:

```python
Image.alpha_composite(
    image,
    watermark_layer
)
```

This allows the watermark to have adjustable transparency.

---

## 🎯 Learning Objectives

By completing this project, I practiced how to:

* Build a desktop application with Tkinter
* Work with images using Pillow
* Open files using a GUI file dialog
* Display images inside Tkinter
* Draw text on images
* Create transparent image layers
* Control watermark opacity
* Dynamically update a GUI preview
* Save processed images
* Handle different image formats

---

## 💡 Practical Applications

Image watermarking can be useful for:

* Photography portfolios
* Digital artwork
* Brand protection
* Social media content
* Product photography
* Business images
* Copyright identification
* Personal branding

---

## 🔮 Future Improvements

Possible future enhancements include:

* 🖼️ Image logo watermark support
* 🔤 Custom font selection
* 🎨 Watermark color selection
* 🔄 Watermark rotation
* 📏 Adjustable watermark size
* 🔢 Batch watermarking
* 🖱️ Drag-and-drop positioning
* 📂 Folder processing
* ↩️ Undo/Redo
* 🌙 Dark mode
* 📊 Image metadata preservation

---

## 📚 100 Days of Python

### Day 91 / 100 — Completed ✅

This project is part of my **100 Days of Python** learning journey.

Day 91 focused on building an **Image Watermarking App** and strengthening practical skills in **Tkinter GUI development and image processing with Pillow**.

---

## 👩‍💻 Author

**Fatima Ch**

### 100 Days of Python 🐍

**Day 91/100 — Learn • Build • Improve 🚀**

---

## 📌 Project Status

**Completed ✅**

A functional desktop image watermarking application featuring:

* Image selection
* Custom text watermark
* Position control
* Opacity control
* Live preview
* Image processing
* Watermarked image export
