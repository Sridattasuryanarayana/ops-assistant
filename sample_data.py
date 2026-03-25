"""
Sample Operational Data for GenAI Operations Assistant
Intel Hackathon 2026

This module provides sample data to demonstrate the RAG pipeline capabilities:
- SOPs (Standard Operating Procedures)
- KB Articles (Knowledge Base)
- Historical Tickets
- Log Patterns
"""

from datetime import datetime, timedelta
import random


# =============================================================================
# STANDARD OPERATING PROCEDURES (SOPs)
# =============================================================================
SAMPLE_SOPS = [
    {
        "doc_id": "SOP-DB-001",
        "doc_type": "sop",
        "title": "Database Connection Pool Exhaustion Runbook",
        "content": """
# SOP: Database Connection Pool Exhaustion

## Symptoms
- Application errors: "Connection pool exhausted"
- Increased response times (>5s)
- Database CPU normal but connections at max

## Immediate Actions
1. Check active connections: SELECT count(*) FROM pg_stat_activity;
2. Identify long-running queries: SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';
3. Kill idle connections if >80% pool utilized

## Resolution Steps
1. Scale connection pool size temporarily (+25%)
2. Identify and optimize slow queries
3. Enable connection pooling (PgBouncer) if not present
4. Set connection timeout to 30s
5. Implement connection retry logic with exponential backoff

## Prevention
- Monitor connection pool utilization (alert at 70%)
- Regular query performance review
- Connection leak detection in CI/CD

## Escalation
- If issue persists >15 mins: Page DBA on-call
- If customer impact: P1 incident declaration
""",
        "metadata": {
            "category": "Database",
            "severity": "High",
            "last_updated": "2026-03-15",
            "author": "DBA Team"
        }
    },
    {
        "doc_id": "SOP-NET-001",
        "doc_type": "sop",
        "title": "Network Latency Troubleshooting",
        "content": """
# SOP: Network Latency Investigation

## Symptoms
- API response times >2x baseline
- Intermittent timeouts between services
- TCP retransmissions in logs

## Diagnostic Steps
1. Run traceroute to affected endpoints
2. Check MTR for packet loss: mtr -rwbzc 100 <target>
3. Verify DNS resolution times
4. Check network interface stats for errors

## Common Causes
- Cross-AZ traffic congestion
- DNS resolution delays
- MTU mismatches
- Network policy blocking

## Resolution
1. If DNS: Switch to local DNS cache / reduce TTL
2. If cross-AZ: Enable endpoint affinity
3. If MTU: Set MTU to 1500 on all interfaces
4. If congestion: Scale network bandwidth

## Monitoring
- Track p99 latency between services
- Alert on >50ms inter-service latency
""",
        "metadata": {
            "category": "Network",
            "severity": "Medium",
            "last_updated": "2026-03-10",
            "author": "Network Ops"
        }
    },
    {
        "doc_id": "SOP-K8S-001",
        "doc_type": "sop",
        "title": "Kubernetes Pod OOMKilled Recovery",
        "content": """
# SOP: Kubernetes OOMKilled Pod Recovery

## Symptoms
- Pods in CrashLoopBackOff
- OOMKilled exit code (137)
- Memory usage spikes before restart

## Immediate Actions
1. kubectl describe pod <pod-name> - Check events
2. kubectl top pod <pod-name> - Current memory usage
3. kubectl logs <pod-name> --previous - Last logs before crash

## Root Cause Analysis
1. Memory leak in application code
2. Insufficient memory limits
3. JVM heap misconfiguration
4. Cache unbounded growth

## Resolution
1. Increase memory limits (+50% of current)
2. If JVM: Set -Xmx to 75% of container limit
3. Enable heap dump on OOM for analysis
4. Implement memory profiling

## Long-term Fix
- Add memory leak detection to CI
- Implement pod disruption budget
- Configure horizontal pod autoscaler
""",
        "metadata": {
            "category": "Kubernetes",
            "severity": "High",
            "last_updated": "2026-03-20",
            "author": "Platform Team"
        }
    },
    {
        "doc_id": "SOP-AUTH-001",
        "doc_type": "sop",
        "title": "Authentication Service Failure",
        "content": """
# SOP: Authentication Service Outage

## Symptoms
- Users cannot login
- 401/403 errors across services
- Token validation failures

## Immediate Actions
1. Check auth service health endpoint
2. Verify Redis/session store connectivity
3. Check certificate expiration
4. Validate IdP (SAML/OIDC) connectivity

## Resolution Steps
1. If Redis down: Failover to replica
2. If cert expired: Deploy new cert (emergency rotation)
3. If IdP unreachable: Enable local auth fallback
4. Clear auth cache if token corruption

## Customer Communication
"We are experiencing authentication issues affecting login. Our team is actively working on resolution. ETA: [X] minutes."

## Prevention
- Certificate expiry monitoring (30-day alert)
- Redis cluster with automatic failover
- Auth service redundancy (multi-region)
""",
        "metadata": {
            "category": "Security",
            "severity": "Critical",
            "last_updated": "2026-03-18",
            "author": "Security Ops"
        }
    },
    {
        "doc_id": "SOP-PERF-001",
        "doc_type": "sop",
        "title": "High CPU Utilization Response",
        "content": """
# SOP: High CPU Investigation

## Symptoms
- CPU utilization >85% sustained
- Increased response latency
- Request queue buildup

## Diagnostic Commands
1. top -c - Identify high CPU processes
2. perf top - Kernel-level profiling
3. htop - Interactive process view
4. pidstat 1 5 - Per-process CPU stats

## Common Causes
- Runaway process/infinite loop
- Cryptomining malware
- Log parsing overhead
- Regex catastrophic backtracking
- GC thrashing

## Resolution
1. Identify process: ps aux --sort=-%cpu | head
2. If malware: Isolate host, scan, rebuild
3. If application: Restart with profiling enabled
4. Scale horizontally if legitimate load

## Escalation
- >95% for 5 mins: Page on-call
- Security concern: Page SecOps
""",
        "metadata": {
            "category": "Performance",
            "severity": "High",
            "last_updated": "2026-03-12",
            "author": "SRE Team"
        }
    }
]


