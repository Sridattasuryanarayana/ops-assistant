# GenAI Operations Assistant

AI-powered operations automation for ticket triage, root cause analysis, and resolution recommendations.

## 🎯 Problem Solved

Operations teams face:
- High ticket volumes
- Repetitive manual triage
- Slow Root Cause Analysis (RCA)
- Knowledge scattered across documents, logs, and SOPs

## 💡 Solution

This assistant uses **RAG (Retrieval-Augmented Generation)** with **Qwen3-8B** to:

1. **Ingest** operational data (tickets, logs, SOPs, knowledge base)
2. **Retrieve** relevant context using semantic search
3. **Analyze** with LLM reasoning (classify, summarize, diagnose)
4. **Recommend** actionable resolutions with draft responses

## 📊 Business Impact

- ~40% reduction in resolution time
- Faster MTTR (Mean Time To Resolution)
- Reduced L1/L2 manual effort
- Consistent triage and classification

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
cd ops-assistant
pip install -r requirements.txt
```

### 2. Configure Endpoint

Edit `.env` to set your Qwen endpoint:

```env
LLM_BASE_URL=http://wiphack30qx5aw.cloudloka.com:8000/v1
LLM_MODEL=Qwen/Qwen3-8B
```

### 3. Run the Demo

```powershell
python demo.py
```

### 4. Start the API Server

```powershell
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

API docs available at: `http://localhost:8080/docs`

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/analyze` | POST | Full ticket analysis (triage + RCA + resolution) |
| `/api/triage` | POST | Classify and prioritize ticket |
| `/api/rca` | POST | Root cause analysis |
| `/api/resolution` | POST | Resolution recommendations |
| `/api/chat` | POST | Free-form chat with RAG context |
| `/api/ingest` | POST | Add document to knowledge base |
| `/api/knowledge/stats` | GET | Knowledge base statistics |

## 📝 Example Usage

### Analyze a Ticket

```python
import requests

response = requests.post("http://localhost:8080/api/analyze", json={
    "ticket_id": "INC001",
    "title": "Database connection timeout",
    "description": "Users reporting slow response times and timeout errors. Logs show connection pool exhausted.",
    "logs": "2024-01-15 14:02:15 ERROR Connection pool exhausted"
})

result = response.json()
print(f"Priority: {result['triage']['priority']}")
print(f"Root Cause: {result['rca']['root_cause']}")
print(f"Actions: {result['resolution']['recommended_actions']}")
```

### Chat Interface

```python
response = requests.post("http://localhost:8080/api/chat", json={
    "message": "How do I troubleshoot high CPU usage on web servers?"
})

print(response.json()["response"])
```

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Tickets/Logs  │────▶│  Document        │────▶│  ChromaDB       │
│   SOPs/KB       │     │  Ingestion       │     │  Vector Store   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌──────────────────┐              │ Semantic
                        │  FastAPI Server  │              │ Search
                        └────────┬─────────┘              │
                                 │                        ▼
┌─────────────────┐     ┌────────▼─────────┐     ┌─────────────────┐
│   User Query    │────▶│  RAG Pipeline    │────▶│  Context        │
│   (Ticket)      │     │                  │     │  Retrieved      │
└─────────────────┘     └────────┬─────────┘     └────────┬────────┘
                                 │                        │
                        ┌────────▼────────────────────────▼────────┐
                        │           Qwen3-8B LLM                   │
                        │   (OpenAI-compatible endpoint)           │
                        └────────────────────┬─────────────────────┘
                                             │
                        ┌────────────────────▼─────────────────────┐
                        │   Response: Triage + RCA + Resolution    │
                        └──────────────────────────────────────────┘
```

## 📁 Project Structure

```
ops-assistant/
├── main.py              # FastAPI application
├── llm_client.py        # Qwen LLM client
├── rag_pipeline.py      # RAG with ChromaDB
├── ingestion.py         # Document ingestion
├── assistant.py         # Core operations assistant
├── demo.py              # Interactive demo
├── test_setup.py        # Setup verification
├── ui.html              # Web UI
├── requirements.txt     # Dependencies
├── .env                 # Configuration
└── README.md
```

## 🔧 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_BASE_URL` | Qwen API endpoint | `http://wiphack30qx5aw.cloudloka.com:8000/v1` |
| `LLM_MODEL` | Model name | `Qwen/Qwen3-8B` |
| `CHROMA_PERSIST_DIR` | Vector DB storage | `./chroma_db` |

## 🧪 Testing

```powershell
# Test LLM connectivity
python -c "from llm_client import get_llm_client; print(get_llm_client().health_check())"

# Test RAG pipeline
python -c "from rag_pipeline import get_rag_pipeline; print(get_rag_pipeline().get_stats())"
```

## 📈 Extending

### Add Custom Documents

```python
from rag_pipeline import get_rag_pipeline

rag = get_rag_pipeline()
rag.add_document(
    content="Your SOP or KB article content...",
    doc_id="sop_custom_001",
    doc_type="sop",
    metadata={"title": "Custom Runbook"}
)
```

### Customize Prompts

Edit the `SYSTEM_PROMPT` in `assistant.py` to tune the assistant's behavior.

## 📄 License

MIT License - Built for Intel Hackathon
