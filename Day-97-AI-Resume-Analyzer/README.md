# 🤖 Day 97 — AI Resume Analyzer

A professional **Flask-based Resume Analyzer** that evaluates a PDF resume against a target job description and provides a clear skill-match analysis.

The application extracts text from the uploaded resume, identifies relevant skills, compares them with the job requirements, calculates a match percentage, highlights missing skills, and provides recommendations for improving the resume.

## ✨ Features

* 📄 PDF Resume Upload
* 📝 Job Description Analysis
* 🔍 Automatic Skill Detection
* ✅ Matched Skills Identification
* ⚠️ Missing Skills Detection
* 📊 Resume Match Score
* 🔎 Job Keyword Extraction
* 💡 Personalized Improvement Recommendations
* 📱 Responsive Web Interface
* 🔐 Temporary & Secure File Handling
* 🚫 File Type and Size Validation

## 🛠️ Tech Stack

* **Python**
* **Flask**
* **PyPDF**
* **HTML5**
* **CSS3**
* **JavaScript**
* **Jinja2**
* **Werkzeug**

## 📂 Project Structure

```text
Day-97-AI-Resume-Analyzer/
│
├── app.py
├── resume_analyzer.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
└── uploads/
    └── .gitkeep
```

## ⚙️ Installation

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## ▶️ Run the Application

```bash
python app.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

## 📋 How It Works

1. Upload a PDF resume.
2. Paste the target job description.
3. Click **Analyze Resume**.
4. The application extracts the resume text.
5. Relevant skills are detected automatically.
6. Resume skills are compared with job requirements.
7. A match score is calculated.
8. Missing skills and improvement recommendations are displayed.

## 📊 Analysis Results

The dashboard provides:

* Overall Match Score
* Resume Skills
* Required Skills
* Matched Skills
* Missing Skills
* Important Job Keywords
* Resume Improvement Recommendations

## 🔒 Privacy

Uploaded resumes are processed temporarily and removed after analysis. The application does not permanently store uploaded resume files.

## ⚠️ Limitations

This is an educational project based on text and predefined skill matching. It is not intended to replace professional recruitment or ATS systems.

Image-only/scanned PDFs may require OCR before their text can be analyzed.

## 🚀 Future Enhancements

* AI-powered semantic analysis
* OCR support
* ATS compatibility scoring
* Resume optimization suggestions
* PDF report generation
* Job recommendation system
* User authentication
* Resume history
* Database integration
* OpenAI API integration

## 🎓 Learning Outcomes

This project strengthened my practical understanding of:

* Flask web development
* PDF processing
* File uploads
* Text extraction
* Regular expressions
* Python data processing
* Jinja2 templating
* Frontend integration
* Error handling
* Responsive UI development

## 📚 100 Days of Python

**Day 97 / 100 ✅**

Another step forward in my Python development journey, combining web development, document processing, text analysis, and practical automation into a real-world application.

### 👩‍💻 Author

**Fatima Ch**

**100 Days of Python — Day 97/100**

> Learn • Build • Practice • Improve 🚀
