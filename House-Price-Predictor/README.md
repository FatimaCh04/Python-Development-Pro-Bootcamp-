Bilkul. Tumhare project ke liye README **professional GitHub-project level** honi chahiye, jisme screenshots ke placeholders bhi hon. Tum screenshots baad mein `screenshots/` folder mein rakh kar paths replace kar sakti ho.

# 🏠 HousePrice AI — House Price Predictor

> **An end-to-end Machine Learning web application for intelligent house price estimation using property details such as area, bedrooms, bathrooms, and location.**

HousePrice AI is a professional **Machine Learning + Flask web application** that predicts the estimated market value of a property based on historical housing data.

The application provides both a user-friendly **House Price Predictor** and an interactive **ML Dashboard** where users can upload datasets, train the model, evaluate its performance, and visualize predictions.

---

## 📸 Screenshots

### 🏠 Home — House Price Predictor

The home page allows users to enter property details and receive an estimated house price.

<img width="1336" height="650" alt="H 1" src="https://github.com/user-attachments/assets/6ff1b4f4-f9c9-41a1-92e5-abb6ce813e38" />

<img width="1355" height="544" alt="H 2" src="https://github.com/user-attachments/assets/ebd59a83-4c7d-477b-8df5-ca8ff42cfe30" />

<img width="1339" height="646" alt="H 3" src="https://github.com/user-attachments/assets/4110791d-0aab-4858-aa6f-0de2a53b3151" />

<img width="1360" height="573" alt="H 4" src="https://github.com/user-attachments/assets/a37092e9-d888-4f5b-9708-63b8e1b8ee25" />


---

### 📊 ML Dashboard

The ML Dashboard provides dataset upload, validation, preview, model training, and dataset information.

![ML Dashboard](screenshots/dashboard.png)

---

### 📈 Model Performance

The dashboard displays dynamically generated model evaluation metrics including R² Score, MAE, and RMSE along with the Actual vs Predicted visualization.

<img width="1358" height="650" alt="H 5" src="https://github.com/user-attachments/assets/2176927e-64ab-4245-9418-437e811001a6" />

<img width="1357" height="649" alt="H 6" src="https://github.com/user-attachments/assets/63f23333-fbea-4a9f-8968-53759e56018b" />


<img width="1357" height="648" alt="H 7" src="https://github.com/user-attachments/assets/a23e4444-1ba5-4b2b-b608-c184c31b9df9" />


---

### 📋 Dataset Information

The dashboard displays information about the uploaded dataset, including total records, columns, missing values, locations, features, and price range.

<img width="1360" height="646" alt="H 8" src="https://github.com/user-attachments/assets/5e9c10ad-2d9c-4346-a766-06c66be0e234" />

<img width="1357" height="646" alt="H 9" src="https://github.com/user-attachments/assets/2247fd56-a4ac-4fbf-a89b-8de25da81d48" />

<img width="1358" height="644" alt="H 10" src="https://github.com/user-attachments/assets/4e627ec5-11cf-4dae-9a8b-a1c0449dafce" />


---

# ✨ Features

## 🏡 House Price Prediction

Users can enter:

* Area in square feet
* Number of bedrooms
* Number of bathrooms
* Property location

The application uses the trained Machine Learning model to generate an estimated property value.

---

## 📂 CSV Dataset Upload

The ML Dashboard allows users to upload their own housing dataset in CSV format.

The application validates the uploaded dataset before training.

Required columns:

```text
area_sqft
bedrooms
bathrooms
location
price
```

---

## 🔍 Dataset Preview

After uploading a CSV file, the dashboard displays the actual dataset records in a clean preview table.

The dataset information is generated dynamically from the uploaded CSV rather than using hardcoded values.

---

## ⚙️ Data Preprocessing

The application performs preprocessing before model training.

### Numerical Features

* Area
* Bedrooms
* Bathrooms

### Categorical Feature

* Location

Location values are converted into machine-readable features using:

**One-Hot Encoding**

---

# 🤖 Machine Learning Model

HousePrice AI uses a:

### Random Forest Regression Model

The dataset is divided into:

* **80% Training Data**
* **20% Testing Data**

The model learns the relationship between property characteristics and house prices from the training dataset.

---

# 📊 Model Evaluation

The application evaluates the trained model using:

### R² Score

Measures how well the model explains variations in house prices.

### MAE — Mean Absolute Error

Measures the average absolute difference between actual and predicted prices.

### RMSE — Root Mean Squared Error

Measures prediction error while giving higher weight to larger errors.

The dashboard dynamically displays these values after model training.

---

# 📈 Data Visualization

HousePrice AI generates an:

### Actual vs Predicted Price Graph

This visualization compares:

* Actual property prices
* Model predicted prices

The graph is generated dynamically from the test dataset after model training.

---

# 💾 Model Persistence

The trained Machine Learning model is saved using:

**Joblib**

This allows the application to reuse the trained model for future predictions without retraining every time.

---

# 🔄 Application Workflow

