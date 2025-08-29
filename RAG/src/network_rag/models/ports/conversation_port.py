# src/network_rag/models/ports/conversation_port.py
"""Conversation management port interface"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..conversation import Conversation, Message, Feedback


class ConversationPort(ABC):
    """Interface for conversation storage and management"""
    
    @abstractmethod
    async def create_conversation(
        self, 
        session_id: str, 
        user_context: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Create new conversation
        
        Args:
            session_id: Session identifier for grouping
            user_context: Context information about the user
            conversation_id: Optional custom conversation ID
            
        Returns:
            Created conversation ID
            
        Raises:
            ConversationError: When creation fails
        """
        pass
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            Conversation if found, None otherwise
            
        Raises:
            ConversationError: When retrieval fails
        """
        pass
    
    @abstractmethod
    async def update_conversation(self, conversation: Conversation) -> bool:
        """
        Update entire conversation object
        
        Args:
            conversation: Updated conversation object
            
        Returns:
            True if updated successfully
            
        Raises:
            ConversationError: When update fails
        """
        pass
    
    @abstractmethod
    async def add_message(self, conversation_id: str, message: Message) -> bool:
        """
        Add message to conversation
        
        Args:
            conversation_id: Target conversation
            message: Message to add
            
        Returns:
            True if added successfully
            
        Raises:
            ConversationError: When message addition fails
        """
        pass
    
    @abstractmethod
    async def add_feedback(self, conversation_id: str, feedback: Feedback) -> bool:
        """
        Add user feedback to conversation
        
        Args:
            conversation_id: Target conversation
            feedback: Feedback to add
            
        Returns:
            True if added successfully
            
        Raises:
            ConversationError: When feedback addition fails
        """
        pass
    
    @abstractmethod
    async def get_recent_conversations(
        self, 
        session_id: str, 
        limit: int = 10,
        include_archived: bool = False
    ) -> List[Conversation]:
        """
        Get recent conversations for session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of conversations
            include_archived: Whether to include archived conversations
            
        Returns:
            List of recent conversations
            
        Raises:
            ConversationError: When retrieval fails
        """
        pass
    
    @abstractmethod
    async def search_conversations(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        limit: int = 10,
        date_range: Optional[Dict[str, datetime]] = None
    ) -> List[Conversation]:
        """
        Search conversations by content
        
        Args:
            query: Search query text
            session_id: Optional session filter
            limit: Maximum number of results
            date_range: Optional date range filter
            
        Returns:
            List of matching conversations
            
        Raises:
            ConversationError: When search fails
        """
        pass
    
    @abstractmethod
    async def get_conversation_analytics(
        self, 
        time_range_days: int = 30,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get conversation analytics and metrics
        
        Args:
            time_range_days: Number of days to analyze
            session_id: Optional session filter
            
        Returns:
            Analytics dictionary with metrics
            
        Raises:
            ConversationError: When analytics retrieval fails
        """
        pass
    
    @abstractmethod
    async def archive_conversation(self, conversation_id: str) -> bool:
        """
        Archive a conversation (soft delete)
        
        Args:
            conversation_id: Conversation to archive
            
        Returns:
            True if archived successfully
            
        Raises:
            ConversationError: When archiving fails
        """
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Permanently delete a conversation
        
        Args:
            conversation_id: Conversation to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            ConversationError: When deletion fails
        """
        pass
    
    @abstractmethod
    async def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation summary and key metrics
        
        Args:
            conversation_id: Conversation to summarize
            
        Returns:
            Summary dictionary if conversation exists
            
        Raises:
            ConversationError: When summary generation fails
        """
        pass
    
    @abstractmethod
    async def get_conversations_by_topic(
        self, 
        topic: str, 
        limit: int = 10,
        session_id: Optional[str] = None
    ) -> List[Conversation]:
        """
        Get conversations that discuss a specific topic
        
        Args:
            topic: Topic to search for
            limit: Maximum number of results
            session_id: Optional session filter
            
        Returns:
            List of conversations about the topic
            
        Raises:
            ConversationError: When topic search fails
        """
        pass
    
    @abstractmethod
    async def get_user_satisfaction_metrics(
        self,
        time_range_days: int = 30,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user satisfaction metrics based on feedback
        
        Args:
            time_range_days: Number of days to analyze
            session_id: Optional session filter
            
        Returns:
            Satisfaction metrics dictionary
            
        Raises:
            ConversationError: When metrics retrieval fails
        """
        pass
    
    @abstractmethod
    async def export_conversations(
        self,
        session_id: Optional[str] = None,
        date_range: Optional[Dict[str, datetime]] = None,
        format: str = "json"
    ) -> str:
        """
        Export conversations for backup or analysis
        
        Args:
            session_id: Optional session filter
            date_range: Optional date range filter
            format: Export format ("json", "csv")
            
        Returns:
            Exported data as string
            
        Raises:
            ConversationError: When export fails
        """
        pass
    
    @abstractmethod
    async def cleanup_old_conversations(
        self,
        days_threshold: int = 90,
        keep_with_feedback: bool = True
    ) -> int:
        """
        Clean up old conversations to manage storage
        
        Args:
            days_threshold: Age threshold for cleanup
            keep_with_feedback: Whether to preserve conversations with feedback
            
        Returns:
            Number of conversations cleaned up
            
        Raises:
            ConversationError: When cleanup fails
        """
        pass