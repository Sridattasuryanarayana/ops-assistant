"""
GenAI Operations Assistant - Complete Working Application
=========================================================
AI-powered operations automation for:
- Ticket Triage & Classification
- Root Cause Analysis (RCA)
- Resolution Recommendations
- Draft Response Generation

Uses RAG (Retrieval-Augmented Generation) with Qwen3-8B LLM
"""

import os
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Third-party imports
import httpx
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://wiphack30qx5aw.cloudloka.com:8000/v1").rstrip('/')
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")


# ============================================================================
# DATA MODELS
# ============================================================================

class TriageResult(BaseModel):
    priority: str
    category: str
    summary: str
    reasoning: str


class RCAResult(BaseModel):
    root_cause: str
    contributing_factors: List[str]
    evidence: List[str]
    confidence: str


class ResolutionResult(BaseModel):
    recommended_actions: List[str]
    draft_response: str
    similar_incidents: List[Dict[str, Any]]
    estimated_time: str
    runbook_reference: Optional[str] = None


class AnalysisResult(BaseModel):
    ticket_id: str
    triage: TriageResult
    rca: RCAResult
    resolution: ResolutionResult
    context_used: List[str]


# ============================================================================
# LLM CLIENT
# ============================================================================

class LLMClient:
    """Client for OpenAI-compatible LLM endpoints"""
    
    def __init__(self, base_url: str = LLM_BASE_URL, model: str = LLM_MODEL):
        self.base_url = base_url
        self.model = model
        self.client = httpx.Client(timeout=LLM_TIMEOUT)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate LLM response"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"LLM Error: {str(e)}")
    
    def health_check(self) -> bool:
        """Check LLM endpoint availability"""
        try:
            response = self.client.get(f"{self.base_url}/models", timeout=10)
            return response.status_code == 200
        except:
            return False


# ============================================================================
# RAG PIPELINE (Simplified In-Memory for Demo)
# ============================================================================

