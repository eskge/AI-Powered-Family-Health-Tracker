"""
Health Tracker - Family Version
Persistent multi-patient personal health tracker
Integrated with Gemini AI for Trend Analysis and Chat
"""

import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai

# =============================================================================
# AI CONFIGURATION (GEMINI)
# =============================================================================
# Replace with your actual API Key from https://aistudio.google.com/
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" 

# Change the logic to check if a key actually exists
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        model = None
else:
    model = None

# =============================================================================
# DATABASE
# =============================================================================

def init_db():
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            report_date DATE,
            notes TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY,
            report_id INTEGER,
            test_name TEXT,
            value REAL,
            unit TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_patient(name, age, gender):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute("SELECT id FROM patients WHERE name = ?", (name,))
    row = c.fetchone()

    if row:
        patient_id = row[0]
    else:
        c.execute(
            "INSERT INTO patients (name, age, gender) VALUES (?, ?, ?)",
            (name, age, gender),
        )
        patient_id = c.lastrowid
        conn.commit()

    conn.close()
    return patient_id


def get_all_patients():
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute("SELECT id, name, age, gender FROM patients ORDER BY name")
    patients = [
        {"id": r[0], "name": r[1], "age": r[2], "gender": r[3]}
        for r in c.fetchall()
    ]

    conn.close()
    return patients


def add_report(patient_id, date, notes=""):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO reports (patient_id, report_date, notes) VALUES (?, ?, ?)",
        (patient_id, date, notes),
    )
    report_id = c.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_or_create_report(patient_id, date, notes=""):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT id FROM reports
        WHERE patient_id = ? AND report_date = ?
        """,
        (patient_id, date),
    )

    row = c.fetchone()

    if row:
        report_id = row[0]
    else:
        c.execute(
            """
            INSERT INTO reports (patient_id, report_date, notes)
            VALUES (?, ?, ?)
            """,
            (patient_id, date, notes),
        )
        report_id = c.lastrowid
        conn.commit()

    conn.close()
    return report_id


def add_test(report_id, name, value, unit, status):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO tests (report_id, test_name, value, unit, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (report_id, name, value, unit, status),
    )

    conn.commit()
    conn.close()


def get_reports(patient_id):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT id, report_date, notes
        FROM reports
        WHERE patient_id = ?
        ORDER BY report_date DESC
        """,
        (patient_id,),
    )

    reports = [{"id": r[0], "date": r[1], "notes": r[2]} for r in c.fetchall()]
    conn.close()
    return reports


def get_tests(report_id):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT test_name, value, unit, status
        FROM tests
        WHERE report_id = ?
        ORDER BY test_name
        """,
        (report_id,),
    )

    tests = [
        {"test": r[0], "value": r[1], "unit": r[2], "status": r[3]}
        for r in c.fetchall()
    ]
    conn.close()
    return tests


def get_all_test_names(patient_id):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT DISTINCT t.test_name
        FROM tests t
        JOIN reports r ON t.report_id = r.id
        WHERE r.patient_id = ?
        ORDER BY t.test_name
        """,
        (patient_id,),
    )

    tests = [r[0] for r in c.fetchall()]
    conn.close()
    return tests


