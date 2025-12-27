# AI Exam Checker - RAG-Based Automated Exam Evaluation System

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A complete local-only NLP research project demonstrating Retrieval-Augmented Generation (RAG) for automated exam answer evaluation.

## 🎯 Project Overview

This system evaluates student exam answers against marking schemes using:
- **Semantic retrieval** (ChromaDB + sentence-transformers)
- **Local LLM reasoning** (Ollama)
- **Structured scoring** (criterion-level evaluation)
- **Explainable feedback** generation

### Key Features

✅ **Fully Local** - No cloud APIs, runs entirely on Windows
✅ **Transparent RAG Pipeline** - Clear separation of retrieval, reasoning, and scoring
✅ **Semantic Search** - Vector similarity for relevant criteria matching
✅ **Grounded Evaluation** - LLM constrained to retrieved marking schemes only
✅ **Structured Output** - JSON-formatted scores with justifications
✅ **Persistent Storage** - ChromaDB (vectors) + SQLite (results)

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Student Answer │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  1. Embedding Generator │  (sentence-transformers)
│     all-MiniLM-L6-v2    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  2. Vector Retrieval    │  (ChromaDB)
│     Top-K similar       │
│     marking criteria    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  3. LLM Evaluation      │  (Ollama - llama3.1:8b)
│     Context-grounded    │
│     scoring             │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  4. Scoring Engine      │  (Aggregation + Validation)
│     Total marks         │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  5. Feedback Generator  │  (Structured feedback)
│     Strengths/Weaknesses│
└─────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI |
| **UI** | Streamlit |
| **Vector DB** | ChromaDB (persistent) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **LLM** | Ollama (llama3.1:8b or mistral) |
| **RAG Framework** | LangChain (minimal) |
| **Database** | SQLite |
| **Language** | Python 3.11+ |

---

## 📋 Prerequisites

- **Windows 10/11**
- **Python 3.11 or higher**
- **8GB+ RAM** (16GB recommended for LLM)
- **10GB+ free disk space** (for models)

---

## 🚀 Installation Guide (Windows)

### Step 1: Clone or Download Project

```powershell
cd "C:\Users\hp\Desktop\uni work\NLP"
# Project should be at: C:\Users\hp\Desktop\uni work\NLP\ai_exam_checker
```

### Step 2: Create Virtual Environment

```powershell
# Navigate to project directory
cd ai_exam_checker

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

**If you get an execution policy error**, run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Python Dependencies

```powershell
# Make sure venv is activated
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages (~2-3GB total).

### Step 4: Install and Setup Ollama

#### 4.1 Download Ollama for Windows

1. Visit: https://ollama.com/download
2. Download **Ollama for Windows**
3. Run the installer
4. Ollama will install and start automatically

#### 4.2 Verify Ollama is Running

```powershell
# Check if Ollama service is running
ollama --version
```

You should see output like: `ollama version 0.x.x`

#### 4.3 Pull the LLM Model

```powershell
# Pull llama3.1 8B model (recommended, ~4.7GB)
ollama pull llama3.1:8b

# OR pull mistral (alternative, ~4.1GB)
ollama pull mistral
```

**Note**: First pull will take 10-20 minutes depending on internet speed.

#### 4.4 Test Ollama

```powershell
# Test the model
ollama run llama3.1:8b "Hello, how are you?"
```

Press `Ctrl+D` or type `/bye` to exit the interactive session.

### Step 5: Create Environment File

```powershell
# Copy example env file
copy .env.example .env
```

The default settings in `.env` should work. You can modify them if needed:
```ini
OLLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL=all-MiniLM-L6-v2
TOP_K_RETRIEVAL=5
```

### Step 6: Ingest Marking Schemes

```powershell
# This loads marking schemes into ChromaDB
python ingest.py
```

**Expected Output:**
```
====================================
MARKING SCHEME INGESTION
====================================

Found 4 marking scheme file(s)

Processing: biology_q1.md
  Subject: Biology
  Question: Q1
  Total Marks: 10
  Created 5 chunks

...

Total documents in vector DB: 20
```

### Step 7: Run Smoke Test (Optional but Recommended)

```powershell
python smoke_test.py
```

This tests:
- ✅ Vector retrieval
- ✅ LLM evaluation
- ✅ Feedback generation
- ✅ Database operations

---

## ▶️ Running the System

### Option 1: FastAPI Backend + Streamlit UI (Recommended)

