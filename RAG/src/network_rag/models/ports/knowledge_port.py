# src/network_rag/models/ports/knowledge_port.py
"""Knowledge storage port interface"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..document import Document, DocumentType


class KnowledgePort(ABC):
    """Interface for knowledge base storage and retrieval"""
    
    @abstractmethod
    async def store_document(self, document: Document) -> str:
        """
        Store document in knowledge base
        
        Args:
            document: Document to store
            
        Returns:
            Document ID
            
        Raises:
            DocumentError: When storage fails
        """
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        Retrieve document by ID
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            Document if found, None otherwise
            
        Raises:
            DocumentError: When retrieval fails
        """
        pass
    
    @abstractmethod
    async def update_document(self, document: Document) -> bool:
        """
        Update existing document
        
        Args:
            document: Document with updates
            
        Returns:
            True if updated successfully
            
        Raises:
            DocumentError: When update fails
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document from knowledge base
        
        Args:
            document_id: Document to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            DocumentError: When deletion fails
        """
        pass
    
    @abstractmethod
    async def search_documents(self, query: str, limit: int = 10) -> List[Document]:
        """
        Text-based search in documents
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching documents
            
        Raises:
            DocumentError: When search fails
        """
        pass
    
    @abstractmethod
    async def get_documents_by_type(self, document_type: DocumentType, limit: Optional[int] = None) -> List[Document]:
        """
        Get documents by type
        
        Args:
            document_type: Type of documents to retrieve
            limit: Optional limit on results
            
        Returns:
            List of documents of specified type
            
        Raises:
            DocumentError: When retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_documents_by_author(self, author: str, limit: Optional[int] = None) -> List[Document]:
        """
        Get documents by author
        
        Args:
            author: Author name
            limit: Optional limit on results
            
        Returns:
            List of documents by author
            
        Raises:
            DocumentError: When retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_recent_documents(self, limit: int = 10) -> List[Document]:
        """
        Get most recently created/updated documents
        
        Args:
            limit: Maximum number of documents
            
        Returns:
            List of recent documents
            
        Raises:
            DocumentError: When retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_popular_documents(self, limit: int = 10) -> List[Document]:
        """
        Get most viewed/accessed documents
        
        Args:
            limit: Maximum number of documents
            
        Returns:
            List of popular documents
            
        Raises:
            DocumentError: When retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_documents_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Document]:
        """
        Get documents matching any of the keywords
        
        Args:
            keywords: List of keywords to match
            limit: Maximum number of results
            
        Returns:
            List of matching documents
            
        Raises:
            DocumentError: When search fails
        """
        pass
    
    @abstractmethod
    async def get_document_statistics(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics
        
        Returns:
            Statistics about documents, types, authors, etc.
            
        Raises:
            DocumentError: When statistics retrieval fails
        """
        pass