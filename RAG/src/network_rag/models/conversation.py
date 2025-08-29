# src/network_rag/models/conversation.py
"""Conversation tracking domain model for learning and context"""

from datetime import datetime , timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeedbackType(str, Enum):
    """Types of user feedback on assistant responses"""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    INCOMPLETE = "incomplete"
    CONFUSING = "confusing"


class Message(BaseModel):
    """Single conversation message"""
    
    # Core message data
    id: str = Field(..., description="Unique message identifier")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Processing information
    processing_time_ms: Optional[int] = Field(None, description="Time to generate response")
    token_count: Optional[int] = Field(None, description="Approximate token count")
    confidence_score: Optional[float] = Field(None, description="Response confidence")
    
    class Config:
        use_enum_values = True
    
    def get_word_count(self) -> int:
        """Get word count of message content"""
        return len(self.content.split())
    
    def is_recent(self, minutes: int = 30) -> bool:
        """Check if message is recent within given minutes"""
        age = datetime.utcnow() - self.timestamp
        return age.total_seconds() < (minutes * 60)


class Feedback(BaseModel):
    """User feedback on assistant response"""
    
    # Core feedback data
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    message_id: str = Field(..., description="ID of message being rated")
    rating: Optional[int] = Field(None, description="Numerical rating 1-5")
    comment: Optional[str] = Field(None, description="Optional feedback comment")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_session_id: Optional[str] = Field(None, description="User session for analytics")
    
    class Config:
        use_enum_values = True
    
    def is_positive(self) -> bool:
        """Check if feedback is positive"""
        return self.feedback_type == FeedbackType.HELPFUL
    
    def is_negative(self) -> bool:
        """Check if feedback indicates problems"""
        return self.feedback_type in [
            FeedbackType.NOT_HELPFUL,
            FeedbackType.INCORRECT,
            FeedbackType.INCOMPLETE,
            FeedbackType.CONFUSING
        ]