# =============================================================================
# KNOWLEDGE BASE ARTICLES
# =============================================================================
SAMPLE_KB_ARTICLES = [
    {
        "doc_id": "KB-001",
        "doc_type": "kb_article",
        "title": "Common HTTP Status Codes and Troubleshooting",
        "content": """
# HTTP Status Codes Reference

## Client Errors (4xx)
- **400 Bad Request**: Invalid request syntax. Check request body/headers.
- **401 Unauthorized**: Authentication required. Verify credentials/tokens.
- **403 Forbidden**: Access denied. Check permissions/roles.
- **404 Not Found**: Resource doesn't exist. Verify URL/endpoint.
- **429 Too Many Requests**: Rate limited. Implement backoff.

## Server Errors (5xx)
- **500 Internal Server Error**: Application crash. Check logs.
- **502 Bad Gateway**: Upstream service unavailable. Check backend health.
- **503 Service Unavailable**: Service overloaded. Scale or wait.
- **504 Gateway Timeout**: Upstream timeout. Increase timeout or optimize.

## Troubleshooting Steps
1. Check application logs for stack traces
2. Verify service health endpoints
3. Test with curl -v for headers
4. Check load balancer configuration
""",
        "metadata": {"category": "General", "views": 1523}
    },
    {
        "doc_id": "KB-002",
        "doc_type": "kb_article",
        "title": "AWS EC2 Instance Troubleshooting",
        "content": """
# EC2 Troubleshooting Guide

## Instance Not Reachable
1. Check security group allows inbound traffic
2. Verify NACL rules
3. Confirm instance is running (not stopped/terminated)
4. Check system status checks in AWS console

## High CPU/Memory
1. Connect via SSM Session Manager (if SSH unavailable)
2. Check CloudWatch metrics
3. Review process list with top/htop
4. Consider instance type upgrade

## Disk Full
1. Check with df -h
2. Find large files: du -sh /* | sort -hr
3. Clean logs: journalctl --vacuum-time=2d
4. Expand EBS volume if needed
""",
        "metadata": {"category": "Cloud", "views": 892}
    },
    {
        "doc_id": "KB-003",
        "doc_type": "kb_article",
        "title": "Docker Container Debugging",
        "content": """
# Docker Container Debugging

## Container Won't Start
1. docker logs <container> - Check startup errors
2. docker inspect <container> - View configuration
3. Verify image exists: docker images
4. Check resource limits (memory/CPU)

## Container Crashes Immediately
1. Run interactively: docker run -it <image> /bin/sh
2. Check entrypoint script
3. Verify environment variables
4. Check file permissions

## Network Issues
1. docker network ls - List networks
2. docker exec <container> ping <target> - Test connectivity
3. Check port mappings: docker port <container>
4. Verify DNS: docker exec <container> nslookup <host>
""",
        "metadata": {"category": "Containers", "views": 2341}
    },
    {
        "doc_id": "KB-004",
        "doc_type": "kb_article",
        "title": "SSL/TLS Certificate Issues",
        "content": """
# SSL Certificate Troubleshooting

## Certificate Expired
- Check expiry: openssl s_client -connect host:443 | openssl x509 -noout -dates
- Renew via cert manager or manual process
- Update in load balancer/ingress

## Certificate Chain Issues
- Verify chain: openssl verify -CAfile ca.crt cert.crt
- Ensure intermediate certs included
- Check certificate order (leaf → intermediate → root)

## Common Errors
- "Certificate not trusted": Missing CA in trust store
- "Hostname mismatch": Wrong CN/SAN in certificate
- "Handshake failed": Protocol mismatch (TLS version)

## Prevention
- Use cert-manager for auto-renewal
- Monitor expiry 30 days in advance
- Test certificates in staging first
""",
        "metadata": {"category": "Security", "views": 1876}
    },
    {
        "doc_id": "KB-005",
        "doc_type": "kb_article",
        "title": "Database Query Optimization",
        "content": """
# Query Optimization Best Practices

## Identifying Slow Queries
- PostgreSQL: pg_stat_statements extension
- MySQL: slow_query_log
- Monitor query execution time >100ms

## Common Issues
1. Missing indexes on WHERE/JOIN columns
2. SELECT * instead of specific columns
3. N+1 query patterns
4. Large OFFSET pagination

## Solutions
1. Add composite indexes for common queries
2. Use EXPLAIN ANALYZE to understand plan
3. Implement query caching
4. Use cursor-based pagination

## Index Guidelines
- Index columns used in WHERE, JOIN, ORDER BY
- Avoid over-indexing (impacts write performance)
- Consider partial indexes for filtered queries
""",
        "metadata": {"category": "Database", "views": 3102}
    },
    {
        "doc_id": "KB-006",
        "doc_type": "kb_article",
        "title": "Kubernetes Deployment Rollback",
        "content": """
# Kubernetes Rollback Procedures

## Quick Rollback
kubectl rollout undo deployment/<name>

## Rollback to Specific Revision
1. View history: kubectl rollout history deployment/<name>
2. Rollback: kubectl rollout undo deployment/<name> --to-revision=<N>

## Verify Rollback
1. kubectl rollout status deployment/<name>
2. kubectl get pods -l app=<name>
3. Check application logs

## Best Practices
- Keep revisionHistoryLimit >= 5
- Test rollback in staging
- Document deployment versions
- Use GitOps for audit trail
""",
        "metadata": {"category": "Kubernetes", "views": 2567}
    },
    {
        "doc_id": "KB-007",
        "doc_type": "kb_article",
        "title": "Memory Leak Detection",
        "content": """
# Memory Leak Investigation

## Symptoms
- Gradual memory increase over time
- OOMKilled after hours/days of runtime
- Performance degradation

## Detection Tools
- Java: jmap, VisualVM, JProfiler
- Node.js: --inspect, clinic.js
- Python: memory_profiler, tracemalloc
- Go: pprof

## Analysis Steps
1. Capture heap dump at regular intervals
2. Compare object counts between dumps
3. Identify growing collections/caches
4. Check for unclosed resources

## Common Causes
- Unbounded caches
- Event listener accumulation
- Global variable growth
- Connection/resource leaks
""",
        "metadata": {"category": "Performance", "views": 1934}
    },
    {
        "doc_id": "KB-008",
        "doc_type": "kb_article",
        "title": "API Rate Limiting Implementation",
        "content": """
# Rate Limiting Best Practices

## Common Algorithms
- Token Bucket: Smooth with burst allowance
- Fixed Window: Simple but edge-case spikes
- Sliding Window: Accurate but memory intensive

## Implementation
1. Use Redis for distributed rate limiting
2. Return 429 with Retry-After header
3. Implement client-side retry with backoff

## Recommended Limits
- Public API: 100 req/min per IP
- Authenticated: 1000 req/min per user
- Admin: 5000 req/min

## Response Headers
- X-RateLimit-Limit: Max requests
- X-RateLimit-Remaining: Requests left
- X-RateLimit-Reset: Reset timestamp
""",
        "metadata": {"category": "API", "views": 1456}
    }
]


