# src/network_rag/models/__init__.py
"""Domain models for the network RAG system"""

# Core domain models
from .ftth_olt_resource import FTTHOLTResource, Environment, ConnectionType
from .document import Document, DocumentType
from .conversation import Conversation, Message, Feedback, MessageRole, FeedbackType, ConversationSummary
from .query_result import QueryResult, ResultSource, SourceType, ConfidenceLevel

# Exceptions
from .exceptions import (
    NetworkRAGException,
    ModelValidationError,
    NetworkAPIError,
    DocumentError,
    ConversationError,
    LLMError,
    EmbeddingError,
    VectorSearchError,
    ConfigurationError,
    DatabaseError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    DataQualityError
)

# Port interfaces (imported for convenience)
from .ports import (
    NetworkPort,
    KnowledgePort,
    VectorSearchPort,
    LLMPort,
    ConversationPort
)

__all__ = [
    # Core models
    "FTTHOLTResource",
    "Environment",
    "ConnectionType",
    "Document",
    "DocumentType", 
    "Conversation",
    "Message",
    "Feedback",
    "MessageRole",
    "FeedbackType",
    "ConversationSummary",
    "QueryResult",
    "ResultSource",
    "SourceType",
    "ConfidenceLevel",
    
    # Exceptions
    "NetworkRAGException",
    "ModelValidationError",
    "NetworkAPIError",
    "DocumentError",
    "ConversationError",
    "LLMError",
    "EmbeddingError",
    "VectorSearchError",
    "ConfigurationError",
    "DatabaseError",
    "AuthenticationError",
    "RateLimitError",
    "TimeoutError",
    "DataQualityError",
    
    # Ports
    "NetworkPort",
    "KnowledgePort",
    "VectorSearchPort", 
    "LLMPort",
    "ConversationPort"
]