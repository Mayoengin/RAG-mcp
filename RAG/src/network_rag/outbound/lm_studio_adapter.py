# src/network_rag/outbound/lm_studio_adapter.py
"""LM Studio adapter for local LLM operations"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from ..models import Message, LLMPort, LLMError


class LMStudioAdapter(LLMPort):
    """Adapter for LM Studio local LLM server"""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:1234", 
        model_name: str = "local-model",
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def generate_response(
        self,
        messages: List[Message],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response from conversation messages"""
        
        session = await self._get_session()
        
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages_to_openai(messages, system_prompt)
            
            payload = {
                "model": self.model_name,
                "messages": openai_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMError(
                        llm_provider="lm_studio",
                        operation="generate_response",
                        message=f"HTTP {response.status}: {error_text}"
                    )
                
                data = await response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    raise LLMError(
                        llm_provider="lm_studio",
                        operation="generate_response", 
                        message="No response content from LM Studio"
                    )
        
        except aiohttp.ClientError as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="generate_response",
                message=f"Connection error: {str(e)}"
            )
        except json.JSONDecodeError as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="generate_response",
                message=f"Invalid JSON response: {str(e)}"
            )
        except Exception as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="generate_response",
                message=str(e)
            )
    
    async def stream_response(
        self,
        messages: List[Message],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream response generation for real-time display"""
        
        session = await self._get_session()
        
        try:
            openai_messages = self._convert_messages_to_openai(messages, system_prompt)
            
            payload = {
                "model": self.model_name,
                "messages": openai_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }
            
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    yield f"Error: HTTP {response.status}: {error_text}"
                    return
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            yield f"Error streaming from LM Studio: {str(e)}"
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding (fallback to sentence transformers)"""
        try:
            # Try LM Studio embeddings endpoint first
            session = await self._get_session()
            
            payload = {
                "model": self.model_name,
                "input": text
            }
            
            async with session.post(
                f"{self.base_url}/v1/embeddings",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and len(data["data"]) > 0:
                        return data["data"][0]["embedding"]
        
        except Exception:
            pass  # Fall back to sentence transformers
        
        # Fallback to sentence transformers
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use a lightweight model for embeddings
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text).tolist()
            return embedding
        
        except ImportError:
            # If sentence transformers not available, return zero vector
            return [0.0] * 384  # Default embedding size
        except Exception as e:
            raise LLMError(
                llm_provider="sentence_transformers",
                operation="generate_embedding",
                message=f"Embedding generation failed: {str(e)}"
            )
    
    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        try:
            # Try batch endpoint first
            session = await self._get_session()
            
            payload = {
                "model": self.model_name,
                "input": texts
            }
            
            async with session.post(
                f"{self.base_url}/v1/embeddings",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if "data" in data:
                        return [item["embedding"] for item in data["data"]]
        
        except Exception:
            pass  # Fall back to individual generation
        
        # Fallback: generate individually
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    async def summarize_text(
        self, 
        text: str, 
        max_length: int = 200,
        style: str = "concise"
    ) -> str:
        """Generate text summary"""
        
        style_prompts = {
            "concise": "Provide a concise summary",
            "detailed": "Provide a detailed summary", 
            "bullet_points": "Provide a summary in bullet points"
        }
        
        prompt = f"""{style_prompts.get(style, "Provide a concise summary")} of the following text in approximately {max_length} characters:

{text}

Summary:"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            return await self.generate_response(
                messages, 
                max_tokens=max_length // 3,  # Rough token estimation
                temperature=0.3  # Lower temperature for factual summaries
            )
        except Exception as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="summarize_text",
                message=f"Text summarization failed: {str(e)}"
            )
    
    async def extract_keywords(
        self, 
        text: str, 
        max_keywords: int = 10,
        include_phrases: bool = True
    ) -> List[str]:
        """Extract keywords and key phrases from text"""
        
        phrase_instruction = "including key phrases" if include_phrases else "single words only"
        
        prompt = f"""Extract the {max_keywords} most important keywords from the following text ({phrase_instruction}). Return only the keywords separated by commas, no other text:

{text}

Keywords:"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            response = await self.generate_response(
                messages, 
                max_tokens=100,
                temperature=0.1  # Very low temperature for consistent extraction
            )
            
            # Parse keywords from response
            keywords = [kw.strip() for kw in response.split(',')]
            # Clean and filter keywords
            cleaned_keywords = []
            for kw in keywords:
                kw = kw.strip().strip('"').strip("'")
                if kw and len(kw) > 2:  # Filter out very short keywords
                    cleaned_keywords.append(kw)
            
            return cleaned_keywords[:max_keywords]
            
        except Exception:
            # Fallback: simple word frequency analysis
            words = text.lower().split()
            from collections import Counter
            
            # Filter common words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            
            word_counts = Counter(filtered_words)
            return [word for word, count in word_counts.most_common(max_keywords)]
    
    async def classify_text(
        self,
        text: str,
        categories: List[str],
        confidence_threshold: float = 0.5
    ) -> Dict[str, float]:
        """Classify text into predefined categories"""
        
        categories_str = ", ".join(categories)
        
        prompt = f"""Classify the following text into one or more of these categories: {categories_str}

Text: {text}

For each category that applies, provide a confidence score between 0.0 and 1.0. Format as: Category: confidence_score

Classification:"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            response = await self.generate_response(
                messages,
                max_tokens=200,
                temperature=0.2
            )
            
            # Parse classification results
            classifications = {}
            for line in response.split('\n'):
                if ':' in line:
                    try:
                        category, score_str = line.split(':', 1)
                        category = category.strip()
                        score = float(score_str.strip())
                        
                        if category in categories and score >= confidence_threshold:
                            classifications[category] = score
                    except (ValueError, IndexError):
                        continue
            
            return classifications
            
        except Exception as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="classify_text",
                message=f"Text classification failed: {str(e)}"
            )
    
    async def detect_intent(self, query: str) -> Dict[str, Any]:
        """Detect intent from user query"""
        
        prompt = f"""Analyze the following user query and detect the primary intent. Choose from these intents:
- information_request: User wants information or explanations
- troubleshooting: User has a problem to solve  
- configuration: User wants to configure something
- comparison: User wants to compare options
- recommendation: User wants recommendations
- status_check: User wants to check status of something

Query: {query}

Respond with: Intent: [intent_name], Confidence: [0.0-1.0], Keywords: [relevant keywords]

Analysis:"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            response = await self.generate_response(
                messages,
                max_tokens=150,
                temperature=0.3
            )
            
            # Parse intent response
            intent_result = {
                "intent": "information_request",  # Default
                "confidence": 0.5,
                "keywords": []
            }
            
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('Intent:'):
                    intent_result["intent"] = line.split(':', 1)[1].strip()
                elif line.startswith('Confidence:'):
                    try:
                        intent_result["confidence"] = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith('Keywords:'):
                    keywords_str = line.split(':', 1)[1].strip()
                    intent_result["keywords"] = [kw.strip() for kw in keywords_str.split(',')]
            
            return intent_result
            
        except Exception as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="detect_intent",
                message=f"Intent detection failed: {str(e)}"
            )
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        
        prompt = f"""Extract named entities from the following text. For each entity, provide the entity text, type, and confidence score.

Entity types: PERSON, ORGANIZATION, LOCATION, TECHNOLOGY, PRODUCT, DATE, NUMBER

Text: {text}

Format each entity as: Entity: [text] | Type: [type] | Confidence: [0.0-1.0]

Entities:"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            response = await self.generate_response(
                messages,
                max_tokens=300,
                temperature=0.2
            )
            
            entities = []
            for line in response.split('\n'):
                if 'Entity:' in line and 'Type:' in line:
                    try:
                        parts = line.split('|')
                        entity_text = parts[0].split(':', 1)[1].strip()
                        entity_type = parts[1].split(':', 1)[1].strip()
                        confidence = 0.8  # Default confidence
                        
                        if len(parts) > 2 and 'Confidence:' in parts[2]:
                            try:
                                confidence = float(parts[2].split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        
                        entities.append({
                            "text": entity_text,
                            "type": entity_type,
                            "confidence": confidence
                        })
                    except (IndexError, ValueError):
                        continue
            
            return entities
            
        except Exception as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="extract_entities",
                message=f"Entity extraction failed: {str(e)}"
            )
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """Translate text to target language"""
        
        source_part = f" from {source_language}" if source_language else ""
        
        prompt = f"""Translate the following text{source_part} to {target_language}. Provide only the translation, no other text:

