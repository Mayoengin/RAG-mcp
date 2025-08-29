# src/network_rag/models/query_result.py
"""Query result domain model with multi-source data fusion"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class SourceType(str, Enum):
    """Types of data sources for query results"""
    NETWORK_API = "network_api"
    KNOWLEDGE_BASE = "knowledge_base"
    CONVERSATION_HISTORY = "conversation_history"
    LLM_GENERATION = "llm_generation"
    CACHED_RESULT = "cached_result"
    EXTERNAL_API = "external_api"


class ConfidenceLevel(str, Enum):
    """Confidence levels for query results"""
    VERY_HIGH = "very_high"    # 0.9 - 1.0
    HIGH = "high"              # 0.7 - 0.9
    MEDIUM = "medium"          # 0.5 - 0.7
    LOW = "low"                # 0.3 - 0.5
    VERY_LOW = "very_low"      # 0.0 - 0.3


class ResultSource(BaseModel):
    """Information about a data source that contributed to the result"""
    
    # Source identification
    source_type: SourceType = Field(..., description="Type of data source")
    source_id: str = Field(..., description="Unique identifier for the source")
    source_name: Optional[str] = Field(None, description="Human-readable source name")
    
    # Quality metrics
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this source")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance to query")
    freshness_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Data freshness")
    
    # Content information
    content_summary: Optional[str] = Field(None, description="Brief summary of contribution")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific metadata")
    
    # Timestamps
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """Get categorical confidence level"""
        if self.confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


class QueryResult(BaseModel):
    """Comprehensive query result with multi-source data fusion and analytics"""
    
    # Query identification
    query_id: str = Field(..., description="Unique query identifier")
    original_query: str = Field(..., description="Original user query")
    processed_query: str = Field(..., description="Processed/normalized query")
    query_intent: Optional[str] = Field(None, description="Detected query intent")
    
    # Core results
    primary_answer: str = Field(..., description="Main answer to the query")
    secondary_answers: List[str] = Field(default_factory=list, description="Alternative answers")
    supporting_data: Dict[str, Any] = Field(default_factory=dict, description="Supporting data from sources")
    
    # Source information
    sources: List[ResultSource] = Field(default_factory=list, description="Data sources used")
    
    # Quality metrics
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall result confidence")
    completeness_score: float = Field(0.0, ge=0.0, le=1.0, description="How complete the answer is")
    accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Estimated accuracy")
    
    # Reasoning and explanation
    reasoning: Optional[str] = Field(None, description="Explanation of how answer was derived")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made")
    limitations: List[str] = Field(default_factory=list, description="Known limitations")
    
    # Context information
    conversation_id: Optional[str] = Field(None, description="Associated conversation")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context")
    session_context: Dict[str, Any] = Field(default_factory=dict, description="Session context")
    
    # Performance metrics
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = Field(None, description="Total processing time")
    source_retrieval_time_ms: Optional[int] = Field(None, description="Time to retrieve sources")
    llm_generation_time_ms: Optional[int] = Field(None, description="Time for LLM generation")
    
    # Follow-up suggestions
    suggested_questions: List[str] = Field(default_factory=list, description="Related questions")
    related_topics: List[str] = Field(default_factory=list, description="Related topics")
    
    class Config:
        use_enum_values = True
        validate_assignment = True
    
    # Domain methods
    def add_source(
        self, 
        source_type: SourceType, 
        source_id: str, 
        confidence: float,
        source_name: Optional[str] = None,
        content_summary: Optional[str] = None,
        **metadata
    ) -> None:
        """Add a data source to the result"""
        source = ResultSource(
            source_type=source_type,
            source_id=source_id,
            source_name=source_name,
            confidence=confidence,
            content_summary=content_summary,
            metadata=metadata
        )
        self.sources.append(source)
    
    def calculate_overall_confidence(self) -> float:
        """Calculate overall confidence from all sources using weighted average"""
        if not self.sources:
            return 0.0
        
        # Define weights for different source types
        source_weights = {
            SourceType.NETWORK_API: 0.35,        # High weight for real network data
            SourceType.KNOWLEDGE_BASE: 0.25,     # Medium-high for curated knowledge
            SourceType.CONVERSATION_HISTORY: 0.15, # Medium for context
            SourceType.LLM_GENERATION: 0.15,     # Medium for AI reasoning
            SourceType.CACHED_RESULT: 0.05,      # Lower for cached data
            SourceType.EXTERNAL_API: 0.05        # Lower for external sources
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for source in self.sources:
            weight = source_weights.get(source.source_type, 0.1)
            weighted_sum += source.confidence * weight
            total_weight += weight
        
        confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        self.overall_confidence = confidence
        return confidence
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """Get categorical confidence level for the overall result"""
        if self.overall_confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.overall_confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.overall_confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif self.overall_confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def get_top_sources(self, limit: int = 3) -> List[ResultSource]:
        """Get highest confidence sources"""
        return sorted(
            self.sources, 
            key=lambda x: x.confidence, 
            reverse=True
        )[:limit]
    
    def get_sources_by_type(self, source_type: SourceType) -> List[ResultSource]:
        """Get all sources of a specific type"""
        return [source for source in self.sources if source.source_type == source_type]
    
    def has_network_data(self) -> bool:
        """Check if result includes real network data"""
        return any(
            source.source_type == SourceType.NETWORK_API 
            for source in self.sources
        )
    
    def has_knowledge_base_data(self) -> bool:
        """Check if result includes knowledge base information"""
        return any(
            source.source_type == SourceType.KNOWLEDGE_BASE 
            for source in self.sources
        )
    
    def get_processing_breakdown(self) -> Dict[str, Any]:
        """Get detailed processing time breakdown"""
        total_time = self.processing_time_ms or 0
        
        breakdown = {
            "total_processing_time_ms": total_time,
            "source_retrieval_time_ms": self.source_retrieval_time_ms,
            "llm_generation_time_ms": self.llm_generation_time_ms,
            "other_processing_time_ms": None
        }
        
        # Calculate other processing time
        if total_time and self.source_retrieval_time_ms and self.llm_generation_time_ms:
            other_time = total_time - self.source_retrieval_time_ms - self.llm_generation_time_ms
            breakdown["other_processing_time_ms"] = max(0, other_time)
        
        return breakdown
    
    def add_limitation(self, limitation: str) -> None:
        """Add a known limitation to the result"""
        if limitation not in self.limitations:
            self.limitations.append(limitation)
    
    def add_assumption(self, assumption: str) -> None:
        """Add an assumption made during processing"""
        if assumption not in self.assumptions:
            self.assumptions.append(assumption)
    
    def add_suggested_question(self, question: str) -> None:
        """Add a follow-up question suggestion"""
        if question not in self.suggested_questions:
            self.suggested_questions.append(question)
    
    def add_related_topic(self, topic: str) -> None:
        """Add a related topic"""
        if topic not in self.related_topics:
            self.related_topics.append(topic)
    
    def is_complete(self) -> bool:
        """Check if the result appears to be complete"""
        return (
            len(self.primary_answer) > 50 and  # Substantial answer
            len(self.sources) > 0 and          # Has sources
            self.overall_confidence > 0.3 and # Reasonable confidence
            self.completeness_score > 0.5     # Good completeness
        )
    
    def needs_human_review(self) -> bool:
        """Check if result should be reviewed by human"""
        return (
            self.overall_confidence < 0.5 or     # Low confidence
            len(self.limitations) > 2 or         # Many limitations
            "error" in self.primary_answer.lower() # Contains error messages
        )
    
    def get_quality_score(self) -> float:
        """Calculate overall quality score (0.0 to 1.0)"""
        factors = [
            self.overall_confidence,
            self.completeness_score,
            min(1.0, len(self.sources) / 3.0),  # Source diversity bonus
            1.0 if len(self.primary_answer) > 100 else 0.5,  # Answer length
            1.0 if self.reasoning else 0.7  # Reasoning provided
        ]
        
        # Remove None values
        valid_factors = [f for f in factors if f is not None]
        
        if not valid_factors:
            return 0.0
        
        return sum(valid_factors) / len(valid_factors)
    
    def to_summary(self) -> Dict[str, Any]:
        """Get a summary representation of the result"""
        return {
            "query_id": self.query_id,
            "original_query": self.original_query,
            "answer_preview": self.primary_answer[:200] + "..." if len(self.primary_answer) > 200 else self.primary_answer,
            "confidence_level": self.get_confidence_level().value,
            "overall_confidence": round(self.overall_confidence, 2),
            "completeness_score": round(self.completeness_score, 2),
            "quality_score": round(self.get_quality_score(), 2),
            "source_count": len(self.sources),
            "source_types": list(set(source.source_type.value for source in self.sources)),
            "has_network_data": self.has_network_data(),
            "has_knowledge_data": self.has_knowledge_base_data(),
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "is_complete": self.is_complete(),
            "needs_review": self.needs_human_review()
        }
    
    def to_detailed_report(self) -> Dict[str, Any]:
        """Get detailed report for analysis and debugging"""
        return {
            "query_info": {
                "query_id": self.query_id,
                "original_query": self.original_query,
                "processed_query": self.processed_query,
                "query_intent": self.query_intent
            },
            "results": {
                "primary_answer": self.primary_answer,
                "secondary_answers": self.secondary_answers,
                "supporting_data_keys": list(self.supporting_data.keys())
            },
            "sources": [
                {
                    "type": source.source_type.value,
                    "id": source.source_id,
                    "name": source.source_name,
                    "confidence": round(source.confidence, 3),
                    "confidence_level": source.get_confidence_level().value,
                    "summary": source.content_summary,
                    "metadata_keys": list(source.metadata.keys())
                }
                for source in self.sources
            ],
            "quality_metrics": {
                "overall_confidence": round(self.overall_confidence, 3),
                "completeness_score": round(self.completeness_score, 3),
                "accuracy_score": round(self.accuracy_score, 3) if self.accuracy_score else None,
                "quality_score": round(self.get_quality_score(), 3),
                "confidence_level": self.get_confidence_level().value
            },
            "processing_info": self.get_processing_breakdown(),
            "context": {
                "conversation_id": self.conversation_id,
                "user_context_keys": list(self.user_context.keys()),
                "session_context_keys": list(self.session_context.keys())
            },
            "metadata": {
                "reasoning": self.reasoning,
                "assumptions": self.assumptions,
                "limitations": self.limitations,
                "suggested_questions": self.suggested_questions,
                "related_topics": self.related_topics,
                "timestamp": self.timestamp.isoformat(),
                "is_complete": self.is_complete(),
                "needs_review": self.needs_human_review()
            }
        }