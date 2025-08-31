# src/network_rag/controller/document_controller.py
"""Document management controller - refined and focused business logic"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import (
    Document, DocumentType,
    VectorSearchPort, LLMPort,
    DocumentError
)


class DocumentController:
    """Simplified business logic for knowledge base document management"""
    
    def __init__(
        self,
        knowledge_port: VectorSearchPort,
        vector_search_port: VectorSearchPort,
        llm_port: LLMPort
    ):
        self.knowledge_port = knowledge_port
        self.vector_search_port = vector_search_port
        self.llm_port = llm_port
    
    async def create_document(
        self,
        title: str,
        content: str,
        document_type: DocumentType,
        author: Optional[str] = None,
        source: str = "system"
    ) -> str:
        """
        Create document with business validation and auto-indexing
        
        Business Rules:
        - Content must meet minimum quality standards
        - Auto-generate keywords and topics
        - Index for similarity search
        """
        
        # Business Rule: Content validation
        self._validate_content_quality(title, content)
        
        # Business Rule: Auto-generate metadata
        keywords = await self.llm_port.extract_keywords(content, max_keywords=8)
        
        # Create document
        document = Document(
            id=f"doc_{int(datetime.utcnow().timestamp())}_{hash(title) % 10000}",
            title=title.strip(),
            content=content.strip(),
            document_type=document_type,
            keywords=keywords,
            author=author,
            source=source
        )
        
        # Store and index
        doc_id = await self.knowledge_port.store_document(document)
        await self._index_document(document)
        
        return doc_id
    
    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update document with validation and re-indexing
        
        Business Rules:
        - Validate content changes
        - Re-generate metadata if content changed
        - Re-index if content changed
        """
        
        document = await self.knowledge_port.get_document(document_id)
        if not document:
            raise DocumentError(f"Document {document_id} not found")
        
        content_changed = False
        
        # Apply updates
        if "content" in updates:
            new_content = updates["content"].strip()
            self._validate_content_quality(document.title, new_content)
            document.content = new_content
            content_changed = True
        
        if "title" in updates:
            document.title = updates["title"].strip()
        
        # Business Rule: Update metadata if content changed
        if content_changed:
            document.keywords = await self.llm_port.extract_keywords(document.content, max_keywords=8)
        
        document.updated_at = datetime.utcnow()
        
        # Update storage
        success = await self.knowledge_port.update_document(document)
        
        # Business Rule: Re-index if content changed
        if success and content_changed:
            await self._index_document(document)
        
        return success
    
    async def search_documents(
        self, 
        query: str,
        limit: int = 10,
        use_vector_search: bool = True
    ) -> List[Document]:
        """
        Smart document search with business ranking
        
        Business Rules:
        - Use vector search for semantic matching
        - Apply quality filters
        - Rank by business value (relevance + quality + recency)
        """
        
        if len(query.strip()) < 3:
            raise DocumentError("Search query must be at least 3 characters")
        
        if use_vector_search:
            # Business Rule: Semantic search
            query_embedding = await self.llm_port.generate_embedding(query)
            results = await self.vector_search_port.similarity_search(
                query_embedding,
                limit=limit * 2,  # Get more for filtering
                threshold=0.5
            )
            
            # Business Rule: Quality filtering and ranking
            filtered_docs = []
            for doc, similarity in results:
                if doc.usefulness_score > 0.3:  # Quality threshold
                    filtered_docs.append((doc, similarity))
            
            # Business Rule: Rank by business value
            ranked_docs = self._rank_by_business_value(filtered_docs)
            return [doc for doc, score in ranked_docs[:limit]]
        
        else:
            # Text search fallback
            return await self.knowledge_port.search_documents(query, limit)
    
    async def get_document_recommendations(
        self, 
        document_id: str, 
        limit: int = 5
    ) -> List[Document]:
        """
        Get related document recommendations
        
        Business Rules:
        - Find semantically similar documents
        - Filter by quality score
        - Avoid stale content
        """
        
        similar_docs = await self.vector_search_port.find_similar_documents(
            document_id, 
            limit=limit * 2,
            threshold=0.6
        )
        
        # Business Rule: Quality filtering
        recommendations = []
        for doc, similarity in similar_docs:
            if doc.usefulness_score > 0.4 and not doc.is_stale(90):
                recommendations.append(doc)
        
        return recommendations[:limit]
    
    async def analyze_document_performance(self) -> Dict[str, Any]:
        """
        Document performance analytics
        
        Business Rules:
        - Identify high/low performing content
        - Detect content gaps
        - Generate actionable insights
        """
        
        stats = await self.knowledge_port.get_document_statistics()
        recent_docs = await self.knowledge_port.get_recent_documents(limit=50)
        
        # Business analysis
        performance_analysis = {
            "total_documents": stats.get("total_documents", 0),
            "quality_distribution": self._analyze_quality_distribution(recent_docs),
            "content_health": self._assess_content_health(recent_docs),
            "recommendations": self._generate_improvement_recommendations(recent_docs)
        }
        
        return performance_analysis
    
    def _validate_content_quality(self, title: str, content: str) -> None:
        """Business rule: Content quality validation"""
        
        if len(content.strip()) < 50:
            raise DocumentError("Content must be at least 50 characters")
        
        if len(title.strip()) < 5:
            raise DocumentError("Title must be at least 5 characters")
    
    async def _index_document(self, document: Document) -> None:
        """Business rule: Document indexing for search"""
        
        try:
            embedding = await self.llm_port.generate_embedding(document.content)
            document.embedding = embedding
            
            await self.vector_search_port.index_document(document, embedding)
            await self.knowledge_port.update_document(document)
            
        except Exception as e:
            # Log but don't fail
            print(f"Warning: Could not index document {document.id}: {e}")
    
    def _rank_by_business_value(self, doc_similarity_pairs: List[tuple]) -> List[tuple]:
        """Business rule: Rank documents by business value"""
        
        def calculate_business_value(doc_sim_pair):
            doc, similarity = doc_sim_pair
            
            # Multi-factor ranking: relevance + quality + recency
            relevance_score = similarity * 0.5
            quality_score = doc.usefulness_score * 0.3
            recency_score = (0.2 if not doc.is_stale(30) else 0.1)
            
            return relevance_score + quality_score + recency_score
        
        return sorted(doc_similarity_pairs, key=calculate_business_value, reverse=True)
    
    def _analyze_quality_distribution(self, documents: List[Document]) -> Dict[str, Any]:
        """Business rule: Analyze content quality distribution"""
        
        if not documents:
            return {"message": "No documents to analyze"}
        
        quality_scores = [doc.usefulness_score for doc in documents]
        
        return {
            "average_quality": round(sum(quality_scores) / len(quality_scores), 2),
            "high_quality_count": len([s for s in quality_scores if s > 0.7]),
            "low_quality_count": len([s for s in quality_scores if s < 0.4])
        }
    
    def _assess_content_health(self, documents: List[Document]) -> Dict[str, Any]:
        """Business rule: Assess overall content health"""
        
        if not documents:
            return {"status": "no_data"}
        
        stale_count = len([doc for doc in documents if doc.is_stale(90)])
        health_score = 1.0 - (stale_count / len(documents))
        
        return {
            "health_score": round(health_score, 2),
            "stale_documents": stale_count,
            "total_documents": len(documents),
            "status": "good" if health_score > 0.8 else "needs_attention"
        }
    
    def _generate_improvement_recommendations(self, documents: List[Document]) -> List[str]:
        """Business rule: Generate content improvement recommendations"""
        
        recommendations = []
        
        if not documents:
            return ["Add content to knowledge base"]
        
        # Quality-based recommendations
        low_quality_count = len([doc for doc in documents if doc.usefulness_score < 0.5])
        if low_quality_count > len(documents) * 0.3:
            recommendations.append("Focus on improving content quality - 30%+ of content has low usefulness scores")
        
        # Freshness recommendations
        stale_count = len([doc for doc in documents if doc.is_stale(90)])
        if stale_count > 5:
            recommendations.append(f"Review and update {stale_count} stale documents")
        
        # Coverage recommendations
        doc_types = {}
        for doc in documents:
            doc_types[doc.document_type.value] = doc_types.get(doc.document_type.value, 0) + 1
        
        if doc_types.get("troubleshooting", 0) < len(documents) * 0.2:
            recommendations.append("Increase troubleshooting documentation")
        
        return recommendations