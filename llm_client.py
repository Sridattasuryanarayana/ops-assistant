"""
LLM Client for Qwen3-8B (OpenAI-compatible endpoint)
Handles all communication with the LLM API
"""
import os
import httpx
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """
    Client for OpenAI-compatible LLM endpoints (Qwen3-8B)
    
    Supports:
    - Chat completion API
    - Streaming responses
    - Health checks
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0
    ):
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "http://wiphack30qx5aw.cloudloka.com:8000/v1")).rstrip('/')
        self.model = model or os.getenv("LLM_MODEL", "Qwen/Qwen3-8B")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
        print(f"[LLM] Initialized with endpoint: {self.base_url}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send chat completion request to the LLM endpoint
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"LLM API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"LLM connection error: {str(e)}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Simple generate interface - returns just the text response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response["choices"][0]["message"]["content"]
    
    def health_check(self) -> bool:
        """Check if the LLM endpoint is reachable"""
        try:
            url = f"{self.base_url}/models"
            response = self.client.get(url, timeout=10.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def close(self):
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the LLM client singleton"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
