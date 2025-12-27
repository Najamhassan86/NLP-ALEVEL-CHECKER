# System Architecture - AI Exam Checker

## High-Level Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                            │
│                      Streamlit Web App                            │
│                     http://localhost:8501                         │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP REST API
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                             │
│                     http://localhost:8000                         │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              EVALUATION ORCHESTRATOR                     │   │
│  │            (app/main.py - /evaluate)                     │   │
│  └────┬──────────────────────────────────────────────┬─────┘   │
│       │                                              │          │
│       ▼                                              ▼          │
│  ┌────────────────────┐                    ┌─────────────────┐ │
│  │   RAG PIPELINE     │                    │  PERSISTENCE     │ │
│  └────────────────────┘                    └─────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline Detail

### Stage 1: Embedding & Indexing (Offline)

```
┌─────────────────────┐
│  Marking Schemes    │
│  (.md files)        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Document Loader    │
│  (ingest.py)        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│     Chunker         │  Strategy: Criterion-based
│  (app/rag.py)       │  - Split by bullet points
└──────┬──────────────┘  - Split by numbered items
       │                  - Preserve metadata
       ▼
┌─────────────────────┐
│ Embedding Generator │  Model: all-MiniLM-L6-v2
│ (app/embeddings.py) │  Dimension: 384
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│    ChromaDB         │  Persistent vector store
│  ./chroma_db/       │  Cosine similarity search
└─────────────────────┘
```

### Stage 2: Retrieval (Online - per evaluation)

```
┌─────────────────────┐
│  Student Answer     │
│  (User Input)       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Embedding Generator │  Convert to 384-dim vector
│ (same model)        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Vector Similarity   │  Query ChromaDB
│    Search           │  Top-K retrieval (K=5)
│                     │  Filter: subject + question_id
└──────┬──────────────┘  Threshold: 0.3 similarity
       │
       ▼
┌─────────────────────┐
│ Retrieved Context   │  5 most relevant criteria
│ (RetrievalResult[]) │  + similarity scores
└─────────────────────┘
```

### Stage 3: LLM Evaluation

```
┌─────────────────────┐
│  Student Answer     │
│        +            │
│ Retrieved Context   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Prompt Builder     │  Constrained prompting:
│ (app/evaluation.py) │  - Only use retrieved context
└──────┬──────────────┘  - Output structured JSON
       │                  - Explain all scores
       ▼
┌─────────────────────┐
│   Ollama LLM        │  Model: llama3.1:8b
│ localhost:11434     │  Temperature: 0.1 (deterministic)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  JSON Response      │  {
│                     │    criteria_evaluations: [
│                     │      {criterion, marks, justification}
└─────────────────────┘    ]
                           }
```

### Stage 4: Scoring & Feedback

```
┌─────────────────────┐
│ Criterion Scores    │  Parsed from LLM JSON
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Scoring Engine     │  - Aggregate total marks
│  (app/scoring.py)   │  - Validate consistency
└──────┬──────────────┘  - Identify strengths/weaknesses
       │
       ▼
┌─────────────────────┐
│ Feedback Generator  │  - Generate summary
│ (app/feedback.py)   │  - Improvement suggestions
└──────┬──────────────┘  - Grade assignment
       │
       ▼
┌─────────────────────┐
│ Evaluation Response │  Complete results
│                     │  (EvaluationResponse)
└─────────────────────┘
```

---

## Data Models

### Core Data Flow

```
EvaluationRequest
  ↓
RetrievalResult[] ──┐
                     ├─→ LLM
Student Answer ──────┘
  ↓
CriterionScore[]
  ↓
EvaluationResponse
  ↓
SQLite Database
```

### Key Pydantic Models

```python
EvaluationRequest {
  subject: str
  question_id: str
  student_answer: str
}

RetrievalResult {
  content: str
  metadata: dict
  similarity_score: float
}

CriterionScore {
  criterion: str
  max_marks: int
  awarded_marks: int
  justification: str
  missing_points: list[str]
}

EvaluationResponse {
  subject: str
  question_id: str
  student_answer: str
  retrieved_context: RetrievalResult[]
  criteria_scores: CriterionScore[]
  total_marks_awarded: int
  total_marks_possible: int
  feedback: str
  strengths: list[str]
  weaknesses: list[str]
  improvement_suggestions: list[str]
  timestamp: datetime
}
```

---

## Component Interactions

### Singleton Pattern (Performance Optimization)

