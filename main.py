"""
FastAPI Application - Operations Assistant REST API
"""
import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Import app modules
from llm_client import get_llm_client
from rag_pipeline import get_rag_pipeline
from ingestion import DocumentIngester
from assistant import OpsAssistant, AnalysisResult, TriageResult, RCAResult, ResolutionResult

# Initialize FastAPI
app = FastAPI(
    title="GenAI Operations Assistant",
    description="AI-powered operations automation for ticket triage, RCA, and resolution",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
assistant: Optional[OpsAssistant] = None


# Request/Response Models
class TicketRequest(BaseModel):
    ticket_id: str
    title: str
    description: str
    logs: Optional[str] = None


class TriageRequest(BaseModel):
    ticket_text: str


class RCARequest(BaseModel):
    ticket_text: str
    logs: Optional[str] = None


class ResolutionRequest(BaseModel):
    ticket_text: str
    root_cause: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


class ChatResponse(BaseModel):
    response: str


class DocumentRequest(BaseModel):
    doc_id: str
    content: str
    doc_type: str = "general"
    metadata: Optional[dict] = None


class IngestResponse(BaseModel):
    success: bool
    documents_added: int
    message: str


class HealthResponse(BaseModel):
    status: str
    llm_available: bool
    documents_indexed: int


# Startup event
@app.on_event("startup")
async def startup():
    global assistant
    print("Initializing Operations Assistant...")
    
    try:
        # Initialize RAG pipeline (this loads the embedding model)
        rag = get_rag_pipeline()
        
        # Initialize assistant
        assistant = OpsAssistant()
        
        # Load sample data if empty
        if rag.get_stats()["total_documents"] == 0:
            print("Loading sample data...")
            ingester = DocumentIngester()
            sample_data = ingester.create_sample_data()
            
            all_docs = sample_data["tickets"] + sample_data["sops"]
            rag.add_documents_batch(all_docs)
            print(f"Loaded {len(all_docs)} sample documents")
        
        print("Operations Assistant ready!")
    except Exception as e:
        print(f"Warning: Startup initialization error: {e}")
        assistant = None


# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    llm = get_llm_client()
    rag = get_rag_pipeline()
    
    return HealthResponse(
        status="healthy",
        llm_available=llm.health_check(),
        documents_indexed=rag.get_stats()["total_documents"]
    )


# Ticket Analysis Endpoints
@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze_ticket(request: TicketRequest):
    """Full ticket analysis: triage + RCA + resolution"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    ticket_text = f"{request.title}\n\n{request.description}"
    
    try:
        result = assistant.full_analysis(
            ticket_id=request.ticket_id,
            ticket_text=ticket_text,
            logs=request.logs
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/triage", response_model=TriageResult)
async def triage_ticket(request: TriageRequest):
    """Classify and prioritize a ticket"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        return assistant.triage_ticket(request.ticket_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rca", response_model=RCAResult)
async def root_cause_analysis(request: RCARequest):
    """Perform root cause analysis"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        return assistant.analyze_root_cause(request.ticket_text, request.logs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/resolution", response_model=ResolutionResult)
async def recommend_resolution(request: ResolutionRequest):
    """Get resolution recommendations"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        return assistant.recommend_resolution(request.ticket_text, request.root_cause)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Free-form chat with RAG context"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        response = assistant.chat(request.message, request.context)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Knowledge Base Management
@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_document(request: DocumentRequest):
    """Add a document to the knowledge base"""
    try:
        rag = get_rag_pipeline()
        rag.add_document(
            content=request.content,
            doc_id=request.doc_id,
            doc_type=request.doc_type,
            metadata=request.metadata
        )
        return IngestResponse(
            success=True,
            documents_added=1,
            message=f"Document {request.doc_id} added successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/batch", response_model=IngestResponse)
async def ingest_batch(documents: List[DocumentRequest]):
    """Add multiple documents to the knowledge base"""
    try:
        rag = get_rag_pipeline()
        docs = [
            {
                "doc_id": d.doc_id,
                "content": d.content,
                "doc_type": d.doc_type,
                "metadata": d.metadata or {}
            }
            for d in documents
        ]
        count = rag.add_documents_batch(docs)
        return IngestResponse(
            success=True,
            documents_added=count,
            message=f"Added {count} documents"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/stats")
async def knowledge_stats():
    """Get knowledge base statistics"""
    try:
        rag = get_rag_pipeline()
        return rag.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/search")
async def search_knowledge(query: str, top_k: int = 5):
    """Search the knowledge base"""
    try:
        rag = get_rag_pipeline()
        results = rag.retrieve(query, top_k=top_k)
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Load sample data endpoint
@app.post("/api/load-samples", response_model=IngestResponse)
async def load_sample_data():
    """Load sample operational data for demo"""
    try:
        rag = get_rag_pipeline()
        ingester = DocumentIngester()
        sample_data = ingester.create_sample_data()
        
        all_docs = sample_data["tickets"] + sample_data["sops"]
        count = rag.add_documents_batch(all_docs)
        
        return IngestResponse(
            success=True,
            documents_added=count,
            message=f"Loaded {count} sample documents (tickets + SOPs)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