class SimpleRAG:
    """
    Simplified RAG implementation using keyword matching
    For production, use ChromaDB with sentence-transformers
    """
    
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self._load_sample_data()
    
    def _load_sample_data(self):
        """Load sample operational knowledge"""
        
        # Sample resolved tickets
        tickets = [
            {
                "id": "ticket_INC001234",
                "content": """Ticket ID: INC001234
Title: Database connection timeout in production
Priority: P1
Category: Database
Status: Resolved
Description: Users reporting slow response times and timeout errors. Application logs show 'Connection pool exhausted' errors. Started after deployment at 14:00 UTC.
Root Cause: Connection pool size was insufficient after traffic increase. Max connections set to 50, but peak load required 200+.
Resolution: Increased connection pool size to 300, added connection timeout settings, implemented connection health checks.""",
                "doc_type": "ticket",
                "keywords": ["database", "connection", "timeout", "pool", "exhausted"]
            },
            {
                "id": "ticket_INC001235",
                "content": """Ticket ID: INC001235
Title: Memory leak in payment service
Priority: P2
Category: Application
Status: Resolved
Description: Payment service pods restarting every 4 hours due to OOMKilled. Memory usage grows linearly over time.
Root Cause: Unclosed HTTP client connections in payment gateway integration. Each request created new client instance without cleanup.
Resolution: Implemented connection pooling for HTTP client, added proper resource cleanup in finally blocks, increased memory limits temporarily.""",
                "doc_type": "ticket",
                "keywords": ["memory", "leak", "oom", "killed", "payment", "restart"]
            },
            {
                "id": "ticket_INC001236",
                "content": """Ticket ID: INC001236
Title: High CPU usage on web servers
Priority: P2
Category: Infrastructure
Status: Resolved
Description: All web server instances showing 95%+ CPU utilization. Response times degraded. No recent deployments.
Root Cause: Regex pattern in request validation causing catastrophic backtracking on malformed input.
Resolution: Fixed regex pattern to prevent backtracking, added input length validation, implemented request timeout.""",
                "doc_type": "ticket",
                "keywords": ["cpu", "high", "utilization", "server", "regex", "slow"]
            },
            {
                "id": "ticket_INC001237",
                "content": """Ticket ID: INC001237
Title: Kafka consumer lag increasing
Priority: P2
Category: Messaging
Status: Resolved
Description: Order processing consumer group showing increasing lag. Orders not being processed within SLA.
Root Cause: Consumer instances scaled down by HPA during low traffic, unable to catch up when traffic increased.
Resolution: Adjusted HPA min replicas, implemented consumer lag-based scaling, added circuit breaker for downstream services.""",
                "doc_type": "ticket",
                "keywords": ["kafka", "consumer", "lag", "queue", "processing", "order"]
            },
            {
                "id": "ticket_INC001238",
                "content": """Ticket ID: INC001238
Title: SSL certificate expiration causing 503 errors
Priority: P1
Category: Security
Status: Resolved
Description: API gateway returning 503 errors. Users unable to access any services. Certificate expired at midnight.
Root Cause: SSL certificate auto-renewal job failed silently. No monitoring alerts configured for certificate expiry.
Resolution: Manually renewed certificate, fixed certbot configuration, added certificate expiry monitoring.""",
                "doc_type": "ticket",
                "keywords": ["ssl", "certificate", "503", "expir", "https", "gateway"]
            }
        ]
        
        # Sample SOPs/Runbooks
        sops = [
            {
                "id": "sop_database_connection",
                "content": """# Database Connection Issues Runbook

## Symptoms
- Application timeout errors
- "Connection pool exhausted" in logs
- Slow query response times

## Diagnostic Steps
1. Check database connection count: SELECT count(*) FROM pg_stat_activity;
2. Verify connection pool configuration in application
3. Check for long-running queries
4. Monitor database CPU and memory

## Resolution Steps
1. If connection count high:
   - Identify and terminate idle connections
   - Increase pool size if justified by load
2. If long-running queries:
   - Identify problematic queries
   - Add missing indexes
   - Optimize query patterns

## Prevention
- Set up alerting for connection pool utilization > 80%
- Regular query performance review
- Implement connection health checks""",
                "doc_type": "sop",
                "keywords": ["database", "connection", "pool", "query", "timeout"]
            },
            {
                "id": "sop_memory_leak",
                "content": """# Memory Leak Investigation Runbook

## Symptoms
- OOMKilled pod restarts
- Linear memory growth over time
- Garbage collection not reclaiming memory

## Diagnostic Steps
1. Enable heap dumps on OOM: -XX:+HeapDumpOnOutOfMemoryError
2. Capture heap dump before OOM threshold
3. Analyze with Eclipse MAT or similar tool
4. Check for common leak patterns:
   - Unclosed connections/streams
   - Static collections growing unboundedly
   - Event listener accumulation

## Resolution Steps
1. Identify retention path in heap dump
2. Fix resource cleanup (try-with-resources)
3. Implement proper cache eviction
4. Add memory usage monitoring

## Prevention
- Code review for resource management
- Automated leak detection in CI
- Regular load testing with memory profiling""",
                "doc_type": "sop",
                "keywords": ["memory", "leak", "oom", "heap", "garbage", "collection"]
            },
            {
                "id": "sop_high_cpu",
                "content": """# High CPU Troubleshooting Guide

## Symptoms
- CPU utilization > 80% sustained
- Increased response latency
- Request timeouts

## Diagnostic Steps
1. Identify top CPU-consuming processes: top -c
2. For JVM: thread dump analysis with jstack
3. Profile application with async-profiler
4. Check for:
   - Infinite loops
   - Regex catastrophic backtracking
   - Tight polling loops
   - GC overhead

## Resolution Steps
1. Scale horizontally if legitimate load increase
2. Fix algorithmic issues (O(n²) -> O(n log n))
3. Add caching for expensive computations
4. Implement circuit breakers

## Prevention
- Performance testing in CI/CD
- CPU alerting at 70% threshold
- Regular profiling sessions""",
                "doc_type": "sop",
                "keywords": ["cpu", "high", "performance", "thread", "profil"]
            },
            {
                "id": "sop_kafka_lag",
                "content": """# Kafka Consumer Lag Runbook

## Symptoms
- Growing consumer lag
- Messages not processed within SLA
- Consumer group rebalancing frequently

## Diagnostic Steps
1. Check consumer lag: kafka-consumer-groups --describe
2. Verify consumer health and logs
3. Check network connectivity to Kafka
4. Monitor consumer processing time per message

## Resolution Steps
1. Scale consumer instances
2. Increase consumer parallelism (partitions)
3. Optimize message processing logic
4. Add circuit breakers for downstream slow services

## Prevention
- Consumer lag alerting
- Auto-scaling based on lag metrics
- Regular capacity planning""",
                "doc_type": "sop",
                "keywords": ["kafka", "consumer", "lag", "message", "queue"]
            }
        ]
        
        # Index all documents
        for doc in tickets + sops:
            self.documents[doc["id"]] = doc
    
    def add_document(self, doc_id: str, content: str, doc_type: str, metadata: dict = None):
        """Add a document to the knowledge base"""
        keywords = self._extract_keywords(content)
        self.documents[doc_id] = {
            "id": doc_id,
            "content": content,
            "doc_type": doc_type,
            "keywords": keywords,
            "metadata": metadata or {}
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        # Count frequency
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        # Return top keywords
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:20]]
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents using keyword matching"""
        query_keywords = set(self._extract_keywords(query))
        
        scores = []
        for doc_id, doc in self.documents.items():
            doc_keywords = set(doc.get("keywords", []))
            # Calculate overlap score
            overlap = len(query_keywords & doc_keywords)
            if overlap > 0:
                scores.append((doc_id, overlap, doc))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        results = []
        for doc_id, score, doc in scores[:top_k]:
            results.append({
                "doc_id": doc_id,
                "content": doc["content"],
                "doc_type": doc["doc_type"],
                "score": score / max(len(query_keywords), 1)
            })
        
        return results
    
    def build_context(self, query: str, top_k: int = 3) -> str:
        """Build context string from retrieved documents"""
        docs = self.retrieve(query, top_k)
        if not docs:
            return "No relevant knowledge found."
        
        context_parts = []
        for doc in docs:
            context_parts.append(f"[{doc['doc_type'].upper()}]\n{doc['content']}\n---")
        
        return "\n\n".join(context_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        type_counts = {}
        for doc in self.documents.values():
            dt = doc.get("doc_type", "unknown")
            type_counts[dt] = type_counts.get(dt, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "by_type": type_counts
        }


# ============================================================================
# OPERATIONS ASSISTANT
# ============================================================================

class OpsAssistant:
    """
    GenAI-Powered Operations Automation Assistant
    
    Capabilities:
    - Ticket triage and classification
    - Root cause analysis with RAG
    - Resolution recommendations
    - Draft response generation
    """
    
    SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) and Operations specialist.
You help triage incidents, perform root cause analysis, and recommend resolutions based on
operational knowledge, past incidents, and standard operating procedures.

Be concise, technical, and actionable. Focus on:
1. Quick diagnosis based on symptoms
2. Evidence-based root cause analysis
3. Practical resolution steps
4. Prevention recommendations

Always structure your response clearly."""

    def __init__(self, llm_client: LLMClient = None, rag: SimpleRAG = None):
        self.llm = llm_client or LLMClient()
        self.rag = rag or SimpleRAG()
        print(f"[Assistant] Initialized with {self.rag.get_stats()['total_documents']} documents")
    
    def triage_ticket(self, ticket_text: str) -> TriageResult:
        """Classify and prioritize a ticket"""
        
        prompt = f"""Analyze this support ticket and provide triage information.

TICKET:
{ticket_text}

Respond in this EXACT format (one item per line):
PRIORITY: [P1/P2/P3/P4]
CATEGORY: [Database/Application/Infrastructure/Network/Security/Messaging/Unknown]
SUMMARY: [One-line summary]
REASONING: [Brief explanation]

Priority Guidelines:
- P1: System down, critical business impact
- P2: Major functionality degraded
- P3: Minor impact, workaround available
- P4: Low priority, enhancement"""

        response = self.llm.generate(prompt, self.SYSTEM_PROMPT, temperature=0.3)
        
        # Parse response
        result = {"priority": "P3", "category": "Unknown", "summary": ticket_text[:100], "reasoning": ""}
        
        for line in response.strip().split('\n'):
            line = line.strip()
            if line.startswith("PRIORITY:"):
                result["priority"] = line.split(":", 1)[1].strip()
            elif line.startswith("CATEGORY:"):
                result["category"] = line.split(":", 1)[1].strip()
            elif line.startswith("SUMMARY:"):
                result["summary"] = line.split(":", 1)[1].strip()
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.split(":", 1)[1].strip()
        
        return TriageResult(**result)
    
    def analyze_root_cause(self, ticket_text: str, logs: str = None) -> RCAResult:
        """Perform root cause analysis using RAG"""
        
        # Get relevant context from knowledge base
        context = self.rag.build_context(ticket_text, top_k=3)
        
        prompt = f"""Perform root cause analysis for this incident.

INCIDENT:
{ticket_text}

{f"LOGS:{chr(10)}{logs}" if logs else ""}

RELEVANT KNOWLEDGE BASE:
{context}

Respond in this EXACT format:
ROOT_CAUSE: [Primary root cause - one clear statement]
CONTRIBUTING_FACTORS: [factor1, factor2, factor3]
EVIDENCE: [evidence1, evidence2, evidence3]
CONFIDENCE: [High/Medium/Low]"""

        response = self.llm.generate(prompt, self.SYSTEM_PROMPT, temperature=0.4)
        
        # Parse response
        result = {
            "root_cause": "Unable to determine",
            "contributing_factors": [],
            "evidence": [],
            "confidence": "Low"
        }
        
        for line in response.strip().split('\n'):
            line = line.strip()
            if line.startswith("ROOT_CAUSE:"):
                result["root_cause"] = line.split(":", 1)[1].strip()
            elif line.startswith("CONTRIBUTING_FACTORS:"):
                factors = line.split(":", 1)[1].strip()
                result["contributing_factors"] = [f.strip() for f in factors.split(',') if f.strip()]
            elif line.startswith("EVIDENCE:"):
                evidence = line.split(":", 1)[1].strip()
                result["evidence"] = [e.strip() for e in evidence.split(',') if e.strip()]
            elif line.startswith("CONFIDENCE:"):
                result["confidence"] = line.split(":", 1)[1].strip()
        
        return RCAResult(**result)
    
    def recommend_resolution(self, ticket_text: str, root_cause: str = None) -> ResolutionResult:
        """Generate resolution recommendations"""
        
        # Get relevant SOPs and similar tickets
        docs = self.rag.retrieve(ticket_text, top_k=3)
        context = "\n\n".join([f"[{d['doc_type'].upper()}]\n{d['content']}" for d in docs])
        
        prompt = f"""Recommend resolution for this incident.

INCIDENT:
{ticket_text}

{f"ROOT CAUSE: {root_cause}" if root_cause else ""}

RELEVANT KNOWLEDGE:
{context}

Respond in this EXACT format:

ACTIONS:
1. [First action step]
2. [Second action step]
3. [Third action step]

DRAFT_RESPONSE:
[Professional response to send to the requester]

ESTIMATED_TIME: [e.g., 30 minutes, 2 hours]
RUNBOOK: [Relevant runbook name or None]"""

        response = self.llm.generate(prompt, self.SYSTEM_PROMPT, temperature=0.5)
        
        # Parse response
        result = {
            "recommended_actions": [],
            "draft_response": "",
            "similar_incidents": [{"doc_id": d["doc_id"], "score": d["score"]} for d in docs[:3]],
            "estimated_time": "Unknown",
            "runbook_reference": None
        }
        
        current_section = None
        actions = []
        draft_lines = []
        
        for line in response.strip().split('\n'):
            line_stripped = line.strip()
            
            if line_stripped.startswith("ACTIONS:"):
                current_section = "actions"
            elif line_stripped.startswith("DRAFT_RESPONSE:"):
                current_section = "draft"
            elif line_stripped.startswith("ESTIMATED_TIME:"):
                result["estimated_time"] = line_stripped.split(":", 1)[1].strip()
                current_section = None
            elif line_stripped.startswith("RUNBOOK:"):
                runbook = line_stripped.split(":", 1)[1].strip()
                result["runbook_reference"] = runbook if runbook.lower() != "none" else None
                current_section = None
            elif current_section == "actions" and line_stripped:
                # Remove numbering
                action = re.sub(r'^\d+\.\s*', '', line_stripped)
                if action:
                    actions.append(action)
            elif current_section == "draft":
                draft_lines.append(line)
        
        result["recommended_actions"] = actions
        result["draft_response"] = "\n".join(draft_lines).strip()
        
        return ResolutionResult(**result)
    
    def full_analysis(self, ticket_id: str, ticket_text: str, logs: str = None) -> AnalysisResult:
        """Complete ticket analysis: triage + RCA + resolution"""
        
        print(f"\n[Analysis] Starting analysis for {ticket_id}")
        
        # Step 1: Triage
        print("[Analysis] Step 1: Triaging ticket...")
        triage = self.triage_ticket(ticket_text)
        print(f"[Analysis] Triage complete: {triage.priority} / {triage.category}")
        
        # Step 2: Root Cause Analysis
        print("[Analysis] Step 2: Analyzing root cause...")
        rca = self.analyze_root_cause(ticket_text, logs)
        print(f"[Analysis] RCA complete: {rca.confidence} confidence")
        
        # Step 3: Resolution
        print("[Analysis] Step 3: Generating resolution...")
        resolution = self.recommend_resolution(ticket_text, rca.root_cause)
        print(f"[Analysis] Resolution complete: {len(resolution.recommended_actions)} actions")
        
        # Get context sources
        docs = self.rag.retrieve(ticket_text, top_k=3)
        context_used = [d["doc_id"] for d in docs]
        
        return AnalysisResult(
            ticket_id=ticket_id,
            triage=triage,
            rca=rca,
            resolution=resolution,
            context_used=context_used
        )
    
    def chat(self, message: str) -> str:
        """Free-form chat with RAG context"""
        context = self.rag.build_context(message, top_k=3)
        
        prompt = f"""RELEVANT KNOWLEDGE:
{context}

USER QUESTION:
{message}

Provide a helpful, technical response."""

        return self.llm.generate(prompt, self.SYSTEM_PROMPT, temperature=0.7)