def get_test_history(patient_id, test_name):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT r.report_date, t.value, t.unit, t.status
        FROM tests t
        JOIN reports r ON t.report_id = r.id
        WHERE r.patient_id = ? AND t.test_name = ?
        ORDER BY r.report_date
        """,
        (patient_id, test_name),
    )

    history = [
        {"date": r[0], "value": r[1], "unit": r[2], "status": r[3]}
        for r in c.fetchall()
    ]
    conn.close()
    return history


# =============================================================================
# TEST DEFINITIONS
# =============================================================================

TESTS = {
    "Blood Sugar": {
        "Fasting Glucose": {"unit": "mg/dL", "normal": (70, 100)},
        "PP Glucose": {"unit": "mg/dL", "normal": (70, 140)},
        "Random Blood Sugar": {"unit": "mg/dL", "normal": (70, 140)},
        "HbA1c": {"unit": "%", "normal": (0, 5.7)},
        "Average Blood Glucose (ABG)": {"unit": "mg/dL", "normal": (90, 120)},
    },
    "Kidney & Metabolic": {
        "Creatinine": {"unit": "mg/dL", "normal": (0.55, 1.02)},
        "BUN": {"unit": "mg/dL", "normal": (7.94, 20.07)},
        "Urea": {"unit": "mg/dL", "normal": (17, 43)},
        "Uric Acid": {"unit": "mg/dL", "normal": (3.2, 6.1)},
        "eGFR": {"unit": "mL/min/1.73 m²", "normal": (90, 150)},
        "BUN / Creatinine Ratio": {"unit": "Ratio", "normal": (9, 23)},
        "Calcium": {"unit": "mg/dL", "normal": (8.8, 10.6)},
    },
    "CBC (Hemogram)": {
        "Hemoglobin": {"unit": "g/dL", "normal": (12.0, 15.0)},
        "WBC (Total Leucocyte Count)": {"unit": "10³/µL", "normal": (4.0, 10.0)},
        "Platelet Count": {"unit": "10³/µL", "normal": (150, 410)},
        "Hematocrit (PCV)": {"unit": "%", "normal": (36.0, 46.0)},
        "MCV": {"unit": "fL", "normal": (83.0, 101.0)},
        "MCH": {"unit": "pg", "normal": (27.0, 32.0)},
        "MCHC": {"unit": "g/dL", "normal": (31.5, 34.5)},
        "Neutrophils": {"unit": "%", "normal": (40, 80)},
        "Lymphocytes": {"unit": "%", "normal": (20, 40)},
        "Monocytes": {"unit": "%", "normal": (2, 10)},
        "Eosinophils": {"unit": "%", "normal": (1, 6)},
        "Basophils": {"unit": "%", "normal": (0, 2)},
        "RDW-CV": {"unit": "%", "normal": (11.6, 14.0)},
        "MPV": {"unit": "fL", "normal": (6.5, 12.0)},
    },
    "Electrolytes": {
        "Sodium": {"unit": "mmol/L", "normal": (136, 145)},
        "Potassium": {"unit": "mmol/L", "normal": (3.5, 5.1)},
    },
    "Thyroid & Hormones": {
        "TSH (Ultra-sensitive)": {"unit": "µIU/mL", "normal": (0.54, 5.30)},
        "Total T3": {"unit": "ng/dL", "normal": (80, 200)},
        "Total T4": {"unit": "µg/dL", "normal": (4.8, 12.7)},
        "Prolactin": {"unit": "ng/mL", "normal": (4.79, 23.3)},
        "Ferritin": {"unit": "ng/mL", "normal": (4.63, 204.0)},
    },
    "Inflammatory & Special": {
        "D-Dimer": {"unit": "µg/mL FEU", "normal": (0, 1.0)},
    }
}


def get_status(test_name, value):
    for tests in TESTS.values():
        if test_name in tests:
            lo, hi = tests[test_name]["normal"]
            if value < lo:
                return "LOW"
            elif value > hi:
                return "HIGH"
            else:
                return "NORMAL"
    return "UNKNOWN"


# =============================================================================
# STREAMLIT APP
# =============================================================================

def main():
    st.set_page_config(page_title="Family Health Tracker", page_icon="🩺", layout="wide")
    init_db()

    if "patient_id" not in st.session_state:
        st.session_state.patient_id = None
        st.session_state.current_patient_name = ""

    with st.sidebar:
        st.title("🩺 Family Health Tracker")
        st.markdown("---")

        patients = get_all_patients()
        options = ["➕ Add New Patient"] + [
            f"{p['name']} ({p['age']} / {p['gender']})" for p in patients
        ]

        selected = st.selectbox("Select Family Member", options)

        if selected != "➕ Add New Patient":
            idx = options.index(selected) - 1
            patient = patients[idx]
            st.session_state.patient_id = patient["id"]
            st.session_state.current_patient_name = patient["name"]
            st.success(f"Active: {patient['name']}")
        else:
            st.markdown("### ➕ New Family Member")
            name = st.text_input("Name")
            age = st.number_input("Age", 1, 120, 30)
            gender = st.selectbox("Gender", ["F", "M"])

            if st.button("Save Patient"):
                if name.strip():
                    st.session_state.patient_id = add_patient(name.strip(), age, gender)
                    st.rerun()
                else:
                    st.warning("Name required")

        st.markdown("---")
        page = st.radio("Navigate", ["📝 Add Report", "📊 Trends", "📋 All Reports", "🤖 AI Health Chat"])

    if not st.session_state.patient_id:
        st.info("👈 Select or add a family member")
        return

    if page == "📝 Add Report":
        add_report_page()
    elif page == "📊 Trends":
        trends_page()
    elif page == "📋 All Reports":
        all_reports_page()
    else:
        ai_chat_page()


def add_report_page():
    st.header("📝 Add New Report")

    date = st.date_input("Report Date", value=datetime.now())
    notes = st.text_input("Notes")

    category = st.selectbox("Test Category", list(TESTS.keys()))
    st.subheader(category)

    values = {}

    for test, info in TESTS[category].items():
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(test)

        values[test] = col2.number_input(
            info["unit"],
            min_value=0.0,
            step=0.1,
            key=f"input_{st.session_state.patient_id}_{category}_{test}",
            label_visibility="collapsed",
        )

        col3.caption(f"{info['normal'][0]}–{info['normal'][1]}")

    if st.button("💾 Save Report", type="primary"):
        report_id = get_or_create_report(
            st.session_state.patient_id, str(date), notes
        )

        for t, v in values.items():
            if v > 0:
                add_test(
                    report_id,
                    t,
                    v,
                    TESTS[category][t]["unit"],
                    get_status(t, v),
                )

        st.success("Tests added to report ✔")
        st.balloons()


def trends_page():
    st.header("📊 Trends")

    tests = get_all_test_names(st.session_state.patient_id)
    if not tests:
        st.info("No data yet")
        return

    test = st.selectbox("Select Test", tests)
    history = get_test_history(st.session_state.patient_id, test)

    if not history:
        return

    df = pd.DataFrame(history)
    df["date"] = pd.to_datetime(df["date"])

    normal_low = None
    normal_high = None
    unit = df["unit"].iloc[0] if not df.empty else ""

    for category in TESTS.values():
        if test in category:
            normal_low, normal_high = category[test]["normal"]
            break

    fig = go.Figure()

    if normal_low is not None and normal_high is not None:
        fig.add_hrect(
            y0=normal_low, 
            y1=normal_high, 
            fillcolor="rgba(0, 255, 0, 0.1)", 
            line_width=0, 
            layer="below", 
            annotation_text="Normal Range", 
            annotation_position="top left"
        )

    fig.add_trace(go.Scatter(
        x=df["date"], 
        y=df["value"], 
        mode="lines+markers",
        name=test,
        line=dict(color="#1f77b4", width=3),
        marker=dict(size=10, color="black")
    ))

    fig.update_layout(
        title=f"Trend for {test} ({unit})",
        xaxis_title="Date",
        yaxis_title=unit,
        hovermode="x unified",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)


def all_reports_page():
    st.header("📋 All Reports")

    for report in get_reports(st.session_state.patient_id):
        with st.expander(f"📄 {report['date']}"):
            df = pd.DataFrame(get_tests(report["id"]))
            st.dataframe(df, use_container_width=True)

# =============================================================================
# NEW: GEMINI AI HEALTH CHAT LAYER
# =============================================================================

def ai_chat_page():
    st.header("🤖 AI Health Assistant")
    
    if not model:
        st.error("Please add a valid `GEMINI_API_KEY` at the top of the file to use the AI assistant.")
        return

    st.markdown(f"Currently analyzing health trends for **{st.session_state.current_patient_name}**.")

    # Fetch context from the database to give the AI "eyes"
    all_reports = get_reports(st.session_state.patient_id)
    health_context = ""
    
    if all_reports:
        # Get last 5 reports for concise but meaningful context
        for r in all_reports[:5]:
            tests = get_tests(r['id'])
            data_points = ", ".join([f"{t['test']}: {t['value']} {t['unit']} ({t['status']})" for t in tests])
            health_context += f"Date: {r['date']} | Results: {data_points}\n"
    else:
        st.warning("No medical data found. Add reports first so the AI can analyze them.")
        return

    # Sidebar Tools for AI
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Summary")
        if st.button("✨ Summarize Trends"):
            prompt = f"""
            System: You are a medical data analyst. Analyze this history for {st.session_state.current_patient_name}:
            {health_context}
            
            Task: Provide a 3-bullet point summary of the most important trends. 
            Highlight anything that is consistently outside the normal range. 
            End with a 'Things to ask your doctor' section.
            Disclaimer: This is for informational purposes only.
            """
            with st.spinner("AI is analyzing trends..."):
                response = model.generate_content(prompt)
                st.info(response.text)

    with col2:
        st.subheader("Health Chat")
        user_input = st.text_input("Ask about specific results (e.g. 'Why is my Potassium fluctuating?')")
        if st.button("Ask AI"):
            if user_input:
                prompt = f"""
                History for {st.session_state.current_patient_name}:
                {health_context}
                
                Question: {user_input}
                
                Instruction: Answer specifically based on the provided trend data. If a value is high, explain what that test generally indicates.
                """
                with st.spinner("Thinking..."):
                    response = model.generate_content(prompt)
                    st.success(response.text)

if __name__ == "__main__":
    main()