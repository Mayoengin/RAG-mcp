# src/network_rag/models/ports/llm_port.py
"""Language model port interface for LLM operations"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator


class LLMPort(ABC):
    """Interface for language model operations"""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate response from conversation messages
        
        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Randomness in generation (0.0 to 1.0)
            system_prompt: Optional system prompt override
            
        Returns:
            Generated response text
            
        Raises:
            LLMError: When generation fails
        """
        pass
    
    @abstractmethod
    async def stream_response(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream response generation for real-time display
        
        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Randomness in generation (0.0 to 1.0)
            system_prompt: Optional system prompt override
            
        Yields:
            Chunks of generated text
            
        Raises:
            LLMError: When streaming fails
        """
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding vector
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding as list of floats
            
        Raises:
            EmbeddingError: When embedding generation fails
        """
        pass
    
    @abstractmethod
    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of vector embeddings
            
        Raises:
            EmbeddingError: When batch embedding fails
        """
        pass
    
    @abstractmethod
    async def summarize_text(
        self, 
        text: str, 
        max_length: int = 200,
        style: str = "concise"
    ) -> str:
        """
        Generate text summary
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length in characters
            style: Summary style ("concise", "detailed", "bullet_points")
            
        Returns:
            Generated summary
            
        Raises:
            LLMError: When summarization fails
        """
        pass
    
    @abstractmethod
    async def extract_keywords(
        self, 
        text: str, 
        max_keywords: int = 10,
        include_phrases: bool = True
    ) -> List[str]:
        """
        Extract keywords and key phrases from text
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to extract
            include_phrases: Whether to include multi-word phrases
            
        Returns:
            List of extracted keywords/phrases
            
        Raises:
            LLMError: When keyword extraction fails
        """
        pass
    
    @abstractmethod
    async def classify_text(
        self,
        text: str,
        categories: List[str],
        confidence_threshold: float = 0.5
    ) -> Dict[str, float]:
        """
        Classify text into predefined categories
        
        Args:
            text: Text to classify
            categories: List of possible categories
            confidence_threshold: Minimum confidence for classification
            
        Returns:
            Dictionary mapping category to confidence score
            
        Raises:
            LLMError: When classification fails
        """
        pass
    
    @abstractmethod
    async def detect_intent(self, query: str) -> Dict[str, Any]:
        """
        Detect intent from user query
        
        Args:
            query: User query text
            
        Returns:
            Dictionary with detected intent and confidence
            
        Raises:
            LLMError: When intent detection fails
        """
        pass
    
    @abstractmethod
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of entities with type and confidence
            
        Raises:
            LLMError: When entity extraction fails
        """
        pass
    
    @abstractmethod
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., "en", "fr")
            source_language: Optional source language code
            
        Returns:
            Translated text
            
        Raises:
            LLMError: When translation fails
        """
        pass
    
    @abstractmethod
    async def check_content_safety(self, text: str) -> Dict[str, Any]:
        """
        Check content for safety issues
        
        Args:
            text: Text to check
            
        Returns:
            Safety assessment with flags and scores
            
        Raises:
            LLMError: When safety check fails
        """
        pass
    
    @abstractmethod
    async def generate_questions(
        self,
        text: str,
        num_questions: int = 5,
        question_type: str = "comprehension"
    ) -> List[str]:
        """
        Generate questions based on text content
        
        Args:
            text: Source text
            num_questions: Number of questions to generate
            question_type: Type of questions ("comprehension", "analytical", "factual")
            
        Returns:
            List of generated questions
            
        Raises:
            LLMError: When question generation fails
        """
        pass
    
    @abstractmethod
    async def improve_text(
        self,
        text: str,
        improvement_type: str = "clarity",
        target_audience: str = "general"
    ) -> str:
        """
        Improve text quality and clarity
        
        Args:
            text: Text to improve
            improvement_type: Type of improvement ("clarity", "grammar", "style")
            target_audience: Target audience ("general", "technical", "beginner")
            
        Returns:
            Improved text
            
        Raises:
            LLMError: When text improvement fails
        """
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the LLM model
        
        Returns:
            Model information (name, version, capabilities, etc.)
            
        Raises:
            LLMError: When model info retrieval fails
        """
        pass
    
    @abstractmethod
    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to analyze
            
        Returns:
            Estimated token count
            
        Raises:
            LLMError: When token estimation fails
        """
        pass