{text}

Translation:"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            return await self.generate_response(
                messages,
                max_tokens=len(text) * 2,  # Allow for text expansion
                temperature=0.1  # Low temperature for accurate translation
            )
        except Exception as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="translate_text",
                message=f"Translation failed: {str(e)}"
            )
    
    async def check_content_safety(self, text: str) -> Dict[str, Any]:
        """Check content for safety issues"""
        
        prompt = f"""Analyze the following text for safety issues. Check for:
- Harmful content
- Inappropriate language
- Misinformation potential
- Privacy concerns

Text: {text}

Respond with: Safe: [yes/no], Issues: [list any issues], Score: [0.0-1.0 where 1.0 is completely safe]

Analysis:"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            response = await self.generate_response(
                messages,
                max_tokens=200,
                temperature=0.2
            )
            
            safety_result = {
                "is_safe": True,
                "safety_score": 1.0,
                "issues": [],
                "recommendations": []
            }
            
            # Parse safety response
            if "Safe: no" in response.lower():
                safety_result["is_safe"] = False
            
            # Extract safety score if present
            for line in response.split('\n'):
                if line.startswith('Score:'):
                    try:
                        score_str = line.split(':', 1)[1].strip()
                        safety_result["safety_score"] = float(score_str)
                    except ValueError:
                        pass
                elif line.startswith('Issues:'):
                    issues_str = line.split(':', 1)[1].strip()
                    if issues_str and issues_str.lower() != 'none':
                        safety_result["issues"] = [issue.strip() for issue in issues_str.split(',')]
            
            return safety_result
            
        except Exception as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="check_content_safety",
                message=f"Content safety check failed: {str(e)}"
            )
    
    async def generate_questions(
        self,
        text: str,
        num_questions: int = 5,
        question_type: str = "comprehension"
    ) -> List[str]:
        """Generate questions based on text content"""
        
        type_instructions = {
            "comprehension": "comprehension questions about the main concepts",
            "analytical": "analytical questions that require deeper thinking",
            "factual": "factual questions about specific details"
        }
        
        instruction = type_instructions.get(question_type, "questions")
        
        prompt = f"""Generate {num_questions} {instruction} based on the following text. Number each question:

