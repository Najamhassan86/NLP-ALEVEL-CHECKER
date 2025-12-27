@echo off
echo Starting AI Exam Checker UI...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Streamlit
echo Starting Streamlit UI on http://localhost:8501
echo.
echo Press Ctrl+C to stop the UI
echo.

streamlit run ui/app.py