# =============================================================================
# HISTORICAL INCIDENTS
# =============================================================================
def generate_sample_tickets():
    """Generate sample historical tickets with realistic data"""
    base_date = datetime(2026, 3, 25)
    
    tickets = [
        {
            "doc_id": "INC-2026-0315-001",
            "doc_type": "ticket",
            "title": "Payment Gateway Timeout - 15% Transaction Failures",
            "content": """
Ticket ID: INC-2026-0315-001
Priority: P1 - Critical
Status: Resolved
Created: 2026-03-15 14:30:00 UTC
Resolved: 2026-03-15 16:45:00 UTC
Resolution Time: 2h 15m

DESCRIPTION:
Starting at 14:30 UTC, customers reported failed payment transactions. Error rate spiked from 0.1% to 15%. Approximately 2,000 customers affected. Payment gateway timeouts observed in logs.

LOGS:
2026-03-15 14:32:15 ERROR [PaymentService] Gateway timeout after 30000ms
2026-03-15 14:33:22 WARN [CircuitBreaker] Circuit OPEN for payment-gateway
2026-03-15 14:35:00 ERROR [PaymentService] 500 errors: 342 in last 5 minutes

ROOT CAUSE:
Payment gateway provider experiencing infrastructure issues. Their API response times increased from 200ms to 30s+ causing our circuit breaker to trip.

RESOLUTION:
1. Engaged payment gateway support (ticket #PG-89234)
2. Temporarily increased timeout to 45s
3. Enabled fallback to secondary payment processor
4. Gateway provider resolved their issue at 16:30 UTC
5. Restored primary gateway, monitored for stability

LESSONS LEARNED:
- Implement automatic failover to backup payment processor
- Add payment gateway latency to monitoring dashboard
""",
            "metadata": {
                "priority": "P1",
                "category": "Payment",
                "resolution_time_hours": 2.25,
                "customers_affected": 2000
            }
        },
        {
            "doc_id": "INC-2026-0318-002",
            "doc_type": "ticket",
            "title": "Database Connection Pool Exhausted - API Errors",
            "content": """
Ticket ID: INC-2026-0318-002
Priority: P2 - High
Status: Resolved
Created: 2026-03-18 09:15:00 UTC
Resolved: 2026-03-18 10:30:00 UTC
Resolution Time: 1h 15m

DESCRIPTION:
API returning 500 errors with "Connection pool exhausted" message. 40% of API requests failing. Started after 9:00 AM traffic spike.

LOGS:
2026-03-18 09:15:33 ERROR [HikariPool] Connection pool exhausted
2026-03-18 09:16:00 WARN [QueryExecutor] Waiting for connection: 5000ms
2026-03-18 09:18:00 ERROR [API] 500 Internal Server Error - DB connection failed

ROOT CAUSE:
Marketing campaign launched causing 3x normal traffic. Connection pool sized for normal load (50 connections) was insufficient.

RESOLUTION:
1. Increased connection pool from 50 to 100
2. Killed long-running idle connections
3. Optimized slow query identified in logs (12s → 200ms)
4. Added connection pool monitoring alert

PREVENTION:
- Coordinate with marketing on campaign launches
- Implement auto-scaling for database connections
- Add load testing to release process
""",
            "metadata": {
                "priority": "P2",
                "category": "Database",
                "resolution_time_hours": 1.25,
                "customers_affected": 500
            }
        },
        {
            "doc_id": "INC-2026-0320-003",
            "doc_type": "ticket",
            "title": "Kubernetes Pods CrashLoopBackOff - Payment Service",
            "content": """
Ticket ID: INC-2026-0320-003
Priority: P1 - Critical
Status: Resolved
Created: 2026-03-20 03:45:00 UTC
Resolved: 2026-03-20 05:00:00 UTC
Resolution Time: 1h 15m

DESCRIPTION:
Payment service pods in CrashLoopBackOff state. All 5 replicas crashing repeatedly. No payment processing capability. Started at 03:45 UTC during low-traffic period.

LOGS:
2026-03-20 03:45:22 ERROR Exit code 137 - OOMKilled
2026-03-20 03:46:00 INFO Pod payment-service-7d9f8b6c4-x2k9j restarting
2026-03-20 03:48:00 ERROR Memory usage: 7.8GB / 8GB limit

ROOT CAUSE:
Memory leak in payment service. Batch job processing accumulated objects in memory without releasing. Memory grew from 2GB to 8GB over 12 hours until OOM.

RESOLUTION:
1. Increased memory limit to 12GB temporarily
2. Identified memory leak in batch processor
3. Deployed hotfix: Clear batch cache after processing
4. Scaled to 8 replicas for stability

PREVENTION:
- Add memory profiling to CI/CD
- Implement memory usage alerting at 70%
- Code review for memory management
""",
            "metadata": {
                "priority": "P1",
                "category": "Kubernetes",
                "resolution_time_hours": 1.25,
                "customers_affected": 0
            }
        },
        {
            "doc_id": "INC-2026-0322-004",
            "doc_type": "ticket",
            "title": "SSL Certificate Expired - API Unavailable",
            "content": """
Ticket ID: INC-2026-0322-004
Priority: P1 - Critical
Status: Resolved
Created: 2026-03-22 00:01:00 UTC
Resolved: 2026-03-22 00:45:00 UTC
Resolution Time: 44m

DESCRIPTION:
API returning SSL errors at midnight. All HTTPS requests failing with "certificate expired" error. Complete service outage.

LOGS:
2026-03-22 00:01:00 ERROR SSL handshake failed: certificate expired
2026-03-22 00:01:05 ERROR [nginx] SSL_do_handshake() failed

ROOT CAUSE:
SSL certificate for api.example.com expired at midnight UTC. Certificate renewal reminder emails went to departed employee.

RESOLUTION:
1. Generated new certificate via Let's Encrypt
2. Deployed to nginx load balancer
3. Verified SSL with openssl s_client
4. Updated certificate renewal contacts

PREVENTION:
- Moved to cert-manager for auto-renewal
- Added certificate expiry to monitoring (30-day warning)
- Created shared alias for cert notifications
""",
            "metadata": {
                "priority": "P1",
                "category": "Security",
                "resolution_time_hours": 0.73,
                "customers_affected": 5000
            }
        },
        {
            "doc_id": "INC-2026-0323-005",
            "doc_type": "ticket",
            "title": "High CPU on Web Servers - Slow Response Times",
            "content": """
Ticket ID: INC-2026-0323-005
Priority: P2 - High
Status: Resolved
Created: 2026-03-23 11:30:00 UTC
Resolved: 2026-03-23 12:15:00 UTC
Resolution Time: 45m

DESCRIPTION:
Web servers showing 95%+ CPU utilization. Page load times increased from 500ms to 8s. 20% of requests timing out.

LOGS:
2026-03-23 11:30:00 WARN CPU usage: 95%
2026-03-23 11:31:00 ERROR Request timeout after 30s
2026-03-23 11:32:00 INFO Process 'image-resize' consuming 80% CPU

ROOT CAUSE:
Image processing job running on web servers instead of worker nodes. Large batch of images uploaded by customer overwhelmed CPU.

RESOLUTION:
1. Killed runaway image processing jobs
2. Moved image processing to dedicated worker queue
3. Added CPU throttling for batch jobs
4. Implemented job queue with rate limiting

PREVENTION:
- Separate compute-heavy jobs from web servers
- CPU usage alerting per process type
- Resource quotas for batch processing
""",
            "metadata": {
                "priority": "P2",
                "category": "Performance",
                "resolution_time_hours": 0.75,
                "customers_affected": 1000
            }
        }
    ]
    
    return tickets


