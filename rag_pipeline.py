"""
RAG Pipeline with ChromaDB Vector Store
Handles document embedding, storage, and retrieval for operations knowledge
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


class RAGPipeline:
    """
    RAG (Retrieval-Augmented Generation) Pipeline
    - Embeds documents using sentence-transformers
    - Stores vectors in ChromaDB
    - Retrieves relevant context for LLM queries
    """
    
    def __init__(
        self,
        persist_dir: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "ops_knowledge"
    ):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.collection_name = collection_name
        
        # Initialize embedding model
        print(f"Loading embedding model: {embedding_model}...")
        self.embedder = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Operations knowledge base"}
        )
        
        print(f"RAG Pipeline initialized. Documents in store: {self.collection.count()}")
    
    def add_document(
        self,
        content: str,
        doc_id: str,
        doc_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a single document to the vector store
        
        Args:
            content: Document text content
            doc_id: Unique document identifier
            doc_type: Type of document (ticket, log, sop, kb_article)
            metadata: Additional metadata
        """
        meta = metadata or {}
        meta["doc_type"] = doc_type
        
        # Generate embedding
        embedding = self.embedder.encode(content).tolist()
        
        # Upsert to collection
        self.collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[meta]
        )
    
    def add_documents_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Add multiple documents in batch
        
        Args:
            documents: List of dicts with keys: content, doc_id, doc_type, metadata
        
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        ids = []
        contents = []
        embeddings = []
        metadatas = []
        
        for doc in documents:
            ids.append(doc["doc_id"])
            contents.append(doc["content"])
            
            meta = doc.get("metadata", {})
            meta["doc_type"] = doc.get("doc_type", "general")
            metadatas.append(meta)
        
        # Batch encode
        embeddings = self.embedder.encode(contents).tolist()
        
        # Upsert batch
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )
        
        return len(documents)
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        doc_type_filter: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            top_k: Number of results to return
            doc_type_filter: Filter by document type
            min_score: Minimum similarity score (0-1)
        
        Returns:
            List of relevant documents with scores
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()
        
        # Build where filter
        where_filter = None
        if doc_type_filter:
            where_filter = {"doc_type": doc_type_filter}
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        retrieved_docs = []
        for i, doc_id in enumerate(results["ids"][0]):
            # Convert distance to similarity score (ChromaDB uses L2 distance)
            distance = results["distances"][0][i]
            similarity = 1 / (1 + distance)  # Convert to 0-1 range
            
            if similarity >= min_score:
                retrieved_docs.append({
                    "doc_id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": round(similarity, 4)
                })
        
        return retrieved_docs
    
    def build_context(
        self,
        query: str,
        top_k: int = 5,
        max_context_length: int = 4000
    ) -> str:
        """
        Build context string from retrieved documents for LLM
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            max_context_length: Maximum character length for context
        
        Returns:
            Formatted context string
        """
        docs = self.retrieve(query, top_k=top_k)
        
        if not docs:
            return "No relevant knowledge found in the database."
        
        context_parts = []
        current_length = 0
        
        for doc in docs:
            doc_text = f"[{doc['metadata'].get('doc_type', 'unknown').upper()}] "
            doc_text += f"(Relevance: {doc['score']:.0%})\n"
            doc_text += doc['content']
            doc_text += "\n---\n"
            
            if current_length + len(doc_text) > max_context_length:
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        count = self.collection.count()
        
        # Get document type distribution
        if count > 0:
            all_docs = self.collection.get(include=["metadatas"])
            type_counts = {}
            for meta in all_docs["metadatas"]:
                doc_type = meta.get("doc_type", "unknown")
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        else:
            type_counts = {}
        
        return {
            "total_documents": count,
            "by_type": type_counts,
            "collection_name": self.collection_name,
            "persist_dir": self.persist_dir
        }
    
    def clear(self) -> None:
        """Clear all documents from the collection"""
        self.chroma_client.delete_collection(self.collection_name)
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Operations knowledge base"}
        )


# Singleton instance
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the RAG pipeline singleton"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
