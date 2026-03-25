"""
GenAI Operations Assistant
AI-powered operations automation for ticket triage, RCA, and resolution
"""
from .assistant import OpsAssistant, get_assistant
from .llm_client import LLMClient, get_llm_client
from .rag_pipeline import RAGPipeline, get_rag_pipeline
from .ingestion import DocumentIngester, get_ingester

__version__ = "1.0.0"
__all__ = [
    "OpsAssistant",
    "get_assistant",
    "LLMClient", 
    "get_llm_client",
    "RAGPipeline",
    "get_rag_pipeline",
    "DocumentIngester",
    "get_ingester"
]