# =============================================================================
# LOG PATTERNS
# =============================================================================
SAMPLE_LOG_PATTERNS = [
    {
        "doc_id": "LOG-PAT-001",
        "doc_type": "log_pattern",
        "title": "Connection Pool Exhausted Pattern",
        "content": """
Pattern: Connection pool exhausted
Regex: (Connection pool exhausted|HikariPool.*exhausted|No available connections)
Severity: High
Category: Database

Common Causes:
- Too many concurrent requests
- Connection leaks (connections not returned to pool)
- Long-running queries holding connections
- Undersized connection pool

Related SOPs: SOP-DB-001
""",
        "metadata": {"severity": "high", "category": "database"}
    },
    {
        "doc_id": "LOG-PAT-002",
        "doc_type": "log_pattern",
        "title": "OOMKilled Pattern",
        "content": """
Pattern: Out of Memory Kill
Regex: (OOMKilled|exit code 137|Cannot allocate memory|OutOfMemoryError)
Severity: Critical
Category: Kubernetes/Memory

Common Causes:
- Memory leak in application
- Insufficient memory limits
- JVM heap misconfiguration
- Large data processing in memory

Related SOPs: SOP-K8S-001
""",
        "metadata": {"severity": "critical", "category": "kubernetes"}
    },
    {
        "doc_id": "LOG-PAT-003",
        "doc_type": "log_pattern",
        "title": "SSL Certificate Error Pattern",
        "content": """
Pattern: SSL/TLS Certificate Issues
Regex: (certificate expired|SSL handshake failed|unable to verify|CERT_HAS_EXPIRED)
Severity: Critical
Category: Security

Common Causes:
- Certificate expiration
- Missing intermediate certificates
- Hostname mismatch
- Trust store issues

Related SOPs: SOP-AUTH-001
Related KB: KB-004
""",
        "metadata": {"severity": "critical", "category": "security"}
    },
    {
        "doc_id": "LOG-PAT-004",
        "doc_type": "log_pattern",
        "title": "Circuit Breaker Pattern",
        "content": """
Pattern: Circuit Breaker Triggered
Regex: (Circuit (breaker )?OPEN|CircuitBreaker.*OPEN|fallback triggered)
Severity: High
Category: Resilience

Indicates: Downstream service experiencing failures
Threshold: Usually >50% failure rate in window

Action Required:
- Check downstream service health
- Review recent deployments
- Verify network connectivity
""",
        "metadata": {"severity": "high", "category": "resilience"}
    },
    {
        "doc_id": "LOG-PAT-005",
        "doc_type": "log_pattern",
        "title": "Rate Limit Exceeded Pattern",
        "content": """
Pattern: Rate Limiting
Regex: (rate limit|429 Too Many Requests|throttled|quota exceeded)
Severity: Medium
Category: API

Common Causes:
- Client making too many requests
- Retry storms
- Misconfigured client

Resolution:
- Implement exponential backoff
- Check X-RateLimit headers
- Review client request patterns
""",
        "metadata": {"severity": "medium", "category": "api"}
    }
]


