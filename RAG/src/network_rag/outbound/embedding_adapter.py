# src/network_rag/outbound/embedding_adapter.py
"""Sentence Transformers adapter for embedding generation"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import pickle
import hashlib

from ..models import EmbeddingError


class SentenceTransformersAdapter:
    """Adapter for sentence transformers embedding generation"""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: Optional[str] = None,
        max_workers: int = 4,
        enable_caching: bool = True
    ):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else Path(".embedding_cache")
        self.max_workers = max_workers
        self.enable_caching = enable_caching
        
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Initialize cache directory
        if self.enable_caching:
            self.cache_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize the sentence transformer model"""
        try:
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor, 
                self._load_model
            )
            
        except Exception as e:
            raise EmbeddingError(
                model_name=self.model_name,
                message=f"Failed to initialize model: {str(e)}"
            )
    
    def _load_model(self):
        """Load sentence transformer model (runs in thread pool)"""
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer(self.model_name)
        except ImportError:
            raise EmbeddingError(
                model_name=self.model_name,
                message="sentence-transformers package not installed. Install with: pip install sentence-transformers"
            )
        except Exception as e:
            raise EmbeddingError(
                model_name=self.model_name,
                message=f"Failed to load model: {str(e)}"
            )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self.model:
            await self.initialize()
        
        if not text or not text.strip():
            raise EmbeddingError(
                model_name=self.model_name,
                text_length=len(text) if text else 0,
                message="Cannot generate embedding for empty text"
            )
        
        try:
            # Check cache first
            if self.enable_caching:
                cached_embedding = await self._get_cached_embedding(text)
                if cached_embedding is not None:
                    return cached_embedding
            
            # Generate embedding in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                self._generate_single_embedding,
                text
            )
            
            # Cache the result
            if self.enable_caching:
                await self._cache_embedding(text, embedding)
            
            return embedding.tolist()
            
        except Exception as e:
            raise EmbeddingError(
                model_name=self.model_name,
                text_length=len(text),
                message=f"Embedding generation failed: {str(e)}"
            )
    
    async def batch_generate_embeddings(
        self, 
        texts: List[str], 
        batch_size: int = 32
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        if not self.model:
            await self.initialize()
        
        if not texts:
            return []
        
        try:
            # Filter out empty texts and keep track of indices
            valid_texts = []
            text_indices = []
            
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text.strip())
                    text_indices.append(i)
            
            if not valid_texts:
                raise EmbeddingError(
                    model_name=self.model_name,
                    message="No valid texts provided for batch embedding"
                )
            
            # Check cache for existing embeddings
            cached_results = {}
            uncached_texts = []
            uncached_indices = []
            
            if self.enable_caching:
                for i, text in enumerate(valid_texts):
                    cached_embedding = await self._get_cached_embedding(text)
                    if cached_embedding is not None:
                        cached_results[i] = cached_embedding
                    else:
                        uncached_texts.append(text)
                        uncached_indices.append(i)
            else:
                uncached_texts = valid_texts
                uncached_indices = list(range(len(valid_texts)))
            
            # Generate embeddings for uncached texts in batches
            new_embeddings = []
            if uncached_texts:
                for i in range(0, len(uncached_texts), batch_size):
                    batch_texts = uncached_texts[i:i + batch_size]
                    
                    loop = asyncio.get_event_loop()
                    batch_embeddings = await loop.run_in_executor(
                        self.executor,
                        self._generate_batch_embeddings,
                        batch_texts
                    )
                    
                    new_embeddings.extend(batch_embeddings)
                
                # Cache new embeddings
                if self.enable_caching:
                    cache_tasks = []
                    for text, embedding in zip(uncached_texts, new_embeddings):
                        cache_tasks.append(self._cache_embedding(text, embedding))
                    await asyncio.gather(*cache_tasks, return_exceptions=True)
            
            # Combine cached and new results
            all_embeddings = [None] * len(valid_texts)
            
            # Add cached results
            for i, embedding in cached_results.items():
                all_embeddings[i] = embedding
            
            # Add new results
            for i, embedding in zip(uncached_indices, new_embeddings):
                all_embeddings[i] = embedding.tolist()
            
            # Expand to match original input length (empty texts get zero vectors)
            final_embeddings = []
            embedding_dim = len(all_embeddings[0]) if all_embeddings and all_embeddings[0] else 384
            
            valid_idx = 0
            for i, original_text in enumerate(texts):
                if i in [text_indices[j] for j in range(len(text_indices))]:
                    # Valid text - use generated embedding
                    if valid_idx < len(all_embeddings):
                        final_embeddings.append(all_embeddings[valid_idx])
                    else:
                        final_embeddings.append([0.0] * embedding_dim)
                    valid_idx += 1
                else:
                    # Empty text - use zero vector
                    final_embeddings.append([0.0] * embedding_dim)
            
            return final_embeddings
            
        except Exception as e:
            raise EmbeddingError(
                model_name=self.model_name,
                message=f"Batch embedding generation failed: {str(e)}"
            )
    
    def _generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate single embedding (runs in thread pool)"""
        return self.model.encode(text, convert_to_numpy=True)
    
    def _generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate batch embeddings (runs in thread pool)"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [embeddings[i] for i in range(len(embeddings))]
    
    async def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding if available"""
        if not self.enable_caching:
            return None
        
        try:
            cache_key = self._get_cache_key(text)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            if cache_file.exists():
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self.executor,
                    self._load_cached_embedding,
                    cache_file
                )
        except Exception:
            # Cache errors are non-fatal
            pass
        
        return None
    
    async def _cache_embedding(self, text: str, embedding: np.ndarray):
        """Cache embedding for future use"""
        if not self.enable_caching:
            return
        
        try:
            cache_key = self._get_cache_key(text)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._save_cached_embedding,
                cache_file,
                embedding.tolist()
            )
        except Exception:
            # Cache errors are non-fatal
            pass
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        # Create hash of model name + text for unique cache key
        content = f"{self.model_name}:{text}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def _load_cached_embedding(self, cache_file: Path) -> List[float]:
        """Load cached embedding from file (runs in thread pool)"""
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    def _save_cached_embedding(self, cache_file: Path, embedding: List[float]):
        """Save embedding to cache file (runs in thread pool)"""
        with open(cache_file, 'wb') as f:
            pickle.dump(embedding, f)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        if not self.model:
            await self.initialize()
        
        try:
            # Get model dimension by encoding a sample text
            sample_embedding = await self.generate_embedding("sample text")
            
            return {
                "model_name": self.model_name,
                "provider": "sentence_transformers",
                "embedding_dimension": len(sample_embedding),
                "max_sequence_length": getattr(self.model, 'max_seq_length', 512),
                "model_type": "sentence_transformer",
                "caching_enabled": self.enable_caching,
                "cache_dir": str(self.cache_dir),
                "capabilities": [
                    "text_embedding",
                    "batch_embedding",
                    "semantic_similarity"
                ]
            }
            
        except Exception as e:
            return {
                "model_name": self.model_name,
                "provider": "sentence_transformers",
                "status": "error",
                "error": str(e)
            }
    
    async def calculate_similarity(
        self, 
        text1: str, 
        text2: str
    ) -> float:
        """Calculate cosine similarity between two texts"""
        try:
            embeddings = await self.batch_generate_embeddings([text1, text2])
            
            if len(embeddings) != 2:
                raise EmbeddingError(
                    model_name=self.model_name,
                    message="Failed to generate embeddings for similarity calculation"
                )
            
            # Calculate cosine similarity
            vec1 = np.array(embeddings[0])
            vec2 = np.array(embeddings[1])
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            raise EmbeddingError(
                model_name=self.model_name,
                message=f"Similarity calculation failed: {str(e)}"
            )
    
    async def find_most_similar(
        self,
        query_text: str,
        candidate_texts: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find most similar texts to query"""
        if not candidate_texts:
            return []
        
        try:
            all_texts = [query_text] + candidate_texts
            embeddings = await self.batch_generate_embeddings(all_texts)
            
            query_embedding = np.array(embeddings[0])
            candidate_embeddings = [np.array(emb) for emb in embeddings[1:]]
            
            # Calculate similarities
            similarities = []
            for i, candidate_emb in enumerate(candidate_embeddings):
                similarity = self._cosine_similarity(query_embedding, candidate_emb)
                similarities.append((candidate_texts[i], similarity))
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            raise EmbeddingError(
                model_name=self.model_name,
                message=f"Similar text search failed: {str(e)}"
            )
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    async def clear_cache(self):
        """Clear embedding cache"""
        if not self.enable_caching or not self.cache_dir.exists():
            return
        
        try:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._clear_cache_files,
                cache_files
            )
            
        except Exception:
            # Cache errors are non-fatal
            pass
    
    def _clear_cache_files(self, cache_files: List[Path]):
        """Clear cache files (runs in thread pool)"""
        for cache_file in cache_files:
            try:
                cache_file.unlink()
            except Exception:
                pass
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enable_caching or not self.cache_dir.exists():
            return {"caching_enabled": False}
        
        try:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            
            total_size = 0
            for cache_file in cache_files:
                try:
                    total_size += cache_file.stat().st_size
                except Exception:
                    pass
            
            return {
                "caching_enabled": True,
                "cache_dir": str(self.cache_dir),
                "cached_embeddings": len(cache_files),
                "total_cache_size_bytes": total_size,
                "total_cache_size_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception:
            return {"caching_enabled": True, "error": "Failed to get cache stats"}
    
    async def close(self):
        """Close the adapter and cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        
        self.model = None