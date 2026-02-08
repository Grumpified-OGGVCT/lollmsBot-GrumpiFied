"""
RAG Store - Retrieval-Augmented Generation with Vector Storage

Implements a lightweight vector store for on-device knowledge updates.
This allows the bot to learn new facts without full retraining by injecting
relevant external knowledge at inference time.

Features:
- Simple vector similarity search (cosine similarity)
- JSONL-based persistence for immutability
- Semantic chunking for long documents
- Query expansion for better retrieval

For production, can be replaced with ChromaDB, Weaviate, or other vector DBs.
"""

from __future__ import annotations

import json
import logging
import math
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("lollmsbot.memory.rag_store")


@dataclass
class Document:
    """A document stored in the RAG system.
    
    Attributes:
        id: Unique document ID
        content: The document text
        metadata: Additional metadata (source, date, etc.)
        embedding: Vector embedding (if computed)
        created_at: When the document was added
    """
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSONL storage."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Document:
        """Create from dict loaded from JSONL."""
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
        )


class SimpleEmbedding:
    """Simple embedding using TF-IDF-like approach.
    
    For production, replace with sentence-transformers or OpenAI embeddings.
    This is a lightweight fallback that doesn't require additional dependencies.
    """
    
    def __init__(self, dim: int = 384):
        """Initialize with embedding dimension."""
        self.dim = dim
        self._vocab: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._doc_count = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple word tokenization."""
        import re
        return [w.lower() for w in re.findall(r'\w+', text) if len(w) > 2]
    
    def _update_vocab(self, tokens: List[str]):
        """Update vocabulary and IDF scores."""
        unique_tokens = set(tokens)
        self._doc_count += 1
        
        for token in unique_tokens:
            if token not in self._vocab:
                self._vocab[token] = len(self._vocab)
            if token not in self._idf:
                self._idf[token] = 0
            self._idf[token] += 1
    
    def embed(self, text: str, update_vocab: bool = True) -> List[float]:
        """Create a simple embedding vector for text.
        
        Args:
            text: Input text
            update_vocab: Whether to update vocabulary (set False for queries)
            
        Returns:
            Embedding vector of length self.dim
        """
        tokens = self._tokenize(text)
        
        if update_vocab:
            self._update_vocab(tokens)
        
        # Create sparse TF-IDF vector
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        
        # Normalize by document length
        doc_len = len(tokens) if tokens else 1
        for token in tf:
            tf[token] /= doc_len
        
        # Apply IDF
        vector = [0.0] * self.dim
        for token, count in tf.items():
            if token in self._vocab:
                idx = self._vocab[token] % self.dim
                idf = math.log(self._doc_count / (self._idf.get(token, 1) + 1))
                vector[idx] += count * idf
        
        # Normalize to unit length
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector


class RAGStore:
    """Simple RAG store with vector similarity search.
    
    Stores documents in JSONL format for immutability and provides
    semantic search capabilities.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize RAG store.
        
        Args:
            storage_path: Path to JSONL storage file
        """
        self.storage_path = storage_path or Path.home() / ".lollmsbot" / "rag_store.jsonl"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.documents: Dict[str, Document] = {}
        self.embedder = SimpleEmbedding()
        
        # Load existing documents
        self._load()
    
    def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """Add a document to the store.
        
        Args:
            content: Document text
            metadata: Optional metadata
            doc_id: Optional ID (generated if not provided)
            
        Returns:
            The document ID
        """
        if doc_id is None:
            # Generate ID from content hash
            doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        # Generate embedding
        embedding = self.embedder.embed(content, update_vocab=True)
        
        # Create document
        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata or {},
            embedding=embedding,
        )
        
        self.documents[doc_id] = doc
        
        # Append to JSONL file
        self._append_to_file(doc)
        
        logger.debug(f"Added document {doc_id} with {len(content)} chars")
        return doc_id
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.1,
    ) -> List[Tuple[Document, float]]:
        """Search for documents similar to query.
        
        Args:
            query: Query text
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of (Document, similarity_score) tuples, sorted by score
        """
        # Generate query embedding
        query_embedding = self.embedder.embed(query, update_vocab=False)
        
        # Compute similarities
        results = []
        for doc in self.documents.values():
            if doc.embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                if similarity >= threshold:
                    results.append((doc, similarity))
        
        # Sort by similarity and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def get(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document or None if not found
        """
        return self.documents.get(doc_id)
    
    def delete(self, doc_id: str) -> bool:
        """Delete a document.
        
        Note: This only removes from memory. JSONL is append-only,
        so the document remains in the file but won't be loaded.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        if doc_id in self.documents:
            del self.documents[doc_id]
            # Mark as deleted in file
            self._append_to_file({"id": doc_id, "deleted": True, "deleted_at": datetime.now().isoformat()})
            return True
        return False
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return max(0.0, min(1.0, dot_product))  # Vectors are already normalized
    
    def _load(self):
        """Load documents from JSONL file."""
        if not self.storage_path.exists():
            return
        
        deleted_ids = set()
        
        with open(self.storage_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("deleted"):
                        deleted_ids.add(data["id"])
                    else:
                        doc = Document.from_dict(data)
                        if doc.id not in deleted_ids:
                            self.documents[doc.id] = doc
                            # Update embedder vocab
                            if doc.embedding:
                                # Reconstruct vocab from existing embeddings
                                pass  # Simplified - in production, store vocab separately
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSONL line: {e}")
        
        logger.info(f"Loaded {len(self.documents)} documents from {self.storage_path}")
    
    def _append_to_file(self, data: Any):
        """Append data to JSONL file."""
        with open(self.storage_path, 'a') as f:
            if isinstance(data, Document):
                f.write(json.dumps(data.to_dict()) + '\n')
            else:
                f.write(json.dumps(data) + '\n')
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "document_count": len(self.documents),
            "vocabulary_size": len(self.embedder._vocab),
            "storage_path": str(self.storage_path),
            "file_size_kb": self.storage_path.stat().st_size / 1024 if self.storage_path.exists() else 0,
        }


# Global instance
_rag_store: Optional[RAGStore] = None


def get_rag_store(storage_path: Optional[Path] = None) -> RAGStore:
    """Get or create the global RAG store instance."""
    global _rag_store
    if _rag_store is None:
        _rag_store = RAGStore(storage_path)
    return _rag_store