**Terminal 1** - Start FastAPI Backend:
```powershell
# Activate venv if not already
.\venv\Scripts\Activate.ps1

# Start FastAPI
python -m uvicorn app.main:app --reload
```

**Terminal 2** - Start Streamlit UI:
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Start Streamlit
streamlit run ui/app.py
```

**Access the UI:**
- Open browser: http://localhost:8501
- API docs: http://localhost:8000/docs

### Option 2: API Only

```powershell
python -m uvicorn app.main:app --reload
```

Test with API docs at http://localhost:8000/docs

---

## 📖 Usage Guide

### Using the Streamlit UI

1. **Navigate to** http://localhost:8501

2. **Select Subject** (Biology or Computer Science)

3. **Select Question** (Q1 or Q2)

4. **Enter Student Answer** in the text area

5. **Click "Evaluate Answer"**

6. **View Results:**
   - Retrieved rubric criteria (transparency)
   - Score breakdown per criterion
   - Total marks and grade
   - Strengths and weaknesses
   - Improvement suggestions

7. **Check History Tab** to review past evaluations

### Using the API

**Evaluate an answer:**
```powershell
# Using curl (install from https://curl.se/windows/)
curl -X POST "http://localhost:8000/evaluate" ^
  -H "Content-Type: application/json" ^
  -d "{\"subject\":\"Biology\",\"question_id\":\"Q1\",\"student_answer\":\"Your answer here\"}"
```

**Get subjects and questions:**
```powershell
curl http://localhost:8000/subjects
```

**Get evaluation history:**
```powershell
curl http://localhost:8000/history
```

---

## 📁 Project Structure

```
ai_exam_checker/
│
├── app/                      # Backend application
│   ├── main.py              # FastAPI endpoints
│   ├── rag.py               # RAG retrieval logic
│   ├── embeddings.py        # Embedding generation
│   ├── evaluation.py        # LLM evaluation
│   ├── scoring.py           # Score aggregation
│   ├── feedback.py          # Feedback generation
│   ├── db.py                # SQLite operations
│   ├── models.py            # Pydantic data models
│   └── settings.py          # Configuration
│
├── ui/                       # Frontend
│   └── app.py               # Streamlit UI
│
├── data/                     # Data files
│   └── markschemes/         # Marking scheme documents
│       ├── biology_q1.md
│       ├── biology_q2.md
│       ├── cs_q1.md
│       └── cs_q2.md
│
├── chroma_db/               # Vector database (auto-created)
├── exam_results.db          # SQLite database (auto-created)
│
├── ingest.py                # Data ingestion script
├── smoke_test.py            # End-to-end test
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## 🧪 Testing

### Run All Tests

```powershell
python smoke_test.py
```

### Test Individual Components

**Test Retrieval:**
```python
python -c "from app.rag import get_retriever; r = get_retriever(); print(r.retrieve('photosynthesis'))"
```

**Test Ollama Connection:**
```powershell
ollama list
```

---

## 🔧 Troubleshooting

### Problem: "Ollama not found" or connection error

**Solution:**
```powershell
# Check if Ollama is running
ollama --version

# Start Ollama service (it should auto-start)
# Check Windows Services for "Ollama"

# Test connection
ollama list
```

### Problem: "No module named 'app'"

**Solution:**
```powershell
# Make sure you're in the project root
cd ai_exam_checker

# Activate venv
.\venv\Scripts\Activate.ps1
```

### Problem: ChromaDB errors

**Solution:**
```powershell
# Reset and re-ingest
python ingest.py --reset
```

### Problem: Out of memory during evaluation

**Solution:**
- Close other applications
- Use a smaller model: `ollama pull mistral`
- Update `.env`: `OLLAMA_MODEL=mistral`

### Problem: Slow evaluation (>60 seconds)

**Causes:**
- First run downloads embedding model (~100MB)
- Ollama model not pulled
- Limited RAM

**Solution:**
```powershell
# Pull model explicitly
ollama pull llama3.1:8b

# Check model is loaded
ollama list
```

---

## 📊 Demo Dataset

The project includes 4 sample marking schemes:

| Subject | Question | Topic | Marks |
|---------|----------|-------|-------|
| Biology | Q1 | Photosynthesis | 10 |
| Biology | Q2 | Mitosis vs Meiosis | 12 |
| Computer Science | Q1 | OOP Principles | 10 |
| Computer Science | Q2 | Time Complexity | 8 |

