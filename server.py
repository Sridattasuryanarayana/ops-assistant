"""
GenAI Operations Assistant - FastAPI REST API Server
"""
import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path

from app import OpsAssistant, SimpleRAG, LLMClient
from app import TriageResult, RCAResult, ResolutionResult, AnalysisResult

# Initialize FastAPI
api = FastAPI(
    title="GenAI Operations Assistant",
    description="AI-powered operations automation for ticket triage, RCA, and resolution",
    version="1.0.0"
)

# CORS
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global assistant instance
assistant: Optional[OpsAssistant] = None


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

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


class ChatResponse(BaseModel):
    response: str


class HealthResponse(BaseModel):
    status: str
    llm_available: bool
    documents_indexed: int


# ============================================================================
# STARTUP
# ============================================================================

@api.on_event("startup")
async def startup():
    global assistant
    print("[API] Starting GenAI Operations Assistant...")
    try:
        assistant = OpsAssistant()
        print("[API] Assistant ready!")
    except Exception as e:
        print(f"[API] Warning: {e}")


# ============================================================================
# ENDPOINTS
# ============================================================================

@api.get("/", response_class=HTMLResponse)
async def root():
    """Serve the UI"""
    ui_path = Path(__file__).parent / "ui.html"
    if ui_path.exists():
        return ui_path.read_text()
    return """
    <html>
        <body>
            <h1>GenAI Operations Assistant API</h1>
            <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
        </body>
    </html>
    """


@api.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if not assistant:
        return HealthResponse(status="initializing", llm_available=False, documents_indexed=0)
    
    return HealthResponse(
        status="healthy",
        llm_available=assistant.llm.health_check(),
        documents_indexed=assistant.rag.get_stats()["total_documents"]
    )


@api.post("/api/analyze", response_model=AnalysisResult)
async def analyze_ticket(request: TicketRequest):
    """
    Full ticket analysis: triage + RCA + resolution
    
    This is the main endpoint that performs complete ticket analysis.
    """
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


@api.post("/api/triage", response_model=TriageResult)
async def triage_ticket(request: TriageRequest):
    """Classify and prioritize a ticket"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        return assistant.triage_ticket(request.ticket_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.post("/api/rca", response_model=RCAResult)
async def root_cause_analysis(request: RCARequest):
    """Perform root cause analysis"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        return assistant.analyze_root_cause(request.ticket_text, request.logs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.post("/api/resolution", response_model=ResolutionResult)
async def recommend_resolution(request: ResolutionRequest):
    """Get resolution recommendations"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        return assistant.recommend_resolution(request.ticket_text, request.root_cause)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Free-form chat with RAG context"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        response = assistant.chat(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/api/knowledge/stats")
async def knowledge_stats():
    """Get knowledge base statistics"""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    return assistant.rag.get_stats()


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8080)
