# 🎓 Skillytics

## 📌 Overview

Skillytics is a **student analytics system** designed to analyze academic and technical skill performance using machine learning.

The system processes raw student datasets, cleans and transforms the data, and applies **Agglomerative Clustering** to group students based on their academic and technical skill performance.

These clusters help administrators **identify student performance patterns**, allowing better decisions when planning academic support, training programs, or skill improvement initiatives.

This project demonstrates practical skills in **data preprocessing, machine learning, backend development, and database integration using Python.**

---

## ❗ Problem Statement

Educational institutions collect large amounts of student performance data, but this data is often **unstructured and difficult to analyze effectively**.

Without proper analysis, administrators cannot easily identify:

* Students who need additional support
* Performance patterns across groups
* Skill gaps between academic and technical abilities

Skillytics solves this by transforming raw data into structured datasets and applying **clustering algorithms** to automatically group students based on performance similarities.

---

## 🧠 Machine Learning Approach

Skillytics uses **Agglomerative Clustering**, a hierarchical clustering algorithm that groups students based on similarity in performance metrics.

The algorithm works by:

1. Treating each student as an individual cluster
2. Iteratively merging the most similar clusters
3. Forming hierarchical groups of students with similar skill profiles

This allows administrators to easily identify clusters such as:

* ⭐ High-performing students
* ⚖️ Balanced performers
* ⚠️ Students requiring academic support

---

## ✨ Key Features

* 📊 Data preprocessing and cleaning pipeline using **Pandas**
* 🧹 Transformation of raw datasets into structured data
* 🧠 Student grouping using **Agglomerative Clustering**
* 🗄️ Database integration for storing processed datasets
* ⚙️ Backend application built with **Flask**
* 🔄 Modular scripts for automated data processing workflows

---

## 🛠️ Tech Stack

### 💻 Language

* Python

### ⚙️ Framework

* Flask

### 🗄️ Database

* SQLite

### 📚 Libraries

* Pandas
* Scikit-learn
* SQLAlchemy

### 🔧 Tools

* Git
* GitHub

---

## 📁 Project Structure

```
Skillytics/
│
├── app.py                     # Main application entry point
├── insert-data-to-db.py       # Script to insert cleaned data into database
├── original-to-clean.py       # Data cleaning and transformation script
│
├── migrations/                # Database migration files
├── instance/                  # Application instance configuration
├── skillytics/                # Core application modules
│
├── venv/                      # Python virtual environment (ignored in Git)
├── node_modules/              # Node dependencies (ignored in Git)
│
├── README.md                  # Project documentation
└── .gitignore
```

---

## 🔄 Data Processing Workflow

The system follows a structured data pipeline:

1️⃣ Raw student dataset is collected
2️⃣ Data cleaning is performed using `original-to-clean.py`
3️⃣ Cleaned dataset is processed and prepared for clustering
4️⃣ **Agglomerative Clustering** groups students based on performance
5️⃣ Processed data is inserted into the database using `insert-data-to-db.py`
6️⃣ Flask backend reads the data for analysis and administrative insights

---

## 🚀 Installation

Clone the repository

```
git clone https://github.com/aqimxn/Skillytics.git
cd Skillytics
```

Create a virtual environment

```
python -m venv venv
```

Activate the environment

Linux / Mac

```
source venv/bin/activate
```

Windows

```
venv\Scripts\activate
```

Install dependencies

```
pip install -r requirements.txt
```

Run the application

```
python app.py
```

---

## 🎯 Learning Outcomes

This project demonstrates:

* 📊 Data preprocessing and cleaning using **Pandas**
* 🤖 Machine learning using **Agglomerative Clustering**
* 🗄️ Database integration using **SQLAlchemy**
* ⚙️ Backend development using **Flask**
* 📂 Writing modular and maintainable Python scripts
* 🔧 Version control using **Git and GitHub**

---

## 🔮 Future Improvements

* 🌐 Create REST API endpoints for analytics data
* 🐳 Containerize the application using Docker
* 🧪 Add automated testing for the data pipeline
* ☁️ Deploy the system using cloud infrastructure

---

## 👨‍💻 Author

**Muhammad Aqiman**

Computer Science Graduate
Interested in **Backend Engineering, Cloud Systems, and Data Engineering**

🔗 GitHub: https://github.com/aqimxn