---

## 🎓 NLP Techniques Demonstrated

### 1. Document Chunking
- **Criterion-based chunking** (splits by bullet points/numbered items)
- **Metadata preservation** (subject, question_id, marks)
- Located in: `app/rag.py` - `Chunker` class

### 2. Embedding Generation
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Dimension**: 384
- **Batch processing** for efficiency
- Located in: `app/embeddings.py`

### 3. Vector Similarity Search
- **Database**: ChromaDB with persistence
- **Similarity**: Cosine similarity (1 - distance)
- **Filtering**: By subject and question_id
- **Threshold**: Configurable minimum similarity
- Located in: `app/rag.py` - `VectorRetriever` class

### 4. Prompt Engineering
- **Constrained prompting** (only use retrieved context)
- **Structured output** (JSON schema enforcement)
- **Low temperature** (0.1) for consistency
- Located in: `app/evaluation.py` - `_build_evaluation_prompt()`

### 5. Structured Information Extraction
- **Output parsing** from LLM JSON
- **Validation** and error handling
- **Schema mapping** to Pydantic models
- Located in: `app/evaluation.py` - `parse_to_criterion_scores()`

---

## 🔐 Safety & Limitations

### Grounding Mechanisms
- ✅ Evaluation **ONLY** uses retrieved marking criteria
- ✅ Low confidence flagged when retrieval quality is poor
- ✅ Similarity threshold prevents irrelevant context

### Limitations
- 🔸 LLM may occasionally produce invalid JSON
- 🔸 Evaluation quality depends on marking scheme completeness
- 🔸 Local LLM less capable than GPT-4 (but private & free)
- 🔸 Requires manual verification for high-stakes grading

### Recommended Use
- ✅ First-pass grading assistance
- ✅ Formative assessment feedback
- ✅ Research and education
- ❌ Not for final exam grading without human review

---

## 🚦 Performance Notes

### Typical Latency (on modern Windows PC)

| Operation | Time |
|-----------|------|
| Embedding generation | 100-300ms |
| Vector retrieval | 50-150ms |
| LLM evaluation | 5-15 seconds |
| **Total evaluation** | **~10-20 seconds** |

### Storage Requirements

| Component | Size |
|-----------|------|
| Ollama llama3.1:8b | ~4.7GB |
| Embedding model | ~100MB |
| ChromaDB (per 100 docs) | ~5-10MB |
| Python packages | ~2GB |

---

## 📝 Adding New Marking Schemes

1. **Create new markdown file** in `data/markschemes/`
   - Name format: `{subject}_{questionid}.md`
   - Example: `physics_q1.md`

2. **Structure your marking scheme:**
```markdown
# Physics - Question 1
## Newton's Laws

**Total Marks: 10**

### Marking Criteria:

1. **First Law (3 marks)**
   - Award 1 mark for stating the law
   - Award 1 mark for explanation
   - Award 1 mark for example

2. **Second Law (3 marks)**
   - ...
```

3. **Re-ingest data:**
```powershell
python ingest.py
```

4. **Verify in UI** - new subject/question should appear

---

## 🤝 Contributing

This is a research/educational project. Potential extensions:

- [ ] Support for image-based answers
- [ ] Multi-language support
- [ ] Batch evaluation mode
- [ ] Export results to PDF/Excel
- [ ] Fine-tuned embedding models
- [ ] Advanced RAG (re-ranking, hybrid search)

---

## 📄 License

MIT License - Free for educational and research use.

---

## 🙏 Acknowledgments

- **Ollama** - Local LLM inference
- **ChromaDB** - Vector database
- **sentence-transformers** - Embedding models
- **FastAPI** - Modern Python web framework
- **Streamlit** - Rapid UI development

---

## 📧 Support

For issues or questions:
1. Check **Troubleshooting** section above
2. Review terminal output for error messages
3. Verify all prerequisites are installed

---

## 🎯 Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Ollama installed and running
- [ ] Model pulled (`ollama pull llama3.1:8b`)
- [ ] Marking schemes ingested (`python ingest.py`)
- [ ] Smoke test passed (`python smoke_test.py`)
- [ ] FastAPI running (port 8000)
- [ ] Streamlit running (port 8501)
- [ ] ✅ **Ready to evaluate answers!**

---

**Built with ❤️ for NLP research and education**