{text}

Questions:"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            response = await self.generate_response(
                messages,
                max_tokens=300,
                temperature=0.5
            )
            
            # Extract numbered questions
            questions = []
            for line in response.split('\n'):
                line = line.strip()
                # Look for numbered questions (1., 2., etc.)
                if line and (line[0].isdigit() or line.startswith('Q')):
                    # Remove numbering
                    question = line
                    if '. ' in question:
                        question = question.split('. ', 1)[1]
                    elif ': ' in question:
                        question = question.split(': ', 1)[1]
                    
                    if question and question.endswith('?'):
                        questions.append(question)
            
            return questions[:num_questions]
            
        except Exception as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="generate_questions",
                message=f"Question generation failed: {str(e)}"
            )
    
    async def improve_text(
        self,
        text: str,
        improvement_type: str = "clarity",
        target_audience: str = "general"
    ) -> str:
        """Improve text quality and clarity"""
        
        improvement_instructions = {
            "clarity": "improve clarity and readability",
            "grammar": "fix grammar and language issues",
            "style": "improve writing style and flow"
        }
        
        instruction = improvement_instructions.get(improvement_type, "improve")
        
        prompt = f"""Please {instruction} in the following text for a {target_audience} audience. Maintain the original meaning and key information:

{text}

Improved text:"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            return await self.generate_response(
                messages,
                max_tokens=len(text) * 2,  # Allow for expansion
                temperature=0.3
            )
        except Exception as e:
            raise LLMError(
                llm_provider="lm_studio",
                operation="improve_text",
                message=f"Text improvement failed: {str(e)}"
            )
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the LLM model"""
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and len(data["data"]) > 0:
                        model_info = data["data"][0]
                        return {
                            "model_name": model_info.get("id", self.model_name),
                            "provider": "lm_studio",
                            "base_url": self.base_url,
                            "capabilities": [
                                "text_generation",
                                "conversation",
                                "streaming",
                                "embedding_fallback"
                            ],
                            "max_tokens": 4096,  # Typical limit
                            "temperature_range": [0.0, 2.0]
                        }
        except Exception:
            pass
        
        # Fallback model info
        return {
            "model_name": self.model_name,
            "provider": "lm_studio",
            "base_url": self.base_url,
            "status": "unknown",
            "capabilities": ["text_generation", "conversation"]
        }
    
    async def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation: ~4 characters per token for English text
        return len(text) // 4
    
    def _convert_messages_to_openai(self, messages: List[Message], system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Convert internal Message objects to OpenAI format"""
        openai_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            openai_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Convert messages
        for msg in messages:
            # msg.role is already a string due to use_enum_values = True in Message model
            role_str = msg.role if isinstance(msg.role, str) else msg.role.value
            openai_messages.append({
                "role": role_str,
                "content": msg.content
            })
        
        return openai_messages
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()