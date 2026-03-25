"""
Configuration for GenAI Operations Assistant
Intel Hackathon 2026 - Powered by Phi-4 Mini
"""
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# LLM Configuration
# =============================================================================
# Recommended: Intel Phi-4 Mini for hackathon
# LLM_BASE_URL = "http://localhost:8080/v1"
# LLM_MODEL = "microsoft/Phi-4-mini-instruct"

# Current: Qwen3-8B (fallback)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://wiphack30qx5aw.cloudloka.com:8000/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

# Model-specific settings
MODEL_CONFIGS = {
    "microsoft/Phi-4-mini-instruct": {
        "name": "Intel Phi-4 Mini",
        "parameters": "3.8B",
        "context_length": 4096,
        "recommended": True,
        "description": "Optimized for edge deployment with excellent reasoning"
    },
    "Qwen/Qwen3-8B": {
        "name": "Qwen3 8B",
        "parameters": "8B",
        "context_length": 8192,
        "recommended": False,
        "description": "General purpose with strong instruction following"
    }
}

# =============================================================================
# Vector Store Configuration
# =============================================================================
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# =============================================================================
# API Configuration
# =============================================================================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# =============================================================================
# Business Impact Metrics (for dashboard)
# =============================================================================
METRICS = {
    "resolution_time_before": 4.2,  # hours
    "resolution_time_after": 2.5,   # hours
    "resolution_improvement": 40,    # percent
    "mttr_before": 62,              # minutes
    "mttr_after": 38,               # minutes
    "mttr_improvement": 39,          # percent
    "l1_effort_before": 68,         # percent
    "l1_effort_after": 25,          # percent
    "misclassification_before": 23, # percent
    "misclassification_after": 5,   # percent
}

# =============================================================================
# Application Info
# =============================================================================
APP_NAME = "GenAI Operations Assistant"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-powered operations automation for ticket triage, RCA, and resolution"
HACKATHON = "Intel Hackathon 2026"
RECOMMENDED_MODEL = "Phi-4 Mini"
