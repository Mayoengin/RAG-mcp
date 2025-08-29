# src/network_rag/models/ports/vector_search_port.py
"""Vector search port interface for similarity search operations"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from ..document import Document


class VectorSearchPort(ABC):
    """Interface for vector similarity search operations"""
    
    @abstractmethod
    async def index_document(self, document: Document, embedding: List[float]) -> bool:
        """
        Index document with its embedding for similarity search
        
        Args:
            document: Document to index
            embedding: Vector embedding of the document
            
        Returns:
            True if indexed successfully
            
        Raises:
            VectorSearchError: When indexing fails
        """
        pass
    
    @abstractmethod
    async def similarity_search(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        threshold: float = 0.7,
        document_types: Optional[List[str]] = None
    ) -> List[Tuple[Document, float]]:
        """
        Find similar documents by embedding similarity
        
        Args:
            query_embedding: Query vector embedding
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            document_types: Optional filter by document types
            
        Returns:
            List of tuples (Document, similarity_score)
            
        Raises:
            VectorSearchError: When search fails
        """
        pass
    
    @abstractmethod
    async def batch_similarity_search(
        self,
        query_embeddings: List[List[float]],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[List[Tuple[Document, float]]]:
        """
        Perform batch similarity search for multiple queries
        
        Args:
            query_embeddings: List of query vector embeddings
            limit: Maximum results per query
            threshold: Minimum similarity threshold
            
        Returns:
            List of result lists, one per query
            
        Raises:
            VectorSearchError: When batch search fails
        """
        pass
    
    @abstractmethod
    async def find_similar_documents(
        self, 
        document_id: str, 
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """
        Find documents similar to a given document
        
        Args:
            document_id: ID of reference document
            limit: Maximum number of similar documents
            threshold: Minimum similarity threshold
            
        Returns:
            List of tuples (Document, similarity_score)
            
        Raises:
            VectorSearchError: When search fails
        """
        pass
    
    @abstractmethod
    async def update_document_embedding(self, document_id: str, embedding: List[float]) -> bool:
        """
        Update document's embedding in the index
        
        Args:
            document_id: Document identifier
            embedding: New vector embedding
            
        Returns:
            True if updated successfully
            
        Raises:
            VectorSearchError: When update fails
        """
        pass
    
    @abstractmethod
    async def remove_document_from_index(self, document_id: str) -> bool:
        """
        Remove document from vector index
        
        Args:
            document_id: Document to remove
            
        Returns:
            True if removed successfully
            
        Raises:
            VectorSearchError: When removal fails
        """
        pass
    
    @abstractmethod
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get vector index statistics and health information
        
        Returns:
            Dictionary with index statistics
            
        Raises:
            VectorSearchError: When stats retrieval fails
        """
        pass
    
    @abstractmethod
    async def rebuild_index(self, documents: List[Tuple[Document, List[float]]]) -> bool:
        """
        Rebuild the entire vector index with given documents
        
        Args:
            documents: List of tuples (Document, embedding)
            
        Returns:
            True if rebuild was successful
            
        Raises:
            VectorSearchError: When rebuild fails
        """
        pass
    
    @abstractmethod
    async def get_document_embedding(self, document_id: str) -> Optional[List[float]]:
        """
        Get the embedding vector for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Embedding vector if found, None otherwise
            
        Raises:
            VectorSearchError: When retrieval fails
        """
        pass
    
    @abstractmethod
    async def cluster_documents(
        self, 
        num_clusters: int = 10,
        document_types: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """
        Cluster documents based on their embeddings
        
        Args:
            num_clusters: Number of clusters to create
            document_types: Optional filter by document types
            
        Returns:
            Dictionary mapping cluster_id to list of document_ids
            
        Raises:
            VectorSearchError: When clustering fails
        """
        pass
    
    @abstractmethod
    async def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings used in this index
        
        Returns:
            Embedding dimension size
            
        Raises:
            VectorSearchError: When dimension retrieval fails
        """
        pass