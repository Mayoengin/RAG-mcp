# src/network_rag/outbound/llama_adapter.py
"""Llama model adapter for LLM interactions"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from datetime import datetime

from ..models import LLMError


class LlamaAdapter:
    """Adapter for Llama model interactions via Ollama API"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b@q8_0",
        timeout: int = 120,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using Llama model"""
        
        # Convert messages to Ollama format (expecting dict format)
        ollama_messages = []
        for msg in messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                ollama_messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 2048
            }
        }
        
        session = await self._get_session()
        
        for attempt in range(self.max_retries):
            try:
                async with session.post(f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('message', {}).get('content', 'No response generated')
                    else:
                        error_text = await response.text()
                        if attempt == self.max_retries - 1:
                            raise LLMError(
                                model_name=self.model_name,
                                message=f"HTTP {response.status}: {error_text}"
                            )
                        
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    raise LLMError(
                        model_name=self.model_name,
                        message=f"Network error: {str(e)}"
                    )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                raise LLMError(
                    model_name=self.model_name,
                    message=f"Unexpected error: {str(e)}"
                )
        
        raise LLMError(
            model_name=self.model_name,
            message=f"Failed after {self.max_retries} attempts"
        )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings for text (fallback implementation)"""
        
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        
        session = await self._get_session()
        
        try:
            async with session.post(f"{self.base_url}/api/embeddings", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('embedding', [])
                else:
                    # Fallback to simple hash-based embedding for compatibility
                    import hashlib
                    hash_obj = hashlib.md5(text.encode())
                    hash_int = int(hash_obj.hexdigest(), 16)
                    
                    # Generate 384-dimensional embedding
                    embedding = []
                    for i in range(384):
                        embedding.append(((hash_int >> (i % 32)) & 1) * 0.1 - 0.05)
                    
                    return embedding
                    
        except Exception as e:
            # Fallback embedding generation
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            
            embedding = []
            for i in range(384):
                embedding.append(((hash_int >> (i % 32)) & 1) * 0.1 - 0.05)
            
            return embedding
    
    async def extract_keywords(self, text: str, max_keywords: int = 8) -> List[str]:
        """Extract keywords from text using the LLM"""
        
        messages = [
            {
                "role": "system",
                "content": "Extract the most important keywords from the following text. Return only the keywords, separated by commas, no explanations."
            },
            {
                "role": "user", 
                "content": f"Extract {max_keywords} keywords from: {text}"
            }
        ]
        
        try:
            response = await self.generate_response(messages)
            keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
            return keywords[:max_keywords]
            
        except Exception:
            # Fallback to simple keyword extraction
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            words = text.lower().replace('.', '').replace(',', '').split()
            keywords = [word for word in words if len(word) > 3 and word not in common_words]
            
            # Get most frequent words
            word_count = {}
            for word in keywords:
                word_count[word] = word_count.get(word, 0) + 1
            
            sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
            return [word for word, count in sorted_words[:max_keywords]]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the Llama model is available"""
        
        session = await self._get_session()
        
        try:
            # Check if Ollama is running and model is available
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model.get('name', '') for model in data.get('models', [])]
                    
                    model_available = any(self.model_name in model for model in models)
                    
                    return {
                        "status": "healthy" if model_available else "model_not_found",
                        "ollama_running": True,
                        "model_name": self.model_name,
                        "model_available": model_available,
                        "available_models": models[:5],  # Show first 5
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "ollama_running": False,
                        "error": f"HTTP {response.status}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            return {
                "status": "unreachable",
                "ollama_running": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None