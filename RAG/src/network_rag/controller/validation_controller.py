# src/network_rag/controller/validation_controller.py
"""Validation controller - simplified business rules and quality assurance"""

from typing import Dict, Any, List
from ..models import FTTHOLTResource, Document, Conversation, QueryResult


class ValidationController:
    """Simplified business logic for validation and quality assurance"""
    
    def validate_ftth_olt(self, olt: FTTHOLTResource) -> Dict[str, Any]:
        """
        FTTH OLT business rule validation
        
        Business Rules:
        - Production systems must have complete configs
        - Connection types must match environment needs
        - Regional standards must be followed
        """
        
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "compliance_score": 1.0
        }
        
        # Business Rule: Production requirements
        if olt.is_production():
            if not olt.host_address:
                result["errors"].append("Production OLT must have host address")
                result["is_valid"] = False
            
            if not olt.connection_type:
                result["errors"].append("Production OLT must have connection type")
                result["is_valid"] = False
            
            bandwidth = olt.calculate_bandwidth_gbps()
            if bandwidth < 10:
                result["warnings"].append("Production bandwidth may be insufficient")
        
        # Business Rule: Regional standards
        if olt.region == "HOBO":
            if olt.calculate_bandwidth_gbps() < 40:
                result["recommendations"].append("HOBO region typically uses 4x10G connections")
            
            if not olt.managed_by_inmanta:
                result["recommendations"].append("HOBO region standardizes on Inmanta management")
        
        # Business Rule: Configuration completeness
        completeness_score = olt.get_configuration_completeness_score()
        if completeness_score < 0.5:
            result["errors"].append(f"Configuration severely incomplete ({completeness_score:.1%})")
            result["is_valid"] = False
        elif completeness_score < 0.7:
            result["warnings"].append(f"Configuration partially incomplete ({completeness_score:.1%})")
        
        # Calculate compliance score
        error_penalty = len(result["errors"]) * 0.3
        warning_penalty = len(result["warnings"]) * 0.1
        result["compliance_score"] = max(0.0, 1.0 - error_penalty - warning_penalty)
        
        return result
    
    def validate_document_quality(self, document: Document) -> Dict[str, Any]:
        """
        Document quality validation
        
        Business Rules:
        - Content must meet minimum standards
        - Metadata must be complete
        - Content must be fresh and useful
        """
        
        result = {
            "is_valid": True,
            "quality_score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        # Content validation
        if len(document.content) < 50:
            result["issues"].append("Content too short")
            result["is_valid"] = False
        
        if len(document.title) < 5:
            result["issues"].append("Title too short")
            result["is_valid"] = False
        
        # Metadata validation
        if len(document.keywords) < 3:
            result["recommendations"].append("Add more keywords for better discoverability")
        
        # Quality assessment
        quality_factors = []
        
        # Content length factor
        if len(document.content) > 200:
            quality_factors.append(0.3)
        elif len(document.content) > 100:
            quality_factors.append(0.2)
        else:
            quality_factors.append(0.1)
        
        # Structure factor
        if any(marker in document.content for marker in ["\n\n", "1.", "•", "-"]):
            quality_factors.append(0.2)
        else:
            quality_factors.append(0.1)
        
        # Usefulness factor
        quality_factors.append(document.usefulness_score * 0.3)
        
        # Freshness factor
        if not document.is_stale(90):
            quality_factors.append(0.2)
        elif not document.is_stale(180):
            quality_factors.append(0.1)
        else:
            quality_factors.append(0.0)
            result["recommendations"].append("Content should be reviewed for currency")
        
        result["quality_score"] = sum(quality_factors)
        
        # Document type specific validation
        if document.document_type.value == "troubleshooting":
            if not any(word in document.content.lower() for word in ["step", "solution", "procedure"]):
                result["recommendations"].append("Troubleshooting docs should include step-by-step guidance")
        
        elif document.document_type.value == "config_guide":
            if not any(word in document.content.lower() for word in ["configure", "setting", "example"]):
                result["recommendations"].append("Configuration guides should include examples")
        
        return result
    
    def validate_conversation_quality(self, conversation: Conversation) -> Dict[str, Any]:
        """
        Conversation quality validation
        
        Business Rules:
        - Conversations should show resolution progress
        - Response quality should meet standards
        - User satisfaction should be positive
        """
        
        result = {
            "quality_score": 0.5,
            "resolution_status": "ongoing",
            "issues": [],
            "insights": []
        }
        
        # Resolution assessment
        satisfaction = conversation.calculate_satisfaction_score()
        turn_count = conversation.get_turn_count()
        
        if satisfaction > 0.8:
            result["resolution_status"] = "well_resolved"
            result["quality_score"] = 0.9
        elif satisfaction > 0.6:
            result["resolution_status"] = "adequately_resolved"
            result["quality_score"] = 0.7
        elif turn_count > 5 and satisfaction < 0.4:
            result["resolution_status"] = "poorly_resolved"
            result["quality_score"] = 0.3
            result["issues"].append("Extended conversation with low satisfaction")
        
        # Response quality assessment
        assistant_messages = conversation.get_assistant_messages()
        if assistant_messages:
            avg_length = sum(len(msg.content) for msg in assistant_messages) / len(assistant_messages)
            
            if avg_length < 50:
                result["issues"].append("Responses may be too brief")
            elif avg_length > 1000:
                result["insights"].append("Responses are comprehensive but may be verbose")
        
        # Engagement assessment
        if len(conversation.feedback) > 0:
            result["insights"].append("User provided feedback - valuable for learning")
        
        if turn_count == 1 and satisfaction > 0.8:
            result["insights"].append("Excellent single-turn resolution")
        
        return result
    
    def validate_query_result(self, query_result: QueryResult) -> Dict[str, Any]:
        """
        Query result quality validation
        
        Business Rules:
        - Results must have adequate confidence
        - Sources must be diverse and reliable
        - Answers must be complete and helpful
        """
        
        result = {
            "is_valid": True,
            "confidence_level": query_result.get_confidence_level().value,
            "issues": [],
            "recommendations": []
        }
        
        # Confidence validation
        if query_result.overall_confidence < 0.3:
            result["issues"].append("Confidence below acceptable threshold")
            result["is_valid"] = False
        elif query_result.overall_confidence < 0.6:
            result["recommendations"].append("Consider improving data sources for higher confidence")
        
        # Source diversity validation
        if query_result.sources:
            source_types = set(source.source_type for source in query_result.sources)
            if len(source_types) < 2:
                result["recommendations"].append("Limited source diversity - consider additional data sources")
            
            avg_source_confidence = sum(s.confidence for s in query_result.sources) / len(query_result.sources)
            if avg_source_confidence < 0.6:
                result["recommendations"].append("Improve source quality or filtering thresholds")
        else:
            result["issues"].append("No sources provided for result validation")
            result["is_valid"] = False
        
        # Answer completeness validation
        if len(query_result.primary_answer) < 50:
            result["issues"].append("Answer too brief for comprehensive response")
        
        if not query_result.supporting_data:
            result["recommendations"].append("Consider providing supporting data for validation")
        
        # Performance validation
        if query_result.processing_time_ms and query_result.processing_time_ms > 10000:
            result["issues"].append("Processing time exceeds acceptable threshold")
        
        return result
    
    def validate_system_health(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        System-wide health validation
        
        Business Rules:
        - Overall system performance must be acceptable
        - Data quality must meet standards
        - User satisfaction must be positive
        """
        
        health_result = {
            "overall_health": "healthy",
            "health_score": 0.8,
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Response time health
        avg_response_time = metrics.get("avg_response_time_ms", 2000)
        if avg_response_time > 10000:
            health_result["critical_issues"].append("Average response time too high")
            health_result["overall_health"] = "unhealthy"
        elif avg_response_time > 5000:
            health_result["warnings"].append("Response times elevated")
        
        # Confidence health
        avg_confidence = metrics.get("avg_confidence", 0.7)
        if avg_confidence < 0.5:
            health_result["critical_issues"].append("System confidence too low")
            health_result["overall_health"] = "unhealthy"
        elif avg_confidence < 0.7:
            health_result["warnings"].append("System confidence below target")
        
        # User satisfaction health
        satisfaction_rate = metrics.get("user_satisfaction_rate", 0.75)
        if satisfaction_rate < 0.5:
            health_result["critical_issues"].append("User satisfaction critically low")
            health_result["overall_health"] = "unhealthy"
        elif satisfaction_rate < 0.7:
            health_result["warnings"].append("User satisfaction below target")
        
        # Document quality health
        doc_quality_avg = metrics.get("document_quality_avg", 0.7)
        if doc_quality_avg < 0.5:
            health_result["warnings"].append("Document quality needs improvement")
        
        # Calculate overall health score
        factors = [
            min(1.0, 5000 / avg_response_time) if avg_response_time > 0 else 1.0,  # Response time factor
            avg_confidence,  # Confidence factor
            satisfaction_rate,  # Satisfaction factor
            doc_quality_avg  # Quality factor
        ]
        
        health_result["health_score"] = sum(factors) / len(factors)
        
        # Determine overall health status
        if len(health_result["critical_issues"]) > 0:
            health_result["overall_health"] = "unhealthy"
        elif len(health_result["warnings"]) > 2:
            health_result["overall_health"] = "degraded"
        elif health_result["health_score"] > 0.8:
            health_result["overall_health"] = "healthy"
        else:
            health_result["overall_health"] = "fair"
        
        # Generate recommendations
        if avg_response_time > 3000:
            health_result["recommendations"].append("Optimize query processing for better performance")
        
        if avg_confidence < 0.8:
            health_result["recommendations"].append("Improve data source quality and coverage")
        
        if satisfaction_rate < 0.8:
            health_result["recommendations"].append("Review user feedback to identify improvement areas")
        
        return health_result