```text
CSV Dataset
     ↓
Dataset Validation
     ↓
Dataset Preview
     ↓
Data Preprocessing
     ↓
One-Hot Encoding
     ↓
Train / Test Split
     ↓
Random Forest Regression
     ↓
Model Evaluation
     ↓
Save Model with Joblib
     ↓
House Price Prediction
```

---

# 🖥️ Application Pages

## 1. Home / Predictor

The main prediction interface where users enter property information and receive an estimated price.

### Inputs

* Area (sqft)
* Bedrooms
* Bathrooms
* Location

### Output

* Estimated Market Value
* Price per Square Foot
* Location
* Property Details
* Model Information

---

## 2. ML Dashboard

The ML Dashboard provides the complete Machine Learning workflow.

It includes:

* CSV Upload
* Dataset Validation
* Dataset Preview
* Dataset Information
* Model Training
* Model Status
* Model Performance
* R² Score
* MAE
* RMSE
* Actual vs Predicted Graph

---<img width="1336" height="650" alt="H 1" src="https://github.com/user-attachments/assets/e622c114-86c9-4818-ab79-16ce771b5f5c" />


# 🛠️ Technologies Used

### Programming Language

* Python

### Machine Learning

* Scikit-learn
* Random Forest Regression
* One-Hot Encoding

### Data Processing

* Pandas
* NumPy

### Visualization

* Matplotlib

### Web Framework

* Flask

### Model Persistence

* Joblib

### Frontend

* HTML
* CSS
* JavaScript

---

# 📁 Project Structure

```text
HousePrice-AI/
│
├── app.py
│
├── model/
│   └── house_price_model.joblib
│
├── dataset/
│   └── house_data.csv
│
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   └── about.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── script.js
│   │
│   └── images/
│
├── screenshots/
│   ├── home.png
│   ├── dashboard.png
│   ├── model-performance.png
│   └── dataset-information.png
│
├── requirements.txt
│
└── README.md
```

# 🚀 Installation & Setup

## 1. Clone the Repository

```bash
git clone (https://github.com/FatimaCh04/Python-Development-Pro-Bootcamp-/edit/main/House-Price-Predictor)
```

Navigate into the project:

```bash
cd HousePrice-AI
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Run the Application

```bash
python app.py
```

The Flask application will start locally.

Open the local address shown by Flask in your browser.

---

# 📄 Dataset Format

The application expects the following CSV columns:

| Column      | Type        | Description                  |
| ----------- | ----------- | ---------------------------- |
| `area_sqft` | Numeric     | Property area in square feet |
| `bedrooms`  | Numeric     | Number of bedrooms           |
| `bathrooms` | Numeric     | Number of bathrooms          |
| `location`  | Categorical | Property location            |
| `price`     | Numeric     | Target house price           |

---

# 🧪 Testing the Application

You can test the application using a CSV dataset containing the required columns.

### Test Workflow

```text
1. Open Home
        ↓
2. Enter Property Details
        ↓
3. Generate Prediction
        ↓
4. Open ML Dashboard
        ↓
5. Upload CSV
        ↓
6. Validate Dataset
        ↓
7. Preview Dataset
        ↓
8. Train Model
        ↓
9. Check R² / MAE / RMSE
        ↓
10. Check Actual vs Predicted Graph
        ↓
11. Return to Home
        ↓
12. Generate Prediction Using New Model
```

---

# 🎯 Project Objectives

The main objectives of HousePrice AI are:

* Build a practical Machine Learning application
* Predict house prices using real property features
* Implement categorical data preprocessing
* Train and evaluate a regression model
* Create a user-friendly web interface
* Allow dynamic CSV dataset uploads
* Visualize model performance
* Save and reuse trained models
* Demonstrate an end-to-end ML workflow

---

# 🌟 Key Highlights

* ✅ End-to-end Machine Learning workflow
* ✅ Random Forest Regression
* ✅ Dynamic CSV upload
* ✅ Dataset validation
* ✅ One-Hot Encoding
* ✅ 80/20 train-test split
* ✅ Dynamic model evaluation
* ✅ R², MAE and RMSE
* ✅ Actual vs Predicted visualization
* ✅ Joblib model persistence
* ✅ Flask web application
* ✅ Interactive prediction form
* ✅ Prediction history
* ✅ Responsive user interface
* ✅ Separate ML Dashboard

---

# 🔮 Future Improvements

Possible future enhancements include:

* More advanced regression models
* Hyperparameter tuning
* Cross-validation
* Feature importance visualization
* Interactive Plotly charts
* User authentication
* Cloud deployment
* Database integration
* Automated model retraining
* More detailed prediction reports

---

# 📚 Machine Learning Concepts Demonstrated

This project demonstrates practical understanding of:

* Supervised Learning
* Regression
* Train/Test Split
* Categorical Encoding
* Feature Preprocessing
* Random Forest
* Model Evaluation
* R² Score
* MAE
* RMSE
* Model Persistence
* Data Visualization

---

## 📌 Author

**Fatima Choudhry**

Machine Learning / Python Project

