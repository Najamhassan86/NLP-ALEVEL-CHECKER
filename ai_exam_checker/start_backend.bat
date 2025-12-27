@echo off
echo Starting AI Exam Checker Backend...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start FastAPI
echo Starting FastAPI server on http://localhost:8000
echo API docs will be available at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --reload
