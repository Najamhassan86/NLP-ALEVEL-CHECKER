"""
Streamlit UI for AI Exam Checker.
Simple, functional interface for answer evaluation.
"""

import streamlit as st
import requests
from datetime import datetime
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="AI Exam Checker",
    page_icon="📝",
    layout="wide"
)


def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_subjects_and_questions():
    """Fetch available subjects and questions from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/subjects")
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def evaluate_answer(subject, question_id, student_answer):
    """Send evaluation request to API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/evaluate",
            json={
                "subject": subject,
                "question_id": question_id,
                "student_answer": student_answer
            },
            timeout=60
        )

        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        return None, f"Error: {str(e)}"


def get_evaluation_history():
    """Fetch evaluation history from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/history?limit=50")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def get_evaluation_detail(eval_id):
    """Fetch detailed evaluation by ID"""
    try:
        response = requests.get(f"{API_BASE_URL}/history/{eval_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def display_evaluation_results(result):
    """Display evaluation results in a structured format"""

    # Header
    st.markdown("---")
    st.markdown("## 📊 Evaluation Results")

    # Score summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Score",
            f"{result['total_marks_awarded']}/{result['total_marks_possible']}"
        )

    with col2:
        percentage = (result['total_marks_awarded'] / result['total_marks_possible'] * 100) if result['total_marks_possible'] > 0 else 0
        st.metric("Percentage", f"{percentage:.1f}%")

    with col3:
        # Simple grade calculation
        if percentage >= 90:
            grade = "A+"
        elif percentage >= 80:
            grade = "A"
        elif percentage >= 70:
            grade = "B"
        elif percentage >= 60:
            grade = "C"
        else:
            grade = "D"
        st.metric("Grade", grade)

    # Retrieved Context (for transparency)
    st.markdown("### 🔍 Retrieved Marking Criteria")
    st.markdown("*These criteria were retrieved from the marking scheme and used for evaluation:*")

    with st.expander("View Retrieved Context", expanded=False):
        for idx, ctx in enumerate(result['retrieved_context'], 1):
            st.markdown(f"**Criterion {idx}** (Similarity: {ctx['similarity_score']:.2f})")
            st.info(ctx['content'])

    # Detailed Scoring
    st.markdown("### 📋 Detailed Score Breakdown")

    for idx, criterion in enumerate(result['criteria_scores'], 1):
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{idx}. {criterion['criterion']}**")
                st.write(criterion['justification'])

                if criterion['missing_points']:
                    st.warning(f"Missing: {', '.join(criterion['missing_points'])}")

            with col2:
                st.markdown(
                    f"<h3 style='text-align: center;'>{criterion['awarded_marks']}/{criterion['max_marks']}</h3>",
                    unsafe_allow_html=True
                )

            st.markdown("---")

    # Feedback Section
    st.markdown("### 💬 Feedback")

    st.markdown(result['feedback'])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Strengths")
        for strength in result['strengths']:
            st.success(strength)

    with col2:
        st.markdown("#### ⚠️ Areas for Improvement")
        for weakness in result['weaknesses']:
            st.warning(weakness)

    st.markdown("#### 💡 Suggestions")
    for suggestion in result['improvement_suggestions']:
        st.info(suggestion)


def main():
    """Main Streamlit app"""

    st.title("📝 AI Exam Checker")
    st.markdown("*RAG-based Automated Exam Answer Evaluation*")

    # Check API health
    if not check_api_health():
        st.error("⚠️ Backend API is not running. Please start the FastAPI server first.")
        st.code("python -m uvicorn app.main:app --reload", language="bash")
        return

    st.success("✅ Connected to backend API")

    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["Evaluate Answer", "History"])

    if page == "Evaluate Answer":
        show_evaluation_page()
    else:
        show_history_page()


def show_evaluation_page():
    """Show the answer evaluation page"""

    st.markdown("---")
    st.markdown("## ✍️ Submit Answer for Evaluation")

    # Get subjects and questions
    subjects_questions = get_subjects_and_questions()

    if not subjects_questions:
        st.warning("No marking schemes found in database. Please run the ingestion script first.")
        st.code("python ingest.py", language="bash")
        return

    # Subject selection
    subjects = list(subjects_questions.keys())
    selected_subject = st.selectbox("Select Subject", subjects)

    # Question selection
    questions = subjects_questions.get(selected_subject, [])
    selected_question = st.selectbox("Select Question", questions)

    # Student answer input
    st.markdown("### Your Answer")
    student_answer = st.text_area(
        "Enter your answer below:",
        height=200,
        placeholder="Type your answer here..."
    )

    # Evaluate button
    if st.button("🚀 Evaluate Answer", type="primary"):
        if not student_answer.strip():
            st.error("Please enter an answer before evaluating.")
            return

        with st.spinner("Evaluating your answer... This may take 10-30 seconds."):
            result, error = evaluate_answer(
                selected_subject,
                selected_question,
                student_answer
            )

        if error:
            st.error(f"Evaluation failed: {error}")
        else:
            display_evaluation_results(result)


def show_history_page():
    """Show evaluation history page"""

    st.markdown("---")
    st.markdown("## 📚 Evaluation History")

    history = get_evaluation_history()

    if not history:
        st.info("No evaluation history found.")
        return

    st.markdown(f"*Showing {len(history)} most recent evaluations*")

    # Display as table
    for item in history:
        with st.expander(
            f"{item['subject']} - {item['question_id']} | "
            f"Score: {item['total_marks_awarded']}/{item['total_marks_possible']} | "
            f"{item['timestamp'][:19]}"
        ):
            st.markdown(f"**Student Answer:**")
            st.write(item['student_answer'][:200] + "..." if len(item['student_answer']) > 200 else item['student_answer'])

            st.markdown(f"**Score:** {item['total_marks_awarded']}/{item['total_marks_possible']}")

            if st.button(f"View Full Details", key=f"view_{item['id']}"):
                detail = get_evaluation_detail(item['id'])
                if detail:
                    st.json(detail)


if __name__ == "__main__":
    main()
