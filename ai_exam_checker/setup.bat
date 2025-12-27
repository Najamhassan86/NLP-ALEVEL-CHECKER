@echo off
echo ============================================
echo AI Exam Checker - Setup Script
echo ============================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Please ensure Python 3.11+ is installed
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Step 3: Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Step 4: Installing dependencies...
echo This may take 5-10 minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

echo Step 5: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created!
) else (
    echo .env file already exists, skipping...
)
echo.

echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Install Ollama from: https://ollama.com/download
echo 2. Pull the model: ollama pull llama3.1:8b
echo 3. Ingest marking schemes: python ingest.py
echo 4. Run smoke test: python smoke_test.py
echo 5. Start backend: start_backend.bat
echo 6. Start UI: start_ui.bat
echo.
pause
