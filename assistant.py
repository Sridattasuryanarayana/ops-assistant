"""
Operations Assistant - Core Intelligence
Handles ticket triage, RCA, and resolution recommendations using RAG + LLM
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
from llm_client import get_llm_client, LLMClient
from rag_pipeline import get_rag_pipeline, RAGPipeline


class TicketPriority(str, Enum):
    P1 = "P1"  # Critical - System down
    P2 = "P2"  # High - Major functionality impacted
    P3 = "P3"  # Medium - Minor functionality impacted
    P4 = "P4"  # Low - Cosmetic or enhancement


class TicketCategory(str, Enum):
    DATABASE = "Database"
    APPLICATION = "Application"
    INFRASTRUCTURE = "Infrastructure"
    NETWORK = "Network"
    SECURITY = "Security"
    MESSAGING = "Messaging"
    UNKNOWN = "Unknown"


class TriageResult(BaseModel):
    priority: str
    category: str
    summary: str
    reasoning: str


class RCAResult(BaseModel):
    root_cause: str
    contributing_factors: List[str]
    evidence: List[str]
    confidence: str  # High, Medium, Low


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


class OpsAssistant:
    """
    GenAI-Powered Operations Automation Assistant
    
    Capabilities:
    - Ticket triage and classification
    - Root cause analysis
    - Resolution recommendations
    - Draft response generation
    """
    
    SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) and Operations specialist. 
You help triage incidents, perform root cause analysis, and recommend resolutions based on 
operational knowledge, past incidents, and standard operating procedures.

Be concise, technical, and actionable in your responses. Focus on:
1. Quick diagnosis based on symptoms
2. Evidence-based root cause analysis
3. Practical resolution steps
4. Prevention recommendations

Always structure your analysis clearly and cite relevant past incidents or SOPs when available."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        rag_pipeline: Optional[RAGPipeline] = None
    ):
        self.llm = llm_client or get_llm_client()
        self.rag = rag_pipeline or get_rag_pipeline()
    
    def triage_ticket(self, ticket_text: str) -> TriageResult:
        """
        Classify and prioritize an incoming ticket
        
        Args:
            ticket_text: Raw ticket description/title
        
        Returns:
            TriageResult with priority, category, and reasoning
        """
        prompt = f"""Analyze this support ticket and provide triage information.

TICKET:
{ticket_text}

Respond in this exact format:
PRIORITY: [P1/P2/P3/P4]
CATEGORY: [Database/Application/Infrastructure/Network/Security/Messaging/Unknown]
SUMMARY: [One-line summary of the issue]
REASONING: [Brief explanation of priority and category assignment]

Priority Guidelines:
- P1: System down, critical business impact, data loss risk
- P2: Major functionality impacted, degraded service
- P3: Minor functionality impacted, workaround available
- P4: Cosmetic issues, enhancements, questions"""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.3
        )
        
        # Parse response
        lines = response.strip().split('\n')
        result = {
            "priority": "P3",
            "category": "Unknown",
            "summary": ticket_text[:100],
            "reasoning": ""
        }
        
        for line in lines:
            if line.startswith("PRIORITY:"):
                result["priority"] = line.replace("PRIORITY:", "").strip()
            elif line.startswith("CATEGORY:"):
                result["category"] = line.replace("CATEGORY:", "").strip()
            elif line.startswith("SUMMARY:"):
                result["summary"] = line.replace("SUMMARY:", "").strip()
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.replace("REASONING:", "").strip()
        
        return TriageResult(**result)
    
    def analyze_root_cause(
        self,
        ticket_text: str,
        logs: Optional[str] = None
    ) -> RCAResult:
        """
        Perform root cause analysis using RAG context
        
        Args:
            ticket_text: Ticket description
            logs: Optional log snippets
        
        Returns:
            RCAResult with root cause and evidence
        """
        # Retrieve relevant context
        context = self.rag.build_context(
            query=ticket_text,
            top_k=5,
            max_context_length=3000
        )
        
        prompt = f"""Perform root cause analysis for this incident.

INCIDENT:
{ticket_text}

{f"LOGS:{chr(10)}{logs}" if logs else ""}

RELEVANT KNOWLEDGE BASE:
{context}

Analyze the incident and provide:
1. ROOT_CAUSE: The primary root cause (one clear statement)
2. CONTRIBUTING_FACTORS: List of contributing factors (comma-separated)
3. EVIDENCE: What evidence supports this analysis (comma-separated)
4. CONFIDENCE: Your confidence level (High/Medium/Low)

