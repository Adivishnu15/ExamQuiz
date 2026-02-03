import streamlit as st
import time
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
TOTAL_QUESTIONS = 10
EXAM_DURATION_MIN = 12
IMAGE_FOLDER = "images"
# Update this list with your correct keys
CORRECT_ANSWERS = ['C', 'B', 'D', 'A', 'A', 'B', 'B', 'C', 'A', 'B'] 
DB_FILE = "results.csv"
ADMIN_PASSWORD = "admin" # Change this for security

# Initialize CSV storage
if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=["Timestamp", "Name", "Roll", "Score"]).to_csv(DB_FILE, index=False)

def save_and_exit(answers):
    """Calculates score, saves to CSV, and moves to result screen"""
    score = 0
    for i in range(TOTAL_QUESTIONS):
        if answers[i] == CORRECT_ANSWERS[i]:
            score += 1
    
    new_data = pd.DataFrame([[
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        st.session_state.name, 
        st.session_state.roll, 
        f"{score}/{TOTAL_QUESTIONS}"
    ]])
    new_data.to_csv(DB_FILE, mode='a', header=False, index=False)
    
    st.session_state.submitted = True
    st.session_state.exam_started = False
    st.session_state.final_score = score
    st.rerun()

def main():
    st.set_page_config(page_title="Interactive Quiz Portal", layout="wide")

    # Sidebar Navigation
    page = st.sidebar.radio("Navigation", ["Take Exam", "Admin Dashboard"])

    if page == "Take Exam":
        run_quiz()
    else:
        run_admin()

def run_quiz():
    st.title("📝 Online Examination Center")

    if 'exam_started' not in st.session_state:
        st.session_state.exam_started = False
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    # --- 1. LOGIN SECTION ---
    if not st.session_state.exam_started and not st.session_state.submitted:
        st.info("Enter your details to begin the exam. The timer starts immediately after clicking 'Start'.")
        with st.form("login_form"):
            name = st.text_input("Candidate Name")
            roll = st.text_input("Roll Number / ID")
            if st.form_submit_button("Start Exam"):
                if name and roll:
                    st.session_state.update({
                        "exam_started": True,
                        "start_time": time.time(),
                        "name": name,
                        "roll": roll,
                        "current_answers": [None] * TOTAL_QUESTIONS
                    })
                    st.rerun()
                else:
                    st.error("Please provide both Name and Roll Number.")

    # --- 2. EXAM SECTION ---
    elif st.session_state.exam_started:
        # Timer Calculations
        elapsed = time.time() - st.session_state.start_time
        remaining = int((EXAM_DURATION_MIN * 60) - elapsed)

        # Auto-Submit if time hits zero
        if remaining <= 0:
            st.error("⏰ TIME EXPIRED! Auto-submitting your answers...")
            time.sleep(2)
            save_and_exit(st.session_state.current_answers)
        
        # UI for Timer
        mins, secs = divmod(remaining, 60)
        # Visual cues: Red color if less than 2 minutes (120 seconds)
        is_urgent = remaining < 120
        timer_color = "#FF4B4B" if is_urgent else "#31333F"
        
        if is_urgent and remaining % 60 == 0:
            st.toast(f"⚠️ Warning: Only {mins} minutes remaining!", icon="⏳")

        st.sidebar.markdown(
            f"""
            <div style="text-align: center; padding: 10px; border: 2px solid {timer_color}; border-radius: 10px;">
                <h1 style="color: {timer_color}; margin: 0;">{mins:02d}:{secs:02d}</h1>
                <p style="color: {timer_color}; font-weight: bold;">TIME REMAINING</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.sidebar.write(f"**Candidate:** {st.session_state.name}")
        st.sidebar.write(f"**Roll No:** {st.session_state.roll}")

        # Display Questions
        for i in range(TOTAL_QUESTIONS):
            st.subheader(f"Question {i+1}")
            try:
                st.image(f"{IMAGE_FOLDER}/{i+1}.jpg", use_container_width=True)
            except:
                st.warning(f"Image '{i+1}.jpg' not found in folder '{IMAGE_FOLDER}'")
            
            st.session_state.current_answers[i] = st.radio(
                f"Select Option for Q{i+1}:", 
                ["A", "B", "C", "D"], 
                index=None, 
                key=f"q{i}"
            )
            st.divider()

        if st.button("Submit Exam Early", type="primary"):
            save_and_exit(st.session_state.current_answers)

        # Force refresh every 1 second for the timer
        time.sleep(1)
        st.rerun()

    # --- 3. RESULTS SECTION ---
    elif st.session_state.submitted:
        st.balloons()
        st.success("Your exam has been submitted successfully.")
        
        col1, col2 = st.columns(2)
        col1.metric("Candidate", st.session_state.name)
        col2.metric("Final Score", f"{st.session_state.final_score} / {TOTAL_QUESTIONS}")
        
        st.subheader("Question-wise Report")
        report = []
        for i in range(TOTAL_QUESTIONS):
            user_ans = st.session_state.current_answers[i]
            correct_ans = CORRECT_ANSWERS[i]
            report.append({
                "Question": i+1,
                "Your Answer": user_ans,
                "Correct Answer": correct_ans,
                "Status": "✅ Correct" if user_ans == correct_ans else "❌ Incorrect"
            })
        st.table(report)

        if st.button("Logout & Clear Session"):
            st.session_state.clear()
            st.rerun()

def run_admin():
    st.title("🔒 Admin Control Panel")
    password = st.text_input("Enter Admin Password", type="password")
    
    if password == ADMIN_PASSWORD:
        st.success("Authentication Successful")
        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE)
            st.subheader("All Participant Results")
            st.dataframe(df, use_container_width=True)
            
            # Download Feature
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Report (CSV)", csv, "final_results.csv", "text/csv")
            
            if st.button("Clear All Data"):
                os.remove(DB_FILE)
                st.rerun()
        else:
            st.info("No records found in results.csv")
    elif password:
        st.error("Invalid Password")

if __name__ == "__main__":
    main()