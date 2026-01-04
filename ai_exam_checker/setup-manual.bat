@echo off
echo ============================================
echo AI Exam Checker - MANUAL Setup Script
echo Use this if setup.bat fails
echo ============================================
echo.

echo IMPORTANT: This installs packages ONE AT A TIME
echo Each package will pause so you can see if it worked
echo.
pause

echo Step 1: Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)
echo.

echo Step 2: Upgrading pip...
python -m pip install --upgrade pip
pause

echo Step 3: Core dependencies...
echo Installing numpy...
pip install numpy
pause

echo Installing pillow...
pip install pillow
pause

echo Installing typing-extensions...
pip install typing-extensions
pause

echo Step 4: Web framework...
echo Installing fastapi...
pip install fastapi
pause

echo Installing uvicorn...
pip install uvicorn[standard]
if errorlevel 1 (
    echo Trying without [standard]...
    pip install uvicorn
)
pause

echo Installing pydantic...
pip install "pydantic>=2.0.0" pydantic-settings python-dotenv
pause

echo Step 5: Streamlit (UI - optional)...
echo Installing streamlit (may take 2-3 minutes)...
pip install streamlit
if errorlevel 1 (
    echo WARNING: Streamlit failed - you can skip it
    echo The backend will still work
    echo Press any key to continue...
    pause >nul
)
pause

echo Step 6: PyTorch (large download ~2GB)...
echo This will take several minutes...
pip install torch
if errorlevel 1 (
    echo ERROR: PyTorch installation failed
    echo Try: pip install torch --index-url https://download.pytorch.org/whl/cu118
    pause
)
pause

echo Step 7: Transformers and Sentence Transformers...
echo Installing transformers...
pip install transformers
pause

echo Installing sentence-transformers...
pip install sentence-transformers
pause

echo Step 8: ChromaDB...
echo Installing chromadb...
pip install chromadb
if errorlevel 1 (
    echo ERROR: ChromaDB failed - this is required!
    pause
    exit /b 1
)
pause

echo Step 9: Ollama client...
echo Installing ollama...
pip install ollama
if errorlevel 1 (
    echo ERROR: Ollama client failed - this is required!
    pause
    exit /b 1
)
pause

echo Step 10: Database and utilities...
echo Installing sqlalchemy...
pip install sqlalchemy
pause

echo Installing utilities...
pip install python-multipart httpx requests
pause

echo Step 11: Verifying installation...
python -c "import fastapi; print('FastAPI: OK')"
python -c "import chromadb; print('ChromaDB: OK')"
python -c "import sentence_transformers; print('SentenceTransformers: OK')"
python -c "import ollama; print('Ollama: OK')"
echo.

echo Step 12: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created!
)
echo.

echo ============================================
echo Manual Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Install Ollama: https://ollama.com/download
echo 2. Pull model: ollama pull llama3.1:8b
echo 3. Ingest data: python ingest.py
echo 4. Test: python smoke_test.py
echo 5. Run: start_backend.bat
echo.
pause