```
┌──────────────────────────────────────────┐
│         Global Instances (Cached)         │
├──────────────────────────────────────────┤
│  EmbeddingGenerator  (loaded once)       │
│  VectorRetriever     (shared connection) │
│  AnswerEvaluator     (Ollama client)     │
│  ScoringEngine       (stateless)         │
│  FeedbackGenerator   (stateless)         │
│  Database            (connection pool)   │
└──────────────────────────────────────────┘
```

### API Endpoint Flow

```
POST /evaluate
  │
  ├─→ get_retriever()
  │    └─→ Semantic search
  │
  ├─→ get_evaluator()
  │    └─→ LLM call (Ollama)
  │
  ├─→ get_scoring_engine()
  │    └─→ Score aggregation
  │
  ├─→ get_feedback_generator()
  │    └─→ Feedback synthesis
  │
  └─→ get_database()
       └─→ Save results
```

---

## Technology Stack Rationale

### Why ChromaDB?
- ✅ **Persistent local storage** (no cloud required)
- ✅ **Built-in embedding support**
- ✅ **Easy metadata filtering**
- ✅ **Windows compatible**
- ✅ **No configuration needed**

### Why Ollama?
- ✅ **Fully local inference** (privacy)
- ✅ **Easy Windows installation**
- ✅ **Multiple model support**
- ✅ **HTTP API** (language agnostic)
- ✅ **Automatic GPU acceleration**

### Why sentence-transformers?
- ✅ **Lightweight models** (~100MB)
- ✅ **Fast inference** (CPU friendly)
- ✅ **High quality semantic embeddings**
- ✅ **Pre-trained on semantic similarity**

### Why FastAPI?
- ✅ **Async support** (future scalability)
- ✅ **Auto-generated API docs**
- ✅ **Type validation** (Pydantic)
- ✅ **Modern Python framework**

### Why Streamlit?
- ✅ **Rapid development** (minimal code)
- ✅ **Python-native** (no JS required)
- ✅ **Interactive widgets**
- ✅ **Perfect for demos/research**

---

## Performance Characteristics

### Latency Breakdown (Typical)

```
Total: ~10-20 seconds
├─ Embedding generation:    0.1-0.3s
├─ Vector retrieval:        0.05-0.15s
├─ LLM inference:           5-15s     ◄── Bottleneck
├─ Score calculation:       <0.01s
├─ Feedback generation:     <0.01s
└─ Database save:           <0.05s
```

### Memory Usage

```
Base (Python + packages):    ~500MB
Embedding model:             ~100MB
ChromaDB index:              ~10MB (per 100 docs)
Ollama (llama3.1:8b):        ~4-6GB
──────────────────────────────────
Total:                       ~5-7GB
```

### Storage

```
./chroma_db/           ~5-10MB  (vectors)
./exam_results.db      ~1-5MB   (per 1000 evaluations)
Models:                ~4.7GB   (Ollama)
                       ~100MB   (embeddings)
```

---

## Security & Privacy

### Data Flow
- ✅ All data stays local (Windows machine)
- ✅ No internet required (after setup)
- ✅ No telemetry or tracking
- ✅ No API keys needed

### Access Control
- 🔸 No authentication (local use only)
- 🔸 API accessible to localhost only
- 🔸 Not production-ready for public deployment

---

## Extensibility Points

### Add New Embedding Model
```python
# app/settings.py
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
```

### Add New LLM
```python
# app/settings.py
OLLAMA_MODEL = "mistral" or "llama2" or "codellama"
```

### Custom Chunking Strategy
```python
# app/rag.py - Chunker class
def chunk_by_semantic_similarity(self, text, metadata):
    # Implement semantic chunking
    pass
```

### Add Re-ranking
```python
# After retrieval, before LLM
from sentence_transformers import CrossEncoder
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
scores = reranker.predict([(query, doc) for doc in retrieved])
```

---

## Error Handling Strategy

```
User Input
  ↓
Validation (Pydantic) ──→ 422 Error
  ↓
Retrieval ──→ No results? ──→ 404 Error
  ↓
LLM Evaluation ──→ Timeout/Error? ──→ 500 Error
  ↓              └─→ Log & return low confidence
Score Validation ──→ Warnings logged
  ↓
Success Response (200)
```

---

## Future Enhancements (Research Directions)

1. **Hybrid Search**: Combine dense (vector) + sparse (BM25) retrieval
2. **Re-ranking**: Two-stage retrieval with cross-encoders
3. **Query Expansion**: Rephrase student answers for better retrieval
4. **Chain-of-Thought**: Multi-step reasoning for complex answers
5. **Confidence Calibration**: Better uncertainty estimation
6. **Multi-modal**: Support image-based answers
7. **Active Learning**: Improve from feedback

---

**This architecture prioritizes transparency, local execution, and research clarity over production scalability.**
