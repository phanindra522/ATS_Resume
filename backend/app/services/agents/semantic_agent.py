"""
Semantic Similarity Agent

This agent uses ChromaDB embeddings for resume vs job description
to calculate cosine similarity score.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent, AgentResult, AgentType
from app.database import get_chroma_collection
from app.routers.resumes import generate_embedding


class SemanticSimilarityAgent(BaseAgent):
    """Agent for semantic similarity using ChromaDB embeddings"""
    
    def __init__(self, weight: float = 0.25):
        super().__init__(AgentType.SEMANTIC_SIMILARITY, weight)
    
    async def analyze(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """Analyze semantic similarity between resume and job"""
        try:
            resume_text = self._extract_text_content(resume)
            job_text = self._extract_job_content(job)
            
            # Generate embeddings
            resume_embedding = self._generate_embedding(resume_text)
            job_embedding = self._generate_embedding(job_text)
            
            if resume_embedding is None or job_embedding is None:
                return self._create_result(
                    score=0.0,
                    evidence={
                        "resume_embedding_generated": resume_embedding is not None,
                        "job_embedding_generated": job_embedding is not None,
                        "similarity_score": 0.0
                    },
                    confidence=0.0,
                    error="Failed to generate embeddings"
                )
            
            # Calculate cosine similarity
            similarity_score = self._calculate_cosine_similarity(resume_embedding, job_embedding)
            
            # Normalize to 0-1 range (cosine similarity is -1 to 1)
            normalized_score = max(0.0, (similarity_score + 1) / 2)
            
            # Calculate confidence based on embedding quality
            confidence = self._calculate_embedding_confidence(resume_embedding, job_embedding)
            
            return self._create_result(
                score=normalized_score,
                evidence={
                    "resume_embedding_generated": True,
                    "job_embedding_generated": True,
                    "similarity_score": similarity_score,
                    "normalized_score": normalized_score,
                    "embedding_dimensions": len(resume_embedding),
                    "resume_text_length": len(resume_text),
                    "job_text_length": len(job_text)
                },
                confidence=confidence
            )
            
        except Exception as e:
            return self._create_result(
                score=0.0,
                evidence={},
                confidence=0.0,
                error=f"Error in semantic analysis: {str(e)}"
            )
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            if not text or len(text.strip()) < 10:
                return None
            
            # Use the existing embedding generation function
            embedding = generate_embedding(text)
            
            if embedding is not None:
                return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            
            return None
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def _calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Ensure same dimensions
            if len(vec1) != len(vec2):
                min_len = min(len(vec1), len(vec2))
                vec1 = vec1[:min_len]
                vec2 = vec2[:min_len]
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Clamp to [-1, 1] range
            return max(-1.0, min(1.0, similarity))
            
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _calculate_embedding_confidence(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate confidence based on embedding quality"""
        try:
            # Check embedding dimensions
            if len(embedding1) != len(embedding2):
                return 0.5  # Lower confidence for dimension mismatch
            
            # Check for zero vectors
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
                return 0.1  # Very low confidence for zero vectors
            
            # Check for reasonable embedding values
            if np.all(vec1 == 0) or np.all(vec2 == 0):
                return 0.2  # Low confidence for all-zero embeddings
            
            # Check for NaN or infinite values
            if np.any(np.isnan(vec1)) or np.any(np.isnan(vec2)) or np.any(np.isinf(vec1)) or np.any(np.isinf(vec2)):
                return 0.3  # Low confidence for invalid values
            
            # Higher confidence for embeddings with good variance
            variance1 = np.var(vec1)
            variance2 = np.var(vec2)
            
            if variance1 > 0.01 and variance2 > 0.01:
                return 1.0  # High confidence
            elif variance1 > 0.001 and variance2 > 0.001:
                return 0.8  # Good confidence
            else:
                return 0.6  # Medium confidence
            
        except Exception as e:
            print(f"Error calculating embedding confidence: {e}")
            return 0.5  # Default medium confidence
    
    async def store_resume_embedding(self, resume_id: str, resume_text: str, user_id: str) -> bool:
        """Store resume embedding in ChromaDB for future use"""
        try:
            embedding = self._generate_embedding(resume_text)
            if embedding is None:
                return False
            
            chroma_collection = get_chroma_collection()
            if chroma_collection is None:
                return False
            
            # Store in ChromaDB
            chroma_collection.add(
                embeddings=[embedding],
                documents=[resume_text],
                metadatas=[{"resume_id": resume_id, "user_id": user_id}],
                ids=[resume_id]
            )
            
            return True
            
        except Exception as e:
            print(f"Error storing resume embedding: {e}")
            return False
    
    async def remove_resume_embedding(self, resume_id: str) -> bool:
        """Remove resume embedding from ChromaDB"""
        try:
            chroma_collection = get_chroma_collection()
            if chroma_collection is None:
                return False
            
            # Remove from ChromaDB
            chroma_collection.delete(ids=[resume_id])
            
            return True
            
        except Exception as e:
            print(f"Error removing resume embedding: {e}")
            return False