# =============================================================================
# DATA LOADER
# =============================================================================
def load_sample_data():
    """
    Load all sample data into the RAG pipeline.
    Call this function to initialize the knowledge base with sample data.
    """
    from rag_pipeline import RAGPipeline
    
    print("=" * 60)
    print("Loading Sample Operational Data")
    print("Intel Hackathon 2026 - GenAI Operations Assistant")
    print("=" * 60)
    
    rag = RAGPipeline()
    
    # Load SOPs
    print("\n📋 Loading SOPs...")
    for sop in SAMPLE_SOPS:
        rag.add_document(
            content=sop["content"],
            doc_id=sop["doc_id"],
            doc_type=sop["doc_type"],
            metadata=sop["metadata"]
        )
        print(f"   ✓ {sop['doc_id']}: {sop['title']}")
    
    # Load KB Articles
    print("\n📚 Loading Knowledge Base Articles...")
    for kb in SAMPLE_KB_ARTICLES:
        rag.add_document(
            content=kb["content"],
            doc_id=kb["doc_id"],
            doc_type=kb["doc_type"],
            metadata=kb["metadata"]
        )
        print(f"   ✓ {kb['doc_id']}: {kb['title']}")
    
    # Load Historical Tickets
    print("\n🎫 Loading Historical Tickets...")
    tickets = generate_sample_tickets()
    for ticket in tickets:
        rag.add_document(
            content=ticket["content"],
            doc_id=ticket["doc_id"],
            doc_type=ticket["doc_type"],
            metadata=ticket["metadata"]
        )
        print(f"   ✓ {ticket['doc_id']}: {ticket['title']}")
    
    # Load Log Patterns
    print("\n📊 Loading Log Patterns...")
    for pattern in SAMPLE_LOG_PATTERNS:
        rag.add_document(
            content=pattern["content"],
            doc_id=pattern["doc_id"],
            doc_type=pattern["doc_type"],
            metadata=pattern["metadata"]
        )
        print(f"   ✓ {pattern['doc_id']}: {pattern['title']}")
    
    # Summary
    stats = rag.get_stats()
    print("\n" + "=" * 60)
    print("✅ Sample Data Loaded Successfully!")
    print(f"   Total Documents: {stats['total_documents']}")
    print("=" * 60)
    
    return stats


def get_sample_ticket_for_demo():
    """Return a sample ticket for testing/demo purposes"""
    return {
        "ticket_id": "INC-2026-0325-DEMO",
        "title": "Database Connection Timeout - Multiple Services Affected",
        "description": """
Since 14:00 UTC today, multiple services are experiencing database connection issues.
Order service, inventory service, and payment service all reporting timeouts.
Error rate increased from 0.5% to 25% across affected services.
Approximately 3,000 customers impacted in the last hour.
Database server CPU is at 30% (normal), but connection count is at 95% capacity.
        """,
        "logs": """
2026-03-25 14:02:15 ERROR [OrderService] Database connection timeout after 30000ms
2026-03-25 14:02:18 WARN [HikariPool-1] Connection pool exhausted, waiting for available connection
2026-03-25 14:02:45 ERROR [InventoryService] Failed to acquire connection in 30000 ms
2026-03-25 14:03:00 ERROR [PaymentService] java.sql.SQLException: Connection pool exhausted
2026-03-25 14:03:15 WARN [QueryLogger] Slow query detected: 12.5s - SELECT * FROM orders WHERE...
        """
    }


if __name__ == "__main__":
    load_sample_data()
