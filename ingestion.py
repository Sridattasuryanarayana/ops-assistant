"""
Document Ingestion Module
Handles loading and processing of tickets, logs, SOPs, and knowledge base articles
"""
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Generator
from datetime import datetime


class DocumentIngester:
    """
    Ingests operational documents from various sources:
    - Tickets (JSON, CSV)
    - Logs (plain text, structured)
    - SOPs (Markdown, text)
    - Knowledge Base articles
    """
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
    
    def load_tickets_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load tickets from a JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        tickets = data if isinstance(data, list) else data.get("tickets", [])
        
        for ticket in tickets:
            # Build document content from ticket fields
            content_parts = [
                f"Ticket ID: {ticket.get('id', 'N/A')}",
                f"Title: {ticket.get('title', ticket.get('subject', 'N/A'))}",
                f"Priority: {ticket.get('priority', 'N/A')}",
                f"Category: {ticket.get('category', 'N/A')}",
                f"Status: {ticket.get('status', 'N/A')}",
                f"Description: {ticket.get('description', '')}",
            ]
            
            if ticket.get('resolution'):
                content_parts.append(f"Resolution: {ticket['resolution']}")
            
            if ticket.get('root_cause'):
                content_parts.append(f"Root Cause: {ticket['root_cause']}")
            
            documents.append({
                "doc_id": f"ticket_{ticket.get('id', len(documents))}",
                "content": "\n".join(content_parts),
                "doc_type": "ticket",
                "metadata": {
                    "priority": ticket.get('priority'),
                    "category": ticket.get('category'),
                    "status": ticket.get('status'),
                    "created_at": ticket.get('created_at')
                }
            })
        
        return documents
    
    def load_logs(self, file_path: str, chunk_size: int = 50) -> List[Dict[str, Any]]:
        """
        Load log files and chunk them for processing
        
        Args:
            file_path: Path to log file
            chunk_size: Number of lines per chunk
        """
        documents = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Chunk logs
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]
            chunk_text = "".join(chunk)
            
            # Extract patterns from logs
            errors = re.findall(r'(?:ERROR|CRITICAL|FATAL)[:\s].*', chunk_text, re.IGNORECASE)
            warnings = re.findall(r'WARNING[:\s].*', chunk_text, re.IGNORECASE)
            
            documents.append({
                "doc_id": f"log_{Path(file_path).stem}_{i}",
                "content": chunk_text,
                "doc_type": "log",
                "metadata": {
                    "source_file": str(file_path),
                    "line_start": i,
                    "line_end": i + len(chunk),
                    "error_count": len(errors),
                    "warning_count": len(warnings)
                }
            })
        
        return documents
    
    def load_sop(self, file_path: str) -> Dict[str, Any]:
        """Load a Standard Operating Procedure document"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from markdown if present
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else Path(file_path).stem
        
        return {
            "doc_id": f"sop_{Path(file_path).stem}",
            "content": content,
            "doc_type": "sop",
            "metadata": {
                "title": title,
                "source_file": str(file_path)
            }
        }
    
    def load_directory(
        self,
        directory: str,
        doc_type: str = "general",
        extensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load all documents from a directory
        
        Args:
            directory: Path to directory
            doc_type: Type to assign to documents
            extensions: File extensions to include (e.g., ['.txt', '.md'])
        """
        extensions = extensions or ['.txt', '.md', '.json', '.log']
        documents = []
        
        dir_path = Path(directory)
        if not dir_path.exists():
            return documents
        
        for file_path in dir_path.glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                if file_path.suffix.lower() == '.json':
                    # Try to load as tickets
                    try:
                        docs = self.load_tickets_from_json(str(file_path))
                        documents.extend(docs)
                    except Exception:
                        pass
                elif file_path.suffix.lower() == '.log':
                    docs = self.load_logs(str(file_path))
                    documents.extend(docs)
                else:
                    # Load as text document
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    documents.append({
                        "doc_id": f"{doc_type}_{file_path.stem}",
                        "content": content,
                        "doc_type": doc_type,
                        "metadata": {
                            "source_file": str(file_path),
                            "loaded_at": datetime.now().isoformat()
                        }
                    })
        
        return documents
    
    def create_sample_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate sample operational data for demo purposes"""
        
        # Sample tickets
        tickets = [
            {
                "id": "INC001234",
                "title": "Database connection timeout in production",
                "priority": "P1",
                "category": "Database",
                "status": "Resolved",
                "description": "Users reporting slow response times and timeout errors. Application logs show 'Connection pool exhausted' errors. Started after deployment at 14:00 UTC.",
                "root_cause": "Connection pool size was insufficient after traffic increase. Max connections set to 50, but peak load required 200+.",
                "resolution": "Increased connection pool size to 300, added connection timeout settings, implemented connection health checks."
            },
            {
                "id": "INC001235",
                "title": "Memory leak in payment service",
                "priority": "P2",
                "category": "Application",
                "status": "Resolved",
                "description": "Payment service pods restarting every 4 hours due to OOMKilled. Memory usage grows linearly over time.",
                "root_cause": "Unclosed HTTP client connections in payment gateway integration. Each request created new client instance without cleanup.",
                "resolution": "Implemented connection pooling for HTTP client, added proper resource cleanup in finally blocks, increased memory limits temporarily."
            },
            {
                "id": "INC001236",
                "title": "SSL certificate expiration warning",
                "priority": "P3",
                "category": "Security",
                "status": "Open",
                "description": "Monitoring alert: SSL certificate for api.example.com expires in 7 days. Need to renew before expiration.",
                "root_cause": "Certificate renewal automation failed due to DNS challenge verification timeout.",
                "resolution": "Manually renewed certificate, fixed certbot configuration for DNS provider."
            },
            {
                "id": "INC001237",
                "title": "High CPU usage on web servers",
                "priority": "P2",
                "category": "Infrastructure",
                "status": "Resolved",
                "description": "All web server instances showing 95%+ CPU utilization. Response times degraded. No recent deployments.",
                "root_cause": "Regex pattern in request validation causing catastrophic backtracking on malformed input.",
                "resolution": "Fixed regex pattern to prevent backtracking, added input length validation, implemented request timeout."
            },
            {
                "id": "INC001238",
                "title": "Kafka consumer lag increasing",
                "priority": "P2",
                "category": "Messaging",
                "status": "Resolved",
                "description": "Order processing consumer group showing increasing lag. Orders not being processed within SLA.",
                "root_cause": "Consumer instances scaled down by HPA during low traffic, unable to catch up when traffic increased.",
                "resolution": "Adjusted HPA min replicas, implemented consumer lag-based scaling, added circuit breaker for downstream services."
            }
        ]
        
        # Sample SOPs
        sops = [
            {
                "title": "Database Connection Issues Runbook",
                "content": """# Database Connection Issues Runbook