class ConversationSummary(BaseModel):
    """Summary of conversation for efficient storage and retrieval"""
    
    main_topics: List[str] = Field(default_factory=list)
    key_questions: List[str] = Field(default_factory=list)
    resolution_status: str = Field("ongoing", description="Status: resolved, ongoing, escalated")
    satisfaction_score: Optional[float] = Field(None, description="Overall satisfaction")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    """Complete conversation with learning data and analytics"""
    
    # Core conversation data
    id: str = Field(..., description="Unique conversation identifier")
    session_id: str = Field(..., description="Session identifier for grouping")
    messages: List[Message] = Field(default_factory=list)
    
    # Learning and feedback data
    feedback: List[Feedback] = Field(default_factory=list)
    summary: Optional[ConversationSummary] = Field(None, description="Conversation summary")
    
    # Classification and context
    topics: List[str] = Field(default_factory=list, description="Identified topics")
    intent: Optional[str] = Field(None, description="Detected user intent")
    complexity_level: str = Field("medium", description="Conversation complexity: low, medium, high")
    
    # User context
    user_context: Dict[str, Any] = Field(default_factory=dict)
    user_expertise_level: Optional[str] = Field(None, description="Estimated user expertise")
    
    # Timestamps and status
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field("active", description="Status: active, completed, archived")
    
    class Config:
        use_enum_values = True
        validate_assignment = True
    
    # Domain methods
    def add_message(
        self, 
        role: MessageRole, 
        content: str, 
        message_id: Optional[str] = None,
        **metadata
    ) -> str:
        """Add new message to conversation"""
        if not message_id:
            message_id = f"msg_{len(self.messages)}_{int(datetime.utcnow().timestamp())}"
        
        message = Message(
            id=message_id,
            role=role,
            content=content,
            metadata=metadata
        )
        
        self.messages.append(message)
        self.last_activity = datetime.utcnow()
        
        return message_id
    
    def add_feedback(
        self, 
        message_id: str, 
        feedback_type: FeedbackType, 
        rating: Optional[int] = None,
        comment: Optional[str] = None
    ) -> None:
        """Add user feedback for a message"""
        feedback = Feedback(
            feedback_type=feedback_type,
            message_id=message_id,
            rating=rating,
            comment=comment
        )
        
        self.feedback.append(feedback)
    
    def get_recent_messages(self, count: int = 5) -> List[Message]:
        """Get most recent messages for context"""
        return self.messages[-count:] if self.messages else []
    
    def get_user_messages(self) -> List[Message]:
        """Get all user messages"""
        return [msg for msg in self.messages if msg.role == MessageRole.USER]
    
    def get_assistant_messages(self) -> List[Message]:
        """Get all assistant messages"""
        return [msg for msg in self.messages if msg.role == MessageRole.ASSISTANT]
    
    def calculate_satisfaction_score(self) -> float:
        """Calculate overall satisfaction based on feedback"""
        if not self.feedback:
            return 0.5  # Neutral when no feedback
        
        positive_count = len([f for f in self.feedback if f.is_positive()])
        negative_count = len([f for f in self.feedback if f.is_negative()])
        total_feedback = len(self.feedback)
        
        if total_feedback == 0:
            return 0.5
        
        # Calculate score: 1.0 = all positive, 0.0 = all negative, 0.5 = neutral
        satisfaction = positive_count / total_feedback
        return satisfaction
    
    def get_duration_minutes(self) -> float:
        """Get conversation duration in minutes"""
        duration = self.last_activity - self.started_at
        return duration.total_seconds() / 60
    
    def get_message_count(self) -> int:
        """Get total message count"""
        return len(self.messages)
    
    def get_turn_count(self) -> int:
        """Get number of conversational turns (user-assistant pairs)"""
        user_messages = len(self.get_user_messages())
        assistant_messages = len(self.get_assistant_messages())
        return min(user_messages, assistant_messages)
    
    def is_active(self, hours: int = 24) -> bool:
        """Check if conversation had recent activity"""
        inactive_threshold = datetime.utcnow() - timedelta(hours=hours)
        return self.last_activity > inactive_threshold
    
    def extract_key_topics(self, max_topics: int = 5) -> List[str]:
        """Extract key topics from conversation content"""
        # Simple topic extraction based on message content
        # In production, this could use more sophisticated NLP
        
        all_content = " ".join([msg.content for msg in self.messages])
        words = all_content.lower().split()
        
        # Network-specific keywords to look for
        network_keywords = {
            "olt", "ftth", "network", "configuration", "connection", 
            "bandwidth", "troubleshooting", "router", "switch", "fiber"
        }
        
        # Count keyword frequency
        topic_counts = {}
        for word in words:
            if word in network_keywords:
                topic_counts[word] = topic_counts.get(word, 0) + 1
        
        # Return top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:max_topics]]
    
    def generate_summary(self) -> ConversationSummary:
        """Generate conversation summary for efficient storage"""
        topics = self.extract_key_topics()
        
        # Extract key questions from user messages
        user_messages = self.get_user_messages()
        key_questions = []
        for msg in user_messages[-3:]:  # Last 3 questions
            if "?" in msg.content:
                # Take first question if multiple
                question = msg.content.split("?")[0] + "?"
                if len(question) < 200:  # Reasonable length
                    key_questions.append(question)
        
        # Determine resolution status based on feedback and conversation flow
        satisfaction = self.calculate_satisfaction_score()
        if satisfaction > 0.7:
            resolution_status = "resolved"
        elif satisfaction < 0.3:
            resolution_status = "escalated"
        else:
            resolution_status = "ongoing"
        
        summary = ConversationSummary(
            main_topics=topics,
            key_questions=key_questions,
            resolution_status=resolution_status,
            satisfaction_score=satisfaction
        )
        
        self.summary = summary
        return summary
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive conversation analytics"""
        return {
            "conversation_id": self.id,
            "session_id": self.session_id,
            "duration_minutes": round(self.get_duration_minutes(), 1),
            "message_count": self.get_message_count(),
            "turn_count": self.get_turn_count(),
            "satisfaction_score": round(self.calculate_satisfaction_score(), 2),
            "feedback_count": len(self.feedback),
            "topics": self.extract_key_topics(),
            "complexity_level": self.complexity_level,
            "status": self.status,
            "is_active": self.is_active(),
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }