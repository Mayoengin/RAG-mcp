# src/network_rag/models/exceptions.py
"""Custom exceptions for the network RAG system"""

from typing import Optional, Dict, Any


class NetworkRAGException(Exception):
    """Base exception for all network RAG system errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ModelValidationError(NetworkRAGException):
    """Raised when model validation fails"""
    
    def __init__(self, model_name: str, field: str, message: str, value: Any = None):
        self.model_name = model_name
        self.field = field
        self.value = value
        details = {
            "model": model_name,
            "field": field,
            "invalid_value": value
        }
        super().__init__(f"Validation error in {model_name}.{field}: {message}", details)


class NetworkAPIError(NetworkRAGException):
    """Raised when network API calls fail"""
    
    def __init__(self, api_endpoint: str, status_code: Optional[int] = None, message: str = "API call failed"):
        self.api_endpoint = api_endpoint
        self.status_code = status_code
        details = {
            "endpoint": api_endpoint,
            "status_code": status_code
        }
        super().__init__(f"Network API error on {api_endpoint}: {message}", details)


class DocumentError(NetworkRAGException):
    """Raised when document operations fail"""
    
    def __init__(self, document_id: Optional[str] = None, operation: Optional[str] = None, message: str = "Document operation failed"):
        self.document_id = document_id
        self.operation = operation
        details = {
            "document_id": document_id,
            "operation": operation
        }
        super().__init__(f"Document error: {message}", details)


class ConversationError(NetworkRAGException):
    """Raised when conversation operations fail"""
    
    def __init__(self, conversation_id: Optional[str] = None, operation: Optional[str] = None, message: str = "Conversation operation failed"):
        self.conversation_id = conversation_id
        self.operation = operation
        details = {
            "conversation_id": conversation_id,
            "operation": operation
        }
        super().__init__(f"Conversation error: {message}", details)


class LLMError(NetworkRAGException):
    """Raised when LLM operations fail"""
    
    def __init__(self, llm_provider: Optional[str] = None, operation: Optional[str] = None, message: str = "LLM operation failed"):
        self.llm_provider = llm_provider
        self.operation = operation
        details = {
            "provider": llm_provider,
            "operation": operation
        }
        super().__init__(f"LLM error: {message}", details)


class EmbeddingError(NetworkRAGException):
    """Raised when embedding operations fail"""
    
    def __init__(self, model_name: Optional[str] = None, text_length: Optional[int] = None, message: str = "Embedding generation failed"):
        self.model_name = model_name
        self.text_length = text_length
        details = {
            "model": model_name,
            "text_length": text_length
        }
        super().__init__(f"Embedding error: {message}", details)


class VectorSearchError(NetworkRAGException):
    """Raised when vector search operations fail"""
    
    def __init__(self, index_name: Optional[str] = None, operation: Optional[str] = None, message: str = "Vector search operation failed"):
        self.index_name = index_name
        self.operation = operation
        details = {
            "index": index_name,
            "operation": operation
        }
        super().__init__(f"Vector search error: {message}", details)


class ConfigurationError(NetworkRAGException):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, config_key: Optional[str] = None, message: str = "Configuration error"):
        self.config_key = config_key
        details = {
            "config_key": config_key
        }
        super().__init__(f"Configuration error: {message}", details)


class DatabaseError(NetworkRAGException):
    """Raised when database operations fail"""
    
    def __init__(self, database: Optional[str] = None, collection: Optional[str] = None, operation: Optional[str] = None, message: str = "Database operation failed"):
        self.database = database
        self.collection = collection
        self.operation = operation
        details = {
            "database": database,
            "collection": collection,
            "operation": operation
        }
        super().__init__(f"Database error: {message}", details)


class AuthenticationError(NetworkRAGException):
    """Raised when authentication fails"""
    
    def __init__(self, service: Optional[str] = None, message: str = "Authentication failed"):
        self.service = service
        details = {
            "service": service
        }
        super().__init__(f"Authentication error: {message}", details)


class RateLimitError(NetworkRAGException):
    """Raised when rate limits are exceeded"""
    
    def __init__(self, service: Optional[str] = None, retry_after: Optional[int] = None, message: str = "Rate limit exceeded"):
        self.service = service
        self.retry_after = retry_after
        details = {
            "service": service,
            "retry_after_seconds": retry_after
        }
        super().__init__(f"Rate limit error: {message}", details)


class TimeoutError(NetworkRAGException):
    """Raised when operations timeout"""
    
    def __init__(self, operation: Optional[str] = None, timeout_seconds: Optional[int] = None, message: str = "Operation timed out"):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        details = {
            "operation": operation,
            "timeout_seconds": timeout_seconds
        }
        super().__init__(f"Timeout error: {message}", details)


class DataQualityError(NetworkRAGException):
    """Raised when data quality issues are detected"""
    
    def __init__(self, data_type: Optional[str] = None, quality_issue: Optional[str] = None, message: str = "Data quality issue detected"):
        self.data_type = data_type
        self.quality_issue = quality_issue
        details = {
            "data_type": data_type,
            "issue": quality_issue
        }
        super().__init__(f"Data quality error: {message}", details)