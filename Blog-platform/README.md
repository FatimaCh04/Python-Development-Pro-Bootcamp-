# 📝 DevBlog Platform

A modern, full-stack blogging platform built with **Flask** that allows users to register, log in, publish blog posts, edit or delete their own articles, upload profile pictures, and interact through comments.

---

## 📌 Features

### 🔐 User Authentication
- User Registration
- User Login & Logout
- Secure Password Hashing
- Session Management using Flask-Login

### 📝 Blog Management
- Create New Blog Posts
- View All Blog Posts
- Edit Your Own Posts
- Delete Your Own Posts
- Responsive Blog Cards

### 💬 Comment System
- Logged-in users can comment on posts
- Display comments under each blog post

### 👤 User Profile
- Update Profile Information
- Upload Profile Picture
- Dashboard with User Statistics

### 🎨 Modern UI
- Bootstrap 5 Responsive Design
- Mobile Friendly Layout
- Clean Navigation
- Flash Messages
- Dashboard Interface

---

## 🛠️ Tech Stack

- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- WTForms
- SQLite
- Jinja2
- Bootstrap 5
- HTML5
- CSS3
- JavaScript

---

## 📂 Project Structure

```
DevBlog/
│
├── app.py
├── models.py
├── routes.py
├── forms.py
├── config.py
├── requirements.txt
│
├── instance/
│   └── blog.db
│
├── static/
│   ├── css/
│   ├── uploads/
│   └── images/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── create_post.html
│   ├── edit_post.html
│   ├── post.html
│   ├── dashboard.html
│   ├── 403.html
│   └── 404.html
│
└── README.md
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/FatimaCh04/Python-Development-Pro-Bootcamp-/tree/main/Blog-platform
cd devblog-platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```


### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000
```

---

## 📸 Screenshots

<img width="1350" height="638" alt="1" src="https://github.com/user-attachments/assets/48646b41-8639-4aa7-b2a3-b82d87d1588f" />

<img width="1356" height="646" alt="2" src="https://github.com/user-attachments/assets/1c3300a3-b1c6-43ce-b72d-90462fafd331" />


<img width="1353" height="645" alt="3" src="https://github.com/user-attachments/assets/257c4a4c-afeb-4ec2-a038-51c3e945fb5c" />

<img width="1357" height="638" alt="4" src="https://github.com/user-attachments/assets/e1502e27-711b-448d-b75d-e1ea3c601b74" />


<img width="1352" height="635" alt="5" src="https://github.com/user-attachments/assets/e65f5bae-4d0d-4347-b36d-637f631aa994" />

<img width="1337" height="639" alt="6" src="https://github.com/user-attachments/assets/59c23cf0-9f99-4bec-90bd-bed0e3cf93ac" />

<img width="1303" height="635" alt="7" src="https://github.com/user-attachments/assets/6b4a678a-6147-40c1-8574-c664d78b186f" />

<img width="1291" height="634" alt="8" src="https://github.com/user-attachments/assets/534659a8-c550-49e2-abe2-952ec9d05dee" />

<img width="1288" height="641" alt="10" src="https://github.com/user-attachments/assets/117a5d5a-ed17-43f3-93fc-eeb38c6418fa" />

<img width="1278" height="639" alt="11" src="https://github.com/user-attachments/assets/dc81b2af-bf0b-4512-aac2-513e25105284" />

<img width="1323" height="641" alt="9" src="https://github.com/user-attachments/assets/73116b33-654f-43e1-a630-8a1d286da61c" />






---

## 📚 Database

The project uses **SQLite** with SQLAlchemy ORM.

### Database Models

- User
- Post
- Comment

Relationships:

```
User
 ├── Posts
 └── Comments

Post
 └── Comments
```

---

## 🔒 Security

- Password Hashing
- Authentication using Flask-Login
- Login Required Routes
- User Authorization
- Form Validation
- Secure File Uploads

---

## 🎯 Future Improvements

- Like & Dislike System
- Categories & Tags
- Search Functionality
- Email Verification
- Password Reset
- Rich Text Editor
- Dark Mode
- Admin Panel

---

## 👨‍💻 Author

**Fatima**

Python & Flask Developer