# ============================================================================
# MAIN / DEMO
# ============================================================================

def run_demo():
    """Interactive demonstration of the Operations Assistant"""
    
    print("=" * 60)
    print("  GenAI Operations Assistant - Demo")
    print("  AI-Powered Ticket Triage, RCA & Resolution")
    print("=" * 60)
    
    # Initialize
    print("\n[Setup] Initializing assistant...")
    
    try:
        assistant = OpsAssistant()
    except Exception as e:
        print(f"[Error] Failed to initialize: {e}")
        return
    
    # Check LLM
    print("[Setup] Checking LLM endpoint...")
    if assistant.llm.health_check():
        print("[Setup] LLM endpoint is available ✓")
    else:
        print("[Setup] WARNING: LLM endpoint may not be available")
    
    # Demo ticket
    demo_ticket = """
    Production Alert: High latency on checkout service
    
    Severity: Critical
    Started: 10 minutes ago
    
    Symptoms:
    - Checkout API response times increased from 200ms to 5+ seconds
    - Error rate up to 15%
    - Database connection warnings in logs
    - Users reporting timeout errors during payment
    
    Recent Changes:
    - No deployments in last 24 hours
    - Traffic is normal levels
    
    Logs:
    2024-01-15 14:02:15 WARN  [checkout] DB connection pool: 48/50 connections in use
    2024-01-15 14:02:18 ERROR [checkout] Connection timeout after 30s
    2024-01-15 14:02:20 WARN  [checkout] Slow query detected: 12.5s
    """
    
    print("\n" + "=" * 60)
    print("  DEMO: Analyzing Sample Ticket")
    print("=" * 60)
    print("\n[Input Ticket]")
    print(demo_ticket)
    
    print("\n[Processing...]")
    
    try:
        result = assistant.full_analysis(
            ticket_id="DEMO-001",
            ticket_text=demo_ticket,
            logs="Connection pool exhausted, slow queries detected"
        )
        
        print("\n" + "=" * 60)
        print("  ANALYSIS RESULTS")
        print("=" * 60)
        
        # Triage
        print("\n[TRIAGE]")
        print(f"  Priority: {result.triage.priority}")
        print(f"  Category: {result.triage.category}")
        print(f"  Summary: {result.triage.summary}")
        
        # RCA
        print("\n[ROOT CAUSE ANALYSIS]")
        print(f"  Root Cause: {result.rca.root_cause}")
        print(f"  Confidence: {result.rca.confidence}")
        if result.rca.contributing_factors:
            print("  Contributing Factors:")
            for f in result.rca.contributing_factors:
                print(f"    - {f}")
        
        # Resolution
        print("\n[RECOMMENDED ACTIONS]")
        for i, action in enumerate(result.resolution.recommended_actions, 1):
            print(f"  {i}. {action}")
        
        print(f"\n  Estimated Time: {result.resolution.estimated_time}")
        if result.resolution.runbook_reference:
            print(f"  Runbook: {result.resolution.runbook_reference}")
        
        # Draft Response
        print("\n[DRAFT RESPONSE]")
        print("-" * 40)
        print(result.resolution.draft_response)
        print("-" * 40)
        
        print(f"\n[Context Sources Used]: {', '.join(result.context_used)}")
        
    except Exception as e:
        print(f"\n[Error] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("  Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
