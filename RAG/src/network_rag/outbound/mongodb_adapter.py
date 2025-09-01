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
        self.health_rules_collection = self.db.health_rules
        self.health_vectors_collection = self.db.health_vectors
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
            
            # Create indexes for health rules (separate collection)
            health_rule_indexes = [
                IndexModel([("device_type", ASCENDING)]),
                IndexModel([("rule_type", ASCENDING)]),
                IndexModel([("id", ASCENDING)]),
                IndexModel([("title", TEXT), ("content", TEXT)]),
                IndexModel([("keywords", ASCENDING)])
            ]
            await self.health_rules_collection.create_indexes(health_rule_indexes)
            
            # Create health rules vectors collection
            self.health_vectors_collection = self.db.health_vectors
            health_vector_indexes = [
                IndexModel([("rule_id", ASCENDING)]),
                IndexModel([("embedding_model", ASCENDING)])
            ]
            await self.health_vectors_collection.create_indexes(health_vector_indexes)
            
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
                "document_type": document.document_type.value if hasattr(document.document_type, 'value') else document.document_type,
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
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document from MongoDB"""
        try:
            result = await self.documents_collection.delete_one({"id": document_id})
            await self.vectors_collection.delete_one({"document_id": document_id})
            return result.deleted_count > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete document: {str(e)}")

    async def remove_document_from_index(self, document_id: str) -> bool:
        """Remove document from index (alias for delete_document)"""
        return await self.delete_document(document_id)
    
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
    
    async def store_health_rule(self, health_rule_data: Dict[str, Any]) -> str:
        """Store health rule in dedicated health rules collection"""
        try:
            rule_data = {
                "id": health_rule_data["id"],
                "title": health_rule_data["title"],
                "content": health_rule_data["content"],
                "device_type": health_rule_data.get("device_type", "unknown"),
                "rule_type": health_rule_data.get("rule_type", "health_analysis"),
                "keywords": health_rule_data.get("keywords", []),
                "executable_rules": health_rule_data.get("executable_rules", {}),
                "usefulness_score": health_rule_data.get("usefulness_score", 0.95),
                "version": health_rule_data.get("version", "1.0"),
                "author": health_rule_data.get("author", "System"),
                "created_at": health_rule_data.get("created_at", datetime.utcnow()),
                "updated_at": datetime.utcnow()
            }
            
            await self.health_rules_collection.replace_one(
                {"id": health_rule_data["id"]}, 
                rule_data, 
                upsert=True
            )
            
            return health_rule_data["id"]
            
        except Exception as e:
            raise DatabaseError(f"Failed to store health rule: {str(e)}")
    
    async def get_health_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get health rule by ID from health rules collection"""
        try:
            return await self.health_rules_collection.find_one({"id": rule_id})
        except Exception as e:
            raise DatabaseError(f"Failed to get health rule: {str(e)}")
    
    async def search_health_rules(self, device_type: str = None, rule_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search health rules by device type or rule type"""
        try:
            query = {}
            if device_type:
                query["device_type"] = device_type
            if rule_type:
                query["rule_type"] = rule_type
            
            cursor = self.health_rules_collection.find(query).limit(limit)
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            raise DatabaseError(f"Failed to search health rules: {str(e)}")
    
    async def delete_health_rule(self, rule_id: str) -> bool:
        """Delete health rule from health rules collection"""
        try:
            # Delete rule and its vector
            result = await self.health_rules_collection.delete_one({"id": rule_id})
            await self.health_vectors_collection.delete_one({"rule_id": rule_id})
            return result.deleted_count > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete health rule: {str(e)}")
    
    async def store_health_rule_embedding(self, rule_id: str, embedding: List[float], model: str = "default") -> bool:
        """Store embedding for a health rule"""
        try:
            vector_data = {
                "rule_id": rule_id,
                "embedding": embedding,
                "embedding_model": model,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.health_vectors_collection.replace_one(
                {"rule_id": rule_id, "embedding_model": model},
                vector_data,
                upsert=True
            )
            return True
            
        except Exception as e:
            raise DatabaseError(f"Failed to store health rule embedding: {str(e)}")
    
    async def get_health_rule_embedding(self, rule_id: str, model: str = "default") -> Optional[List[float]]:
        """Get embedding for a health rule"""
        try:
            vector_data = await self.health_vectors_collection.find_one({
                "rule_id": rule_id, 
                "embedding_model": model
            })
            return vector_data.get("embedding") if vector_data else None
            
        except Exception as e:
            raise DatabaseError(f"Failed to get health rule embedding: {str(e)}")
    
    async def find_similar_health_rules(self, query_embedding: List[float], limit: int = 5, device_type: str = None) -> List[Tuple[Dict[str, Any], float]]:
        """Find similar health rules using vector search"""
        try:
            # Simple cosine similarity implementation (in production, use vector database)
            similar_rules = []
            
            # Get all health rule vectors
            query = {"embedding_model": "default"}
            async for vector_doc in self.health_vectors_collection.find(query):
                rule_embedding = vector_doc.get("embedding", [])
                if not rule_embedding:
                    continue
                
                # Calculate cosine similarity
                similarity = self._calculate_cosine_similarity(query_embedding, rule_embedding)
                
                # Get the actual rule
                rule_id = vector_doc.get("rule_id")
                rule = await self.get_health_rule(rule_id)
                
                if rule and (not device_type or rule.get("device_type") == device_type):
                    similar_rules.append((rule, similarity))
            
            # Sort by similarity and return top results
            similar_rules.sort(key=lambda x: x[1], reverse=True)
            return similar_rules[:limit]
            
        except Exception as e:
            raise DatabaseError(f"Failed to find similar health rules: {str(e)}")
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import math
            
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception:
            return 0.0

    async def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()