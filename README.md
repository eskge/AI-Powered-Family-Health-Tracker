# 🧠 AI-Powered Family Health Tracker

A **personal, multi-patient health tracking application** built with **Streamlit**, **SQLite**, and **Gemini AI**, designed to store, visualize, and analyze medical test reports over time.  
The system supports **family-level tracking**, **trend visualization**, and **AI-assisted medical insights** — all running locally.

> ⚠️ Disclaimer: This project is for **personal tracking and educational purposes only**. It does NOT provide medical advice.

---

## ✨ Key Features

### 👨‍👩‍👧 Multi-Patient Support
- Store and manage health records for **multiple family members**
- Persistent local database using SQLite
- Switch seamlessly between patients

### 📄 Date-Based Medical Reports
- One report per **patient + date**
- Add tests from **multiple categories** (Blood Sugar, CBC, Electrolytes, etc.) to the same date
- Mimics real-world lab reports

### 🧪 Extensive Test Coverage
- Blood Sugar (HbA1c, ABG, Fasting, PP)
- Kidney & Metabolic Panel
- CBC / Hemogram
- Electrolytes
- Thyroid & Hormonal Tests
- Inflammatory Markers (D-Dimer)

Each test is automatically marked as:
- **LOW**
- **NORMAL**
- **HIGH**
based on clinically defined reference ranges.

### 📊 Trend Visualization
- Interactive Plotly charts
- Date-wise trends for any test
- Normal reference range highlighted visually
- Helps identify long-term patterns and fluctuations

### 🤖 AI Health Assistant (Gemini)
- Integrated with **Google Gemini**
- AI summarizes recent health trends
- Allows natural-language questions like:
  - *“Why is my potassium fluctuating?”*
  - *“Is my HbA1c improving?”*
- Context-aware: AI answers based only on stored medical data

---

## 🛠️ Tech Stack

| Layer | Technology |
|------|-----------|
| Frontend | Streamlit |
| Database | SQLite |
| Visualization | Plotly |
| AI / LLM | Google Gemini |
| Language | Python |

---

## 🗂️ Project Structure

├── app.py # Main Streamlit application
├── health_tracker.db # SQLite database (auto-created)
├── README.md
