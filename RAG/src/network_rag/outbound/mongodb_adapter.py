# src/network_rag/outbound/mongodb_adapter.py
"""MongoDB adapter implementing knowledge storage, vector search, and conversation management"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, TEXT

from ..models import (
    Document, Conversation, Message, Feedback,
    KnowledgePort, VectorSearchPort, ConversationPort,
    DatabaseError
)


class MongoDBAdapter(KnowledgePort, VectorSearchPort, ConversationPort):
    """MongoDB adapter implementing multiple storage interfaces"""
    
    def __init__(self, connection_string: str, database_name: str = "network_rag"):
        self.client = AsyncIOMotorClient(connection_string)
        self.db: AsyncIOMotorDatabase = self.client[database_name]
        
        # Collections
        self.documents = self.db.documents
        self.conversations = self.db.conversations
        self.vector_index = self.db.vector_index
        
        self._indexes_created = False
    
    async def initialize(self):
        """Initialize database indexes"""
        if not self._indexes_created:
            await self._create_indexes()
            self._indexes_created = True
    
    async def _create_indexes(self):
        """Create necessary database indexes"""
        try:
            # Document indexes
            await self.documents.create_indexes([
                IndexModel([("id", ASCENDING)], unique=True),
                IndexModel([("document_type", ASCENDING)]),
                IndexModel([("keywords", ASCENDING)]),
                IndexModel([("title", TEXT), ("content", TEXT)]),
                IndexModel([("created_at", ASCENDING)]),
                IndexModel([("usefulness_score", ASCENDING)])
            ])
            
            # Conversation indexes
            await self.conversations.create_indexes([
                IndexModel([("id", ASCENDING)], unique=True),
                IndexModel([("session_id", ASCENDING)]),
                IndexModel([("last_activity", ASCENDING)]),
                IndexModel([("topics", ASCENDING)])
            ])
            
            # Vector index
            await self.vector_index.create_indexes([
                IndexModel([("document_id", ASCENDING)], unique=True),
                IndexModel([("document_type", ASCENDING)])
            ])
            
        except Exception as e:
            raise DatabaseError(operation="create_indexes", message=f"Failed to create indexes: {e}")
    
    # KnowledgePort Implementation
    
    async def store_document(self, document: Document) -> str:
        """Store document in MongoDB"""
        try:
            doc_dict = document.dict()
            doc_dict["_id"] = document.id
            
            await self.documents.insert_one(doc_dict)
            return document.id
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="insert",
                message=f"Failed to store document: {e}"
            )
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve document by ID"""
        try:
            doc_data = await self.documents.find_one({"id": document_id})
            if doc_data:
                doc_data.pop("_id", None)
                return Document(**doc_data)
            return None
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="find_one",
                message=f"Failed to retrieve document: {e}"
            )
    
    async def update_document(self, document: Document) -> bool:
        """Update existing document"""
        try:
            doc_dict = document.dict()
            doc_dict.pop("id", None)  # Don't update ID
            
            result = await self.documents.update_one(
                {"id": document.id},
                {"$set": doc_dict}
            )
            return result.modified_count > 0
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="update",
                message=f"Failed to update document: {e}"
            )
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        try:
            # Remove from documents
            doc_result = await self.documents.delete_one({"id": document_id})
            
            # Remove from vector index
            await self.vector_index.delete_one({"document_id": document_id})
            
            return doc_result.deleted_count > 0
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="delete",
                message=f"Failed to delete document: {e}"
            )
    
    async def search_documents(self, query: str, limit: int = 10) -> List[Document]:
        """Text search in documents"""
        try:
            cursor = self.documents.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            documents = []
            async for doc_data in cursor:
                doc_data.pop("_id", None)
                doc_data.pop("score", None)
                documents.append(Document(**doc_data))
            
            return documents
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="text_search",
                message=f"Text search failed: {e}"
            )
    
    async def get_documents_by_type(self, document_type: str, limit: Optional[int] = None) -> List[Document]:
        """Get documents by type"""
        try:
            cursor = self.documents.find({"document_type": document_type})
            if limit:
                cursor = cursor.limit(limit)
            
            documents = []
            async for doc_data in cursor:
                doc_data.pop("_id", None)
                documents.append(Document(**doc_data))
            
            return documents
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="find_by_type",
                message=f"Failed to find documents by type: {e}"
            )
    
    async def get_documents_by_author(self, author: str, limit: Optional[int] = None) -> List[Document]:
        """Get documents by author"""
        try:
            cursor = self.documents.find({"author": author})
            if limit:
                cursor = cursor.limit(limit)
            
            documents = []
            async for doc_data in cursor:
                doc_data.pop("_id", None)
                documents.append(Document(**doc_data))
            
            return documents
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="find_by_author",
                message=f"Failed to find documents by author: {e}"
            )
    
    async def get_recent_documents(self, limit: int = 10) -> List[Document]:
        """Get most recently created/updated documents"""
        try:
            cursor = self.documents.find().sort("updated_at", -1).limit(limit)
            
            documents = []
            async for doc_data in cursor:
                doc_data.pop("_id", None)
                documents.append(Document(**doc_data))
            
            return documents
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="find_recent",
                message=f"Failed to get recent documents: {e}"
            )
    
    async def get_popular_documents(self, limit: int = 10) -> List[Document]:
        """Get most viewed documents"""
        try:
            cursor = self.documents.find().sort("view_count", -1).limit(limit)
            
            documents = []
            async for doc_data in cursor:
                doc_data.pop("_id", None)
                documents.append(Document(**doc_data))
            
            return documents
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="find_popular",
                message=f"Failed to get popular documents: {e}"
            )
    
    async def get_documents_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Document]:
        """Get documents matching keywords"""
        try:
            cursor = self.documents.find(
                {"keywords": {"$in": keywords}}
            ).limit(limit)
            
            documents = []
            async for doc_data in cursor:
                doc_data.pop("_id", None)
                documents.append(Document(**doc_data))
            
            return documents
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="find_by_keywords",
                message=f"Failed to find documents by keywords: {e}"
            )
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get document statistics"""
        try:
            total_docs = await self.documents.count_documents({})
            
            # Count by type
            pipeline = [
                {"$group": {"_id": "$document_type", "count": {"$sum": 1}}}
            ]
            
            type_counts = {}
            async for result in self.documents.aggregate(pipeline):
                type_counts[result["_id"]] = result["count"]
            
            return {
                "total_documents": total_docs,
                "documents_by_type": type_counts,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise DatabaseError(
                collection="documents",
                operation="statistics",
                message=f"Failed to get document statistics: {e}"
            )
    
    # VectorSearchPort Implementation
    
    async def index_document(self, document: Document, embedding: List[float]) -> bool:
        """Index document with embedding"""
        try:
            vector_doc = {
                "_id": document.id,
                "document_id": document.id,
                "title": document.title,
                "document_type": document.document_type.value,
                "embedding": embedding,
                "keywords": document.keywords,
                "created_at": document.created_at,
                "usefulness_score": document.usefulness_score
            }
            
            await self.vector_index.replace_one(
                {"document_id": document.id},
                vector_doc,
                upsert=True
            )
            return True
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="index",
                message=f"Failed to index document: {e}"
            )
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        document_types: Optional[List[str]] = None
    ) -> List[Tuple[Document, float]]:
        """Find similar documents using cosine similarity"""
        try:
            # Build query filter
            match_filter = {}
            if document_types:
                match_filter["document_type"] = {"$in": document_types}
            
            # Get all vector documents (in production, use vector search engine)
            cursor = self.vector_index.find(match_filter)
            
            results = []
            async for vector_doc in cursor:
                if "embedding" in vector_doc and vector_doc["embedding"]:
                    similarity = self._calculate_cosine_similarity(
                        query_embedding,
                        vector_doc["embedding"]
                    )
                    
                    if similarity >= threshold:
                        # Get full document
                        document = await self.get_document(vector_doc["document_id"])
                        if document:
                            results.append((document, similarity))
            
            # Sort by similarity and limit
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="similarity_search",
                message=f"Similarity search failed: {e}"
            )
    
    async def batch_similarity_search(
        self,
        query_embeddings: List[List[float]],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[List[Tuple[Document, float]]]:
        """Batch similarity search"""
        try:
            tasks = []
            for embedding in query_embeddings:
                task = self.similarity_search(embedding, limit, threshold)
                tasks.append(task)
            
            return await asyncio.gather(*tasks)
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="batch_similarity_search",
                message=f"Batch similarity search failed: {e}"
            )
    
    async def find_similar_documents(
        self,
        document_id: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """Find documents similar to given document"""
        try:
            # Get document embedding
            vector_doc = await self.vector_index.find_one({"document_id": document_id})
            if not vector_doc or "embedding" not in vector_doc:
                return []
            
            # Search for similar documents
            results = await self.similarity_search(
                vector_doc["embedding"],
                limit + 1,  # +1 to account for self
                threshold
            )
            
            # Remove the original document from results
            filtered_results = [(doc, sim) for doc, sim in results if doc.id != document_id]
            return filtered_results[:limit]
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="find_similar",
                message=f"Failed to find similar documents: {e}"
            )
    
    async def update_document_embedding(self, document_id: str, embedding: List[float]) -> bool:
        """Update document embedding"""
        try:
            result = await self.vector_index.update_one(
                {"document_id": document_id},
                {"$set": {"embedding": embedding}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="update_embedding",
                message=f"Failed to update embedding: {e}"
            )
    
    async def remove_document_from_index(self, document_id: str) -> bool:
        """Remove document from vector index"""
        try:
            result = await self.vector_index.delete_one({"document_id": document_id})
            return result.deleted_count > 0
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="remove_from_index",
                message=f"Failed to remove from index: {e}"
            )
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get vector index statistics"""
        try:
            total_docs = await self.vector_index.count_documents({})
            
            # Count by document type
            pipeline = [
                {"$group": {"_id": "$document_type", "count": {"$sum": 1}}}
            ]
            
            type_counts = {}
            async for result in self.vector_index.aggregate(pipeline):
                type_counts[result["_id"]] = result["count"]
            
            return {
                "total_documents": total_docs,
                "documents_by_type": type_counts,
                "index_name": "vector_index",
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="get_stats",
                message=f"Failed to get index stats: {e}"
            )
    
    async def rebuild_index(self, documents: List[Tuple[Document, List[float]]]) -> bool:
        """Rebuild entire vector index"""
        try:
            # Clear existing index
            await self.vector_index.delete_many({})
            
            # Index all documents
            for document, embedding in documents:
                await self.index_document(document, embedding)
            
            return True
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="rebuild_index",
                message=f"Failed to rebuild index: {e}"
            )
    
    async def get_document_embedding(self, document_id: str) -> Optional[List[float]]:
        """Get document embedding"""
        try:
            vector_doc = await self.vector_index.find_one({"document_id": document_id})
            if vector_doc and "embedding" in vector_doc:
                return vector_doc["embedding"]
            return None
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="get_embedding",
                message=f"Failed to get document embedding: {e}"
            )
    
    async def cluster_documents(
        self,
        num_clusters: int = 10,
        document_types: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """Cluster documents by embeddings (simplified implementation)"""
        try:
            # This would typically use a clustering algorithm like K-means
            # For now, return a simple grouping by document type
            
            match_filter = {}
            if document_types:
                match_filter["document_type"] = {"$in": document_types}
            
            pipeline = [
                {"$match": match_filter},
                {"$group": {"_id": "$document_type", "documents": {"$push": "$document_id"}}}
            ]
            
            clusters = {}
            async for result in self.vector_index.aggregate(pipeline):
                cluster_id = f"cluster_{result['_id']}"
                clusters[cluster_id] = result["documents"]
            
            return clusters
            
        except Exception as e:
            raise DatabaseError(
                collection="vector_index",
                operation="cluster_documents",
                message=f"Document clustering failed: {e}"
            )
    
    async def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        try:
            sample_doc = await self.vector_index.find_one({"embedding": {"$exists": True}})
            if sample_doc and "embedding" in sample_doc:
                return len(sample_doc["embedding"])
            return 384  # Default dimension
            
        except Exception as e:
            return 384  # Fallback dimension
    
    # ConversationPort Implementation
    
    async def create_conversation(
        self,
        session_id: str,
        user_context: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> str:
        """Create new conversation"""
        try:
            if not conversation_id:
                conversation_id = f"conv_{int(datetime.utcnow().timestamp())}"
            
            conversation = Conversation(
                id=conversation_id,
                session_id=session_id,
                user_context=user_context
            )
            
            conv_dict = conversation.dict()
            conv_dict["_id"] = conversation_id
            
            await self.conversations.insert_one(conv_dict)
            return conversation_id
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="create",
                message=f"Failed to create conversation: {e}"
            )
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        try:
            conv_data = await self.conversations.find_one({"id": conversation_id})
            if conv_data:
                conv_data.pop("_id", None)
                return Conversation(**conv_data)
            return None
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="get",
                message=f"Failed to get conversation: {e}"
            )
    
    async def update_conversation(self, conversation: Conversation) -> bool:
        """Update conversation"""
        try:
            conv_dict = conversation.dict()
            conv_dict.pop("id", None)
            
            result = await self.conversations.update_one(
                {"id": conversation.id},
                {"$set": conv_dict}
            )
            return result.modified_count > 0
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="update",
                message=f"Failed to update conversation: {e}"
            )
    
    async def add_message(self, conversation_id: str, message: Message) -> bool:
        """Add message to conversation"""
        try:
            result = await self.conversations.update_one(
                {"id": conversation_id},
                {
                    "$push": {"messages": message.dict()},
                    "$set": {"last_activity": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="add_message",
                message=f"Failed to add message: {e}"
            )
    
    async def add_feedback(self, conversation_id: str, feedback: Feedback) -> bool:
        """Add feedback to conversation"""
        try:
            result = await self.conversations.update_one(
                {"id": conversation_id},
                {"$push": {"feedback": feedback.dict()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="add_feedback",
                message=f"Failed to add feedback: {e}"
            )
    
    async def get_recent_conversations(
        self,
        session_id: str,
        limit: int = 10,
        include_archived: bool = False
    ) -> List[Conversation]:
        """Get recent conversations"""
        try:
            query = {"session_id": session_id}
            if not include_archived:
                query["status"] = {"$ne": "archived"}
            
            cursor = self.conversations.find(query).sort("last_activity", -1).limit(limit)
            
            conversations = []
            async for conv_data in cursor:
                conv_data.pop("_id", None)
                conversations.append(Conversation(**conv_data))
            
            return conversations
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="get_recent",
                message=f"Failed to get recent conversations: {e}"
            )
    
    async def search_conversations(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10,
        date_range: Optional[Dict[str, datetime]] = None
    ) -> List[Conversation]:
        """Search conversations"""
        try:
            search_filter = {"messages.content": {"$regex": query, "$options": "i"}}
            
            if session_id:
                search_filter["session_id"] = session_id
            
            if date_range:
                if "start" in date_range:
                    search_filter["started_at"] = {"$gte": date_range["start"]}
                if "end" in date_range:
                    search_filter.setdefault("started_at", {})["$lte"] = date_range["end"]
            
            cursor = self.conversations.find(search_filter).limit(limit)
            
            conversations = []
            async for conv_data in cursor:
                conv_data.pop("_id", None)
                conversations.append(Conversation(**conv_data))
            
            return conversations
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="search",
                message=f"Failed to search conversations: {e}"
            )
    
    async def get_conversation_analytics(
        self,
        time_range_days: int = 30,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get conversation analytics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_range_days)
            
            match_filter = {"started_at": {"$gte": cutoff_date}}
            if session_id:
                match_filter["session_id"] = session_id
            
            total_conversations = await self.conversations.count_documents(match_filter)
            
            return {
                "total_conversations": total_conversations,
                "time_range_days": time_range_days,
                "period_start": cutoff_date.isoformat(),
                "session_id": session_id
            }
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="analytics",
                message=f"Failed to get analytics: {e}"
            )
    
    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive conversation"""
        try:
            result = await self.conversations.update_one(
                {"id": conversation_id},
                {"$set": {"status": "archived", "archived_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="archive",
                message=f"Failed to archive conversation: {e}"
            )
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        try:
            result = await self.conversations.delete_one({"id": conversation_id})
            return result.deleted_count > 0
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="delete",
                message=f"Failed to delete conversation: {e}"
            )
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation summary"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if conversation:
                return conversation.get_analytics()
            return None
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="get_summary",
                message=f"Failed to get conversation summary: {e}"
            )
    
    async def get_conversations_by_topic(
        self,
        topic: str,
        limit: int = 10,
        session_id: Optional[str] = None
    ) -> List[Conversation]:
        """Get conversations by topic"""
        try:
            search_filter = {"topics": topic}
            if session_id:
                search_filter["session_id"] = session_id
            
            cursor = self.conversations.find(search_filter).limit(limit)
            
            conversations = []
            async for conv_data in cursor:
                conv_data.pop("_id", None)
                conversations.append(Conversation(**conv_data))
            
            return conversations
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="find_by_topic",
                message=f"Failed to find conversations by topic: {e}"
            )
    
    async def get_user_satisfaction_metrics(
        self,
        time_range_days: int = 30,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user satisfaction metrics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_range_days)
            
            match_filter = {"started_at": {"$gte": cutoff_date}}
            if session_id:
                match_filter["session_id"] = session_id
            
            # Aggregate satisfaction scores
            pipeline = [
                {"$match": match_filter},
                {"$project": {
                    "feedback_count": {"$size": "$feedback"},
                    "messages_count": {"$size": "$messages"}
                }},
                {"$group": {
                    "_id": None,
                    "avg_feedback_count": {"$avg": "$feedback_count"},
                    "avg_messages_count": {"$avg": "$messages_count"},
                    "total_conversations": {"$sum": 1}
                }}
            ]
            
            result = None
            async for doc in self.conversations.aggregate(pipeline):
                result = doc
                break
            
            return {
                "satisfaction_metrics": result or {},
                "time_range_days": time_range_days,
                "session_id": session_id
            }
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="satisfaction_metrics",
                message=f"Failed to get satisfaction metrics: {e}"
            )
    
    async def export_conversations(
        self,
        session_id: Optional[str] = None,
        date_range: Optional[Dict[str, datetime]] = None,
        format: str = "json"
    ) -> str:
        """Export conversations"""
        try:
            search_filter = {}
            if session_id:
                search_filter["session_id"] = session_id
            
            if date_range:
                if "start" in date_range:
                    search_filter["started_at"] = {"$gte": date_range["start"]}
                if "end" in date_range:
                    search_filter.setdefault("started_at", {})["$lte"] = date_range["end"]
            
            conversations = []
            async for conv_data in self.conversations.find(search_filter):
                conv_data.pop("_id", None)
                conversations.append(conv_data)
            
            if format == "json":
                import json
                return json.dumps(conversations, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="export",
                message=f"Failed to export conversations: {e}"
            )
    
    async def cleanup_old_conversations(
        self,
        days_threshold: int = 90,
        keep_with_feedback: bool = True
    ) -> int:
        """Clean up old conversations"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            delete_filter = {
                "started_at": {"$lt": cutoff_date},
                "status": {"$ne": "archived"}
            }
            
            if keep_with_feedback:
                delete_filter["feedback"] = {"$size": 0}
            
            result = await self.conversations.delete_many(delete_filter)
            return result.deleted_count
            
        except Exception as e:
            raise DatabaseError(
                collection="conversations",
                operation="cleanup",
                message=f"Failed to cleanup conversations: {e}"
            )
    
    # Utility Methods
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm_a = np.linalg.norm(vec1_np)
            norm_b = np.linalg.norm(vec2_np)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return float(dot_product / (norm_a * norm_b))
        
        except Exception:
            return 0.0
    
    async def close(self):
        """Close database connection"""
        self.client.close()