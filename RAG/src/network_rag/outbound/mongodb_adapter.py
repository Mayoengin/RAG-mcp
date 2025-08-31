# src/network_rag/outbound/mongodb_adapter.py
"""Simplified MongoDB adapter implementing knowledge storage and vector search"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, TEXT

from ..models import (
    Document,
    VectorSearchPort,
    DatabaseError
)


class MongoDBAdapter(VectorSearchPort):
    """Simplified MongoDB adapter for vector search and document storage"""
    
    def __init__(self, connection_string: str, database_name: str = "network_rag"):
        self.client = AsyncIOMotorClient(connection_string)
        self.db: AsyncIOMotorDatabase = self.client[database_name]
        self.documents_collection = self.db.documents
        self.vectors_collection = self.db.vectors
    
    async def initialize(self) -> None:
        """Initialize database collections and indexes"""
        try:
            # Create indexes for documents
            document_indexes = [
                IndexModel([("document_type", ASCENDING)]),
                IndexModel([("keywords", ASCENDING)]),
                IndexModel([("usefulness_score", -1)]),
                IndexModel([("title", TEXT), ("content", TEXT)])
            ]
            await self.documents_collection.create_indexes(document_indexes)
            
            # Create indexes for vectors
            vector_indexes = [
                IndexModel([("document_id", ASCENDING)]),
                IndexModel([("embedding_model", ASCENDING)])
            ]
            await self.vectors_collection.create_indexes(vector_indexes)
            
        except Exception as e:
            raise DatabaseError(f"Failed to initialize MongoDB: {str(e)}")
    
    async def store_document(self, document: Document) -> str:
        """Store document in MongoDB"""
        try:
            doc_data = {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "document_type": document.document_type.value,
                "keywords": document.keywords,
                "usefulness_score": document.usefulness_score,
                "created_at": document.created_at,
                "updated_at": datetime.utcnow()
            }
            
            await self.documents_collection.replace_one(
                {"id": document.id}, 
                doc_data, 
                upsert=True
            )
            
            return document.id
            
        except Exception as e:
            raise DatabaseError(f"Failed to store document: {str(e)}")
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve document by ID"""
        try:
            doc_data = await self.documents_collection.find_one({"id": document_id})
            if doc_data:
                return Document(
                    id=doc_data["id"],
                    title=doc_data["title"],
                    content=doc_data["content"],
                    document_type=doc_data["document_type"],
                    keywords=doc_data.get("keywords", []),
                    usefulness_score=doc_data.get("usefulness_score", 0.5),
                    created_at=doc_data.get("created_at", datetime.utcnow())
                )
            return None
            
        except Exception as e:
            raise DatabaseError(f"Failed to get document: {str(e)}")
    
    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        use_vector_search: bool = True,
        document_types: Optional[List[str]] = None
    ) -> List[Document]:
        """Search documents using text search"""
        try:
            # Build search filter
            search_filter = {"$text": {"$search": query}}
            
            if document_types:
                search_filter["document_type"] = {"$in": document_types}
            
            # Execute search
            cursor = self.documents_collection.find(
                search_filter,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            documents = []
            async for doc_data in cursor:
                documents.append(Document(
                    id=doc_data["id"],
                    title=doc_data["title"],
                    content=doc_data["content"],
                    document_type=doc_data["document_type"],
                    keywords=doc_data.get("keywords", []),
                    usefulness_score=doc_data.get("usefulness_score", 0.5),
                    created_at=doc_data.get("created_at", datetime.utcnow())
                ))
            
            return documents
            
        except Exception as e:
            print(f"Document search failed: {e}")
            return []  # Return empty list on error
    
    async def store_embedding(
        self,
        document_id: str,
        embedding: List[float],
        model_name: str = "default"
    ) -> None:
        """Store document embedding"""
        try:
            vector_data = {
                "document_id": document_id,
                "embedding": embedding,
                "embedding_model": model_name,
                "created_at": datetime.utcnow()
            }
            
            await self.vectors_collection.replace_one(
                {"document_id": document_id, "embedding_model": model_name},
                vector_data,
                upsert=True
            )
            
        except Exception as e:
            raise DatabaseError(f"Failed to store embedding: {str(e)}")
    
    async def vector_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """Perform vector similarity search (simplified version)"""
        try:
            # This is a simplified implementation
            # In production, you'd use MongoDB Atlas Vector Search or similar
            documents = []
            async for doc_data in self.documents_collection.find().limit(limit):
                document = Document(
                    id=doc_data["id"],
                    title=doc_data["title"],
                    content=doc_data["content"],
                    document_type=doc_data["document_type"],
                    keywords=doc_data.get("keywords", []),
                    usefulness_score=doc_data.get("usefulness_score", 0.5),
                    created_at=doc_data.get("created_at", datetime.utcnow())
                )
                # Use usefulness_score as a proxy for similarity
                similarity = doc_data.get("usefulness_score", 0.5)
                documents.append((document, similarity))
            
            # Sort by similarity
            documents.sort(key=lambda x: x[1], reverse=True)
            return documents
            
        except Exception as e:
            print(f"Vector search failed: {e}")
            return []
    
    # Stub implementations for VectorSearchPort abstract methods
    async def index_document(self, document: Document, embedding: List[float]) -> bool:
        """Index document with embedding"""
        await self.store_document(document)
        await self.store_embedding(document.id, embedding)
        return True
    
    async def similarity_search(self, query_embedding: List[float], limit: int = 10, threshold: float = 0.7) -> List[Tuple[Document, float]]:
        """Similarity search (reuse vector_search)"""
        return await self.vector_search(query_embedding, limit, threshold)
    
    async def find_similar_documents(self, document_id: str, limit: int = 10) -> List[Tuple[Document, float]]:
        """Find similar documents"""
        return []  # Stub implementation
    
    async def get_document_embedding(self, document_id: str) -> Optional[List[float]]:
        """Get document embedding"""
        return None  # Stub implementation
    
    async def remove_document_from_index(self, document_id: str) -> bool:
        """Remove document from index"""
        await self.documents_collection.delete_one({"id": document_id})
        await self.vectors_collection.delete_one({"document_id": document_id})
        return True
    
    async def update_document_embedding(self, document_id: str, embedding: List[float]) -> bool:
        """Update document embedding"""
        await self.store_embedding(document_id, embedding)
        return True
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        doc_count = await self.documents_collection.count_documents({})
        return {"document_count": doc_count}
    
    async def rebuild_index(self) -> bool:
        """Rebuild index"""
        return True  # Stub implementation
    
    async def batch_similarity_search(self, query_embeddings: List[List[float]], limit: int = 10) -> List[List[Tuple[Document, float]]]:
        """Batch similarity search"""
        return []  # Stub implementation
    
    async def cluster_documents(self, num_clusters: int = 5) -> Dict[str, List[str]]:
        """Cluster documents"""
        return {}  # Stub implementation
    
    async def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return 384  # Default dimension
    
    async def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()