Format your response exactly as:
ROOT_CAUSE: [statement]
CONTRIBUTING_FACTORS: [factor1, factor2, ...]
EVIDENCE: [evidence1, evidence2, ...]
CONFIDENCE: [High/Medium/Low]"""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.4
        )
        
        # Parse response
        result = {
            "root_cause": "Unable to determine root cause",
            "contributing_factors": [],
            "evidence": [],
            "confidence": "Low"
        }
        
        for line in response.strip().split('\n'):
            if line.startswith("ROOT_CAUSE:"):
                result["root_cause"] = line.replace("ROOT_CAUSE:", "").strip()
            elif line.startswith("CONTRIBUTING_FACTORS:"):
                factors = line.replace("CONTRIBUTING_FACTORS:", "").strip()
                result["contributing_factors"] = [f.strip() for f in factors.split(',') if f.strip()]
            elif line.startswith("EVIDENCE:"):
                evidence = line.replace("EVIDENCE:", "").strip()
                result["evidence"] = [e.strip() for e in evidence.split(',') if e.strip()]
            elif line.startswith("CONFIDENCE:"):
                result["confidence"] = line.replace("CONFIDENCE:", "").strip()
        
        return RCAResult(**result)
    
    def recommend_resolution(
        self,
        ticket_text: str,
        root_cause: Optional[str] = None
    ) -> ResolutionResult:
        """
        Recommend resolution steps and generate draft response
        
        Args:
            ticket_text: Ticket description
            root_cause: Optional RCA result
        
        Returns:
            ResolutionResult with actions and draft response
        """
        # Retrieve similar incidents and SOPs
        similar_docs = self.rag.retrieve(
            query=ticket_text,
            top_k=5
        )
        
        # Build context from similar incidents
        similar_context = "\n".join([
            f"[{d['metadata'].get('doc_type', 'unknown')}] {d['content'][:500]}..."
            for d in similar_docs
        ])
        
        prompt = f"""Recommend resolution for this incident.

INCIDENT:
{ticket_text}

{f"ROOT CAUSE: {root_cause}" if root_cause else ""}

SIMILAR INCIDENTS AND SOPS:
{similar_context}

Provide:
1. ACTIONS: Numbered list of resolution steps
2. DRAFT_RESPONSE: A professional response to send to the requester
3. ESTIMATED_TIME: Estimated time to resolve (e.g., "30 minutes", "2 hours")
4. RUNBOOK: Reference any relevant runbook or SOP title

Format:
ACTIONS:
1. [action]
2. [action]
...

DRAFT_RESPONSE:
[response text]

ESTIMATED_TIME: [time]
RUNBOOK: [runbook name or "None"]"""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.5
        )
        
        # Parse response
        result = {
            "recommended_actions": [],
            "draft_response": "",
            "similar_incidents": [
                {"doc_id": d["doc_id"], "score": d["score"]}
                for d in similar_docs[:3]
            ],
            "estimated_time": "Unknown",
            "runbook_reference": None
        }
        
        current_section = None
        actions = []
        draft_lines = []
        
        for line in response.strip().split('\n'):
            if line.startswith("ACTIONS:"):
                current_section = "actions"
            elif line.startswith("DRAFT_RESPONSE:"):
                current_section = "draft"
            elif line.startswith("ESTIMATED_TIME:"):
                result["estimated_time"] = line.replace("ESTIMATED_TIME:", "").strip()
                current_section = None
            elif line.startswith("RUNBOOK:"):
                runbook = line.replace("RUNBOOK:", "").strip()
                result["runbook_reference"] = runbook if runbook.lower() != "none" else None
                current_section = None
            elif current_section == "actions" and line.strip():
                # Remove numbering and add to actions
                action = line.strip()
                if action[0].isdigit() and '.' in action:
                    action = action.split('.', 1)[1].strip()
                if action:
                    actions.append(action)
            elif current_section == "draft" and line.strip():
                draft_lines.append(line)
        
        result["recommended_actions"] = actions
        result["draft_response"] = "\n".join(draft_lines)
        
        return ResolutionResult(**result)
    
    def full_analysis(
        self,
        ticket_id: str,
        ticket_text: str,
        logs: Optional[str] = None
    ) -> AnalysisResult:
        """
        Perform complete ticket analysis: triage + RCA + resolution
        
        Args:
            ticket_id: Ticket identifier
            ticket_text: Full ticket description
            logs: Optional log data
        
        Returns:
            Complete AnalysisResult
        """
        # Step 1: Triage
        triage = self.triage_ticket(ticket_text)
        
        # Step 2: Root Cause Analysis
        rca = self.analyze_root_cause(ticket_text, logs)
        
        # Step 3: Resolution Recommendation
        resolution = self.recommend_resolution(ticket_text, rca.root_cause)
        
        # Get context sources used
        docs = self.rag.retrieve(ticket_text, top_k=3)
        context_used = [d["doc_id"] for d in docs]
        
        return AnalysisResult(
            ticket_id=ticket_id,
            triage=triage,
            rca=rca,
            resolution=resolution,
            context_used=context_used
        )
    
    def chat(self, message: str, context: Optional[str] = None) -> str:
        """
        Free-form chat with RAG-enhanced context
        
        Args:
            message: User message
            context: Optional additional context
        
        Returns:
            Assistant response
        """
        # Get relevant context from RAG
        rag_context = self.rag.build_context(message, top_k=3)
        
        full_context = f"""RELEVANT KNOWLEDGE:
{rag_context}

{f"ADDITIONAL CONTEXT:{chr(10)}{context}" if context else ""}"""

        prompt = f"""{full_context}

USER QUESTION:
{message}

Provide a helpful, technical response based on the available knowledge."""

        return self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.7
        )


# Convenience function
def get_assistant() -> OpsAssistant:
    return OpsAssistant()
