"""
Configuration for GenAI Operations Assistant
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://wiphack30qx5aw.cloudloka.com:8000/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

# Vector Store Configuration
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))