## Symptoms
- Application timeout errors
- "Connection pool exhausted" in logs
- Slow query response times

## Diagnostic Steps
1. Check database connection count: `SELECT count(*) FROM pg_stat_activity;`
2. Verify connection pool configuration in application
3. Check for long-running queries: `SELECT * FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;`
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
- Set up alerting for connection pool utilization
- Regular query performance review
- Implement connection health checks
"""
            },
            {
                "title": "Memory Leak Investigation Runbook",
                "content": """# Memory Leak Investigation Runbook

## Symptoms
- OOMKilled pod restarts
- Linear memory growth over time
- Garbage collection not reclaiming memory

## Diagnostic Steps
1. Enable heap dumps on OOM: `-XX:+HeapDumpOnOutOfMemoryError`
2. Capture heap dump before OOM
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
- Automated memory leak detection in CI
- Regular load testing with memory profiling
"""
            },
            {
                "title": "High CPU Troubleshooting Guide",
                "content": """# High CPU Troubleshooting Guide

## Symptoms
- CPU utilization > 80% sustained
- Increased response latency
- Request timeouts

## Diagnostic Steps
1. Identify top CPU-consuming processes: `top -c`
2. For JVM: thread dump analysis `jstack <pid>`
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
- Regular profiling sessions
"""
            }
        ]
        
        return {
            "tickets": [
                {
                    "doc_id": f"ticket_{t['id']}",
                    "content": f"Ticket ID: {t['id']}\nTitle: {t['title']}\nPriority: {t['priority']}\nCategory: {t['category']}\nStatus: {t['status']}\nDescription: {t['description']}\nRoot Cause: {t['root_cause']}\nResolution: {t['resolution']}",
                    "doc_type": "ticket",
                    "metadata": {"priority": t['priority'], "category": t['category']}
                }
                for t in tickets
            ],
            "sops": [
                {
                    "doc_id": f"sop_{sop['title'].lower().replace(' ', '_')}",
                    "content": sop['content'],
                    "doc_type": "sop",
                    "metadata": {"title": sop['title']}
                }
                for sop in sops
            ]
        }


# Convenience function
def get_ingester() -> DocumentIngester:
    return DocumentIngester()
