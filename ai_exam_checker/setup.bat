@echo off
echo ============================================
echo AI Exam Checker - Setup Script
echo Python 3.11-3.13 Compatible
echo ============================================
echo.

echo Checking Python version...
python --version
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
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

echo Step 3: Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
echo.

echo Step 4: Installing dependencies in stages...
echo This may take 10-15 minutes. Please be patient...
echo.

echo [Stage 1/8] Installing core dependencies...
pip install --default-timeout=100 numpy pillow typing-extensions
if errorlevel 1 (
    echo WARNING: Core dependencies had issues, but continuing...
)
echo.

echo [Stage 2/8] Installing web framework...
pip install --default-timeout=100 fastapi uvicorn[standard] pydantic pydantic-settings python-dotenv
if errorlevel 1 (
    echo ERROR: Failed to install web framework
    echo Try running: pip install fastapi uvicorn pydantic pydantic-settings python-dotenv
    pause
    exit /b 1
)
echo.

echo [Stage 3/8] Installing Streamlit (UI)...
pip install --default-timeout=100 streamlit
if errorlevel 1 (
    echo WARNING: Streamlit installation failed
    echo The system can work without UI. You can install it later with: pip install streamlit
    echo Press any key to continue...
    pause >nul
)
echo.

echo [Stage 4/8] Installing ML/NLP packages (large download ~2GB)...
pip install --default-timeout=100 torch transformers sentence-transformers
if errorlevel 1 (
    echo ERROR: Failed to install ML packages
    echo Try manually: pip install torch transformers sentence-transformers
    pause
    exit /b 1
)
echo.

echo [Stage 5/8] Installing ChromaDB...
pip install --default-timeout=100 chromadb
if errorlevel 1 (
    echo ERROR: Failed to install ChromaDB
    pause
    exit /b 1
)
echo.

echo [Stage 6/8] Installing Ollama client...
pip install --default-timeout=100 ollama
if errorlevel 1 (
    echo ERROR: Failed to install Ollama client
    pause
    exit /b 1
)
echo.

echo [Stage 7/8] Installing database...
pip install --default-timeout=100 sqlalchemy
echo.

echo [Stage 8/8] Installing utilities...
pip install --default-timeout=100 python-multipart httpx requests
echo.

echo Verifying installation...
python -c "import fastapi, chromadb, sentence_transformers, ollama; print('Core packages OK')"
if errorlevel 1 (
    echo WARNING: Some packages may not have installed correctly
    echo Check the output above for errors
)
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
echo If you had any errors, check TROUBLESHOOTING.txt
echo.
pause
