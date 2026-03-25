"""
Quick test script to verify the Operations Assistant setup
"""
import sys
import os

def test_llm_connection():
    """Test LLM endpoint connectivity"""
    print("Testing LLM connection...")
    try:
        from llm_client import get_llm_client
        client = get_llm_client()
        
        if client.health_check():
            print("✓ LLM endpoint is reachable")
            
            # Quick generation test
            response = client.generate(
                prompt="Say 'Hello, Operations!' in one line.",
                temperature=0.1,
                max_tokens=50
            )
            print(f"✓ LLM responded: {response[:100]}")
            return True
        else:
            print("✗ LLM endpoint not reachable")
            return False
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
        return False


def test_rag_pipeline():
    """Test RAG pipeline initialization"""
    print("\nTesting RAG pipeline...")
    try:
        from rag_pipeline import get_rag_pipeline
        rag = get_rag_pipeline()
        
        stats = rag.get_stats()
        print(f"✓ RAG pipeline initialized")
        print(f"  Documents in store: {stats['total_documents']}")
        
        # Test adding a document
        rag.add_document(
            content="Test document for verification",
            doc_id="test_doc_001",
            doc_type="test"
        )
        print("✓ Document ingestion works")
        
        # Test retrieval
        results = rag.retrieve("test verification", top_k=1)
        if results:
            print("✓ Document retrieval works")
        
        return True
    except Exception as e:
        print(f"✗ RAG test failed: {e}")
        return False


def test_assistant():
    """Test Operations Assistant"""
    print("\nTesting Operations Assistant...")
    try:
        from assistant import OpsAssistant
        from ingestion import DocumentIngester
        from rag_pipeline import get_rag_pipeline
        
        # Load sample data first
        rag = get_rag_pipeline()
        if rag.get_stats()["total_documents"] < 5:
            print("  Loading sample data...")
            ingester = DocumentIngester()
            sample_data = ingester.create_sample_data()
            all_docs = sample_data["tickets"] + sample_data["sops"]
            rag.add_documents_batch(all_docs)
        
        assistant = OpsAssistant()
        print("✓ Assistant initialized")
        
        # Test triage
        result = assistant.triage_ticket(
            "Database connection timeout errors in production"
        )
        print(f"✓ Triage works - Priority: {result.priority}, Category: {result.category}")
        
        return True
    except Exception as e:
        print(f"✗ Assistant test failed: {e}")
        return False


def main():
    print("=" * 50)
    print("GenAI Operations Assistant - Setup Test")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("LLM Connection", test_llm_connection()))
    results.append(("RAG Pipeline", test_rag_pipeline()))
    results.append(("Operations Assistant", test_assistant()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✓ All tests passed! The assistant is ready to use.")
        print("\nNext steps:")
        print("  1. Run the demo: python demo.py")
        print("  2. Start the API: uvicorn app.main:app --port 8080")
    else:
        print("\n✗ Some tests failed. Check the configuration.")
        print("  - Verify LLM_BASE_URL in .env file")
        print("  - Ensure the Qwen endpoint is accessible")


if __name__ == "__main__":
    main()
