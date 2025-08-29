# src/network_rag/models/document.py
"""Knowledge base document domain model"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    """Types of knowledge base documents"""
    CONFIGURATION_GUIDE = "config_guide"
    TROUBLESHOOTING = "troubleshooting"
    BEST_PRACTICES = "best_practices"
    API_REFERENCE = "api_reference"
    NETWORK_DOCUMENTATION = "network_docs"
    USER_MANUAL = "user_manual"


class Document(BaseModel):
    """Knowledge base document with embeddings and metadata"""
    
    # Core content
    id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content/body")
    document_type: DocumentType = Field(..., description="Type of document")
    
    # Search and embeddings
    embedding: Optional[List[float]] = Field(None, description="Vector embedding for similarity search")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords for search")
    
    # Metadata
    source: str = Field("system", description="Source of the document")
    author: Optional[str] = Field(None, description="Document author")
    version: str = Field("1.0", description="Document version")
    language: str = Field("en", description="Document language")
    
    # Classification
    topics: List[str] = Field(default_factory=list, description="Topic categories")
    tags: List[str] = Field(default_factory=list, description="Custom tags")
    
    # Quality metrics
    view_count: int = Field(0, description="Number of times accessed")
    usefulness_score: float = Field(0.0, description="User feedback score")
    last_reviewed: Optional[datetime] = Field(None, description="Last review date")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
        validate_assignment = True
    
    # Domain methods
    def needs_embedding(self) -> bool:
        """Check if document needs embedding generation"""
        return self.embedding is None or len(self.embedding) == 0
    
    def calculate_relevance(self, query_embedding: List[float]) -> float:
        """Calculate relevance score against query embedding using cosine similarity"""
        if not self.embedding or not query_embedding:
            return 0.0
        
        try:
            import numpy as np
            
            # Convert to numpy arrays
            doc_vec = np.array(self.embedding)
            query_vec = np.array(query_embedding)
            
            # Calculate cosine similarity
            dot_product = np.dot(doc_vec, query_vec)
            norm_doc = np.linalg.norm(doc_vec)
            norm_query = np.linalg.norm(query_vec)
            
            if norm_doc == 0 or norm_query == 0:
                return 0.0
            
            return float(dot_product / (norm_doc * norm_query))
        
        except Exception:
            return 0.0
    
    def get_content_preview(self, max_length: int = 200) -> str:
        """Get truncated content preview"""
        if len(self.content) <= max_length:
            return self.content
        
        # Find the last complete sentence within the limit
        truncated = self.content[:max_length]
        last_sentence_end = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        
        if last_sentence_end > max_length // 2:  # If we found a reasonable break point
            return truncated[:last_sentence_end + 1]
        else:
            return truncated + "..."
    
    def increment_view_count(self) -> None:
        """Increment view count when document is accessed"""
        self.view_count += 1
    
    def update_usefulness_score(self, feedback_score: float) -> None:
        """Update usefulness score based on user feedback"""
        if not 0.0 <= feedback_score <= 1.0:
            raise ValueError("Feedback score must be between 0.0 and 1.0")
        
        # Running average of usefulness scores
        current_weight = 0.8  # Weight for existing score
        new_weight = 0.2      # Weight for new feedback
        
        self.usefulness_score = (
            self.usefulness_score * current_weight + 
            feedback_score * new_weight
        )
    
    def mark_as_reviewed(self) -> None:
        """Mark document as reviewed today"""
        self.last_reviewed = datetime.utcnow()
    
    def is_stale(self, days_threshold: int = 180) -> bool:
        """Check if document is potentially stale and needs review"""
        if not self.last_reviewed:
            # If never reviewed, check age
            age_days = (datetime.utcnow() - self.created_at).days
            return age_days > days_threshold
        
        days_since_review = (datetime.utcnow() - self.last_reviewed).days
        return days_since_review > days_threshold
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get comprehensive quality metrics"""
        content_length = len(self.content)
        word_count = len(self.content.split())
        
        return {
            "content_length": content_length,
            "word_count": word_count,
            "keyword_count": len(self.keywords),
            "topic_count": len(self.topics),
            "view_count": self.view_count,
            "usefulness_score": round(self.usefulness_score, 2),
            "has_embedding": not self.needs_embedding(),
            "is_stale": self.is_stale(),
            "days_since_update": (datetime.utcnow() - self.updated_at).days
        }