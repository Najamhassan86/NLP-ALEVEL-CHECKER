# Quick Start Guide - 5 Minutes to Running System

## Prerequisites
- Windows 10/11
- Python 3.11+ installed
- 8GB+ RAM

## Setup (One-Time)

### 1. Run Automated Setup
```powershell
# Double-click or run:
setup.bat
```

This will:
- Create virtual environment
- Install all Python dependencies (~5-10 minutes)
- Create `.env` configuration file

### 2. Install Ollama

**Download & Install:**
1. Go to: https://ollama.com/download
2. Download "Ollama for Windows"
3. Run installer
4. Ollama starts automatically

**Pull the model:**
```powershell
ollama pull llama3.1:8b
```
Wait for ~4.7GB download (10-20 minutes)

### 3. Ingest Data

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Load marking schemes
python ingest.py
```

Expected output: "Total documents in vector DB: 20"

### 4. Test System (Optional)

```powershell
python smoke_test.py
```

Should show: "🎉 All tests passed!"

---

## Running the System

### Method 1: Using Batch Files (Easiest)

**Terminal 1** - Backend:
```powershell
start_backend.bat
```

**Terminal 2** - UI:
```powershell
start_ui.bat
```

### Method 2: Manual Commands

**Terminal 1** - Backend:
```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

**Terminal 2** - UI:
```powershell
.\venv\Scripts\Activate.ps1
streamlit run ui/app.py
```

---

## Access the Application

1. **UI**: http://localhost:8501
2. **API Docs**: http://localhost:8000/docs

---

## Usage Flow

1. Open UI at http://localhost:8501
2. Select Subject (Biology or Computer Science)
3. Select Question (Q1 or Q2)
4. Type or paste student answer
5. Click "Evaluate Answer"
6. Wait 10-20 seconds
7. View results:
   - Retrieved criteria (transparency)
   - Score breakdown
   - Feedback

---

## Troubleshooting

### "Ollama connection error"
```powershell
# Check Ollama is running
ollama --version

# List models
ollama list

# Should show: llama3.1:8b
```

### "No documents in vector DB"
```powershell
python ingest.py
```

### "Module not found"
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1
```

### PowerShell execution policy error
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Next Steps

- **Add your own marking schemes**: See README.md "Adding New Marking Schemes"
- **Customize settings**: Edit `.env` file
- **Explore API**: http://localhost:8000/docs
- **View history**: Check "History" tab in UI

---

## File Locations

- Vector DB: `./chroma_db/`
- Results: `./exam_results.db`
- Marking schemes: `./data/markschemes/`
- Config: `.env`

---

**Need help?** See full README.md
