"""
Demo Script - GenAI Operations Assistant
Interactive demonstration of ticket analysis capabilities
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import print as rprint

from assistant import OpsAssistant
from rag_pipeline import get_rag_pipeline
from ingestion import DocumentIngester

console = Console()


def setup_knowledge_base():
    """Initialize knowledge base with sample data"""
    console.print("\n[bold blue]Setting up knowledge base...[/bold blue]")
    
    rag = get_rag_pipeline()
    stats = rag.get_stats()
    
    if stats["total_documents"] == 0:
        console.print("Loading sample operational data...")
        ingester = DocumentIngester()
        sample_data = ingester.create_sample_data()
        
        all_docs = sample_data["tickets"] + sample_data["sops"]
        rag.add_documents_batch(all_docs)
        console.print(f"[green]✓ Loaded {len(all_docs)} documents[/green]")
    else:
        console.print(f"[green]✓ Knowledge base ready ({stats['total_documents']} documents)[/green]")
    
    return rag


def demo_triage(assistant: OpsAssistant):
    """Demonstrate ticket triage"""
    console.print(Panel.fit("[bold]Demo 1: Ticket Triage[/bold]", style="cyan"))
    
    test_ticket = """
    Application throwing 500 errors intermittently. Users report slow page loads 
    and occasional timeouts. Started around 2 PM after the latest deployment. 
    Affecting approximately 30% of requests to the checkout API.
    """
    
    console.print("[yellow]Input Ticket:[/yellow]")
    console.print(test_ticket.strip())
    console.print()
    
    console.print("[yellow]Analyzing...[/yellow]")
    result = assistant.triage_ticket(test_ticket)
    
    table = Table(title="Triage Result")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Priority", result.priority)
    table.add_row("Category", result.category)
    table.add_row("Summary", result.summary)
    table.add_row("Reasoning", result.reasoning)
    
    console.print(table)
    console.print()


def demo_rca(assistant: OpsAssistant):
    """Demonstrate root cause analysis"""
    console.print(Panel.fit("[bold]Demo 2: Root Cause Analysis[/bold]", style="cyan"))
    
    test_ticket = """
    Production database showing high CPU utilization (95%+) for the past 2 hours.
    Application response times have increased from 200ms to 3+ seconds.
    No recent deployments. Started around the time of the daily batch job.
    """
    
    sample_logs = """
    2024-01-15 14:02:15 WARN  [db-pool] Connection wait time exceeded threshold: 5000ms
    2024-01-15 14:02:18 ERROR [query] Slow query detected (12.5s): SELECT * FROM orders WHERE status IN (...)
    2024-01-15 14:02:20 WARN  [db-pool] Active connections: 48/50
    2024-01-15 14:02:25 ERROR [query] Query timeout after 30s: SELECT COUNT(*) FROM audit_log WHERE...
    """
    
    console.print("[yellow]Input Ticket:[/yellow]")
    console.print(test_ticket.strip())
    console.print()
    console.print("[yellow]Logs:[/yellow]")
    console.print(sample_logs.strip())
    console.print()
    
    console.print("[yellow]Analyzing root cause...[/yellow]")
    result = assistant.analyze_root_cause(test_ticket, sample_logs)
    
    console.print()
    console.print(f"[bold green]Root Cause:[/bold green] {result.root_cause}")
    console.print()
    console.print("[bold]Contributing Factors:[/bold]")
    for factor in result.contributing_factors:
        console.print(f"  • {factor}")
    console.print()
    console.print("[bold]Evidence:[/bold]")
    for evidence in result.evidence:
        console.print(f"  • {evidence}")
    console.print()
    console.print(f"[bold]Confidence:[/bold] {result.confidence}")
    console.print()


def demo_resolution(assistant: OpsAssistant):
    """Demonstrate resolution recommendations"""
    console.print(Panel.fit("[bold]Demo 3: Resolution Recommendations[/bold]", style="cyan"))
    
    test_ticket = """
    Kafka consumer lag growing rapidly on order-processing topic.
    Consumer group 'order-processor' showing 50k+ message backlog.
    Orders are not being processed within the 5-minute SLA.
    """
    
    console.print("[yellow]Input Ticket:[/yellow]")
    console.print(test_ticket.strip())
    console.print()
    
    console.print("[yellow]Generating recommendations...[/yellow]")
    result = assistant.recommend_resolution(test_ticket)
    
    console.print()
    console.print("[bold green]Recommended Actions:[/bold green]")
    for i, action in enumerate(result.recommended_actions, 1):
        console.print(f"  {i}. {action}")
    
    console.print()
    console.print(f"[bold]Estimated Resolution Time:[/bold] {result.estimated_time}")
    
    if result.runbook_reference:
        console.print(f"[bold]Runbook Reference:[/bold] {result.runbook_reference}")
    
    console.print()
    console.print("[bold]Draft Response:[/bold]")
    console.print(Panel(result.draft_response, style="dim"))
    console.print()


def demo_full_analysis(assistant: OpsAssistant):
    """Demonstrate complete ticket analysis"""
    console.print(Panel.fit("[bold]Demo 4: Complete Ticket Analysis[/bold]", style="cyan"))
    
    test_ticket = """
    Memory alerts firing on payment-service pods. Pods are being OOMKilled 
    every 2-3 hours. Memory usage grows linearly from restart. 
    No memory leaks detected in recent code changes.
    """
    
    console.print("[yellow]Input Ticket:[/yellow]")
    console.print(test_ticket.strip())
    console.print()
    
    console.print("[yellow]Running full analysis (triage + RCA + resolution)...[/yellow]")
    result = assistant.full_analysis(
        ticket_id="INC-DEMO-001",
        ticket_text=test_ticket
    )
    
    # Display results
    console.print()
    console.print(f"[bold magenta]Analysis for {result.ticket_id}[/bold magenta]")
    console.print("=" * 50)
    
    # Triage
    console.print()
    console.print("[bold cyan]TRIAGE[/bold cyan]")
    console.print(f"  Priority: {result.triage.priority}")
    console.print(f"  Category: {result.triage.category}")
    console.print(f"  Summary: {result.triage.summary}")
    
    # RCA
    console.print()
    console.print("[bold cyan]ROOT CAUSE ANALYSIS[/bold cyan]")
    console.print(f"  Root Cause: {result.rca.root_cause}")
    console.print(f"  Confidence: {result.rca.confidence}")
    
    # Resolution
    console.print()
    console.print("[bold cyan]RESOLUTION[/bold cyan]")
    console.print("  Actions:")
    for i, action in enumerate(result.resolution.recommended_actions[:3], 1):
        console.print(f"    {i}. {action}")
    
    console.print()
    console.print(f"  [dim]Context sources used: {', '.join(result.context_used)}[/dim]")
    console.print()


def interactive_mode(assistant: OpsAssistant):
    """Interactive chat mode"""
    console.print(Panel.fit("[bold]Interactive Mode[/bold]", style="green"))
    console.print("Enter ticket descriptions or questions. Type 'quit' to exit.\n")
    
    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if not user_input.strip():
                continue
            
            console.print("[yellow]Thinking...[/yellow]")
            response = assistant.chat(user_input)
            console.print()
            console.print(f"[bold green]Assistant:[/bold green] {response}")
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break


def main():
    console.print(Panel.fit(
        "[bold white]GenAI Operations Assistant Demo[/bold white]\n"
        "AI-Powered Ticket Triage, RCA & Resolution",
        style="blue"
    ))
    
    # Setup
    setup_knowledge_base()
    
    console.print("\n[bold blue]Initializing Operations Assistant...[/bold blue]")
    assistant = OpsAssistant()
    console.print("[green]✓ Assistant ready[/green]\n")
    
    # Run demos
    try:
        demo_triage(assistant)
        input("Press Enter to continue...")
        
        demo_rca(assistant)
        input("Press Enter to continue...")
        
        demo_resolution(assistant)
        input("Press Enter to continue...")
        
        demo_full_analysis(assistant)
        input("Press Enter to continue to interactive mode...")
        
        interactive_mode(assistant)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[yellow]Make sure the LLM endpoint is accessible.[/yellow]")


if __name__ == "__main__":
    main()
