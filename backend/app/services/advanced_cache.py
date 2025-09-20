"""
Advanced Caching Implementation for Additional System Components
Extends caching beyond LLM to cover embeddings, database queries, file processing, and more
"""
import hashlib
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np

from app.services.cache_service import get_cache_service, cached
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Cache for expensive embedding operations"""
    
    def __init__(self):
        self.cache_service = get_cache_service()
        self.stats = {
            "embedding_requests": 0,
            "embedding_cache_hits": 0,
            "tokens_saved_embeddings": 0
        }
    
    async def get_text_embedding(self, text: str, model: str = None) -> np.ndarray:
        """Get text embedding with caching"""
        self.stats["embedding_requests"] += 1
        
        # Normalize text for consistent caching
        normalized_text = text.lower().strip()[:2000]  # Limit text length
        model_name = model or settings.LLM_EMBEDDING_MODEL
        
        # Generate cache key
        cache_key = hashlib.sha256(f"{model_name}:{normalized_text}".encode()).hexdigest()[:16]
        
        # Try cache first
        cached_embedding = await self.cache_service.get(
            namespace="text_embeddings",
            identifier=cache_key,
            model=model_name,
            text_length=len(normalized_text)
        )
        
        if cached_embedding is not None:
            self.stats["embedding_cache_hits"] += 1
            self.stats["tokens_saved_embeddings"] += len(normalized_text) // 4
            logger.debug(f"✅ Embedding cache HIT: {cache_key}")
            return np.array(cached_embedding)
        
        # Cache miss - generate embedding
        logger.debug(f"❌ Embedding cache MISS: {cache_key}")
        
        # TODO: Replace with actual OpenAI embedding API call
        embedding = self._generate_placeholder_embedding(normalized_text)
        
        # Cache the result
        await self.cache_service.set(
            namespace="text_embeddings",
            identifier=cache_key,
            value=embedding.tolist(),
            ttl=settings.CACHE_EMBEDDINGS_TTL_SECONDS,
            model=model_name,
            text_length=len(normalized_text)
        )
        
        return embedding
    
    def _generate_placeholder_embedding(self, text: str) -> np.ndarray:
        """Placeholder embedding generation - replace with OpenAI API"""
        return np.random.rand(settings.EMBEDDING_DIMENSION)
    
    async def get_bulk_embeddings(self, texts: List[str], model: str = None) -> List[np.ndarray]:
        """Get multiple embeddings efficiently with caching"""
        tasks = [self.get_text_embedding(text, model) for text in texts]
        return await asyncio.gather(*tasks)

class DatabaseQueryCache:
    """Cache for expensive database queries"""
    
    def __init__(self):
        self.cache_service = get_cache_service()
        self.stats = {
            "db_requests": 0,
            "db_cache_hits": 0
        }
    
    async def get_user_resumes(self, user_id: str, db) -> List[Dict]:
        """Get user resumes with caching"""
        self.stats["db_requests"] += 1
        
        # Try cache first
        cached_resumes = await self.cache_service.get(
            namespace="user_resumes",
            identifier=user_id,
            cache_version="v1"
        )
        
        if cached_resumes is not None:
            self.stats["db_cache_hits"] += 1
            logger.debug(f"✅ User resumes cache HIT: {user_id}")
            return cached_resumes
        
        # Cache miss - query database
        logger.debug(f"❌ User resumes cache MISS: {user_id}")
        resumes = await db.resumes.find({"user_id": user_id}).to_list(length=100)
        
        # Cache for shorter time since data can change
        await self.cache_service.set(
            namespace="user_resumes",
            identifier=user_id,
            value=resumes,
            ttl=300,  # 5 minutes
            cache_version="v1"
        )
        
        return resumes
    
    async def get_user_jobs(self, user_id: str, db) -> List[Dict]:
        """Get user jobs with caching"""
        self.stats["db_requests"] += 1
        
        cached_jobs = await self.cache_service.get(
            namespace="user_jobs",
            identifier=user_id,
            cache_version="v1"
        )
        
        if cached_jobs is not None:
            self.stats["db_cache_hits"] += 1
            return cached_jobs
        
        jobs = await db.jobs.find({"user_id": user_id}).to_list(length=100)
        
        await self.cache_service.set(
            namespace="user_jobs",
            identifier=user_id,
            value=jobs,
            ttl=300,  # 5 minutes
            cache_version="v1"
        )
        
        return jobs
    
    async def get_scoring_results(self, job_id: str, user_id: str, db) -> Optional[Dict]:
        """Get scoring results with caching"""
        cache_key = f"{user_id}:{job_id}"
        
        cached_results = await self.cache_service.get(
            namespace="scoring_results",
            identifier=cache_key,
            cache_version="v1"
        )
        
        if cached_results is not None:
            logger.debug(f"✅ Scoring results cache HIT: {cache_key}")
            return cached_results
        
        # Query database
        results = await db.scoring_results.find_one({
            "job_id": job_id,
            "user_id": user_id
        })
        
        if results:
            await self.cache_service.set(
                namespace="scoring_results",
                identifier=cache_key,
                value=results,
                ttl=1800,  # 30 minutes
                cache_version="v1"
            )
        
        return results
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user"""
        await self.cache_service.delete("user_resumes", user_id)
        await self.cache_service.delete("user_jobs", user_id)
        logger.info(f"🗑️ Invalidated cache for user: {user_id}")

class FileProcessingCache:
    """Cache for file processing operations"""
    
    def __init__(self):
        self.cache_service = get_cache_service()
    
    async def get_extracted_text(self, file_hash: str, file_processor_func, file_path: str) -> str:
        """Get extracted text with caching based on file hash"""
        
        cached_text = await self.cache_service.get(
            namespace="file_extraction",
            identifier=file_hash,
            cache_version="v1"
        )
        
        if cached_text is not None:
            logger.debug(f"✅ File extraction cache HIT: {file_hash}")
            return cached_text
        
        # Cache miss - extract text
        logger.debug(f"❌ File extraction cache MISS: {file_hash}")
        extracted_text = await file_processor_func(file_path)
        
        # Cache with long TTL since file content doesn't change
        await self.cache_service.set(
            namespace="file_extraction",
            identifier=file_hash,
            value=extracted_text,
            ttl=86400 * 7,  # 7 days
            cache_version="v1"
        )
        
        return extracted_text
    
    async def get_file_hash_cache(self, content: bytes) -> str:
        """Get or compute file hash with caching"""
        # For file hashes, we can use a simple in-memory cache
        # since hash computation is relatively fast
        content_preview = content[:1024]  # First 1KB for quick hash
        preview_hash = hashlib.md5(content_preview).hexdigest()
        
        cached_full_hash = await self.cache_service.get(
            namespace="file_hashes",
            identifier=preview_hash,
            cache_version="v1"
        )
        
        if cached_full_hash is not None:
            return cached_full_hash
        
        # Compute full hash
        full_hash = hashlib.sha256(content).hexdigest()
        
        # Cache the full hash
        await self.cache_service.set(
            namespace="file_hashes",
            identifier=preview_hash,
            value=full_hash,
            ttl=3600,  # 1 hour
            cache_version="v1"
        )
        
        return full_hash

class ScoringCache:
    """Cache for resume scoring operations"""
    
    def __init__(self):
        self.cache_service = get_cache_service()
        self.embedding_cache = EmbeddingCache()
    
    async def get_similarity_score(self, resume_text: str, job_text: str) -> float:
        """Get similarity score with caching"""
        
        # Create deterministic cache key
        resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()[:12]
        job_hash = hashlib.sha256(job_text.encode()).hexdigest()[:12]
        cache_key = f"{resume_hash}:{job_hash}"
        
        cached_score = await self.cache_service.get(
            namespace="similarity_scores",
            identifier=cache_key,
            algorithm="cosine_similarity"
        )
        
        if cached_score is not None:
            logger.debug(f"✅ Similarity score cache HIT: {cache_key}")
            return cached_score
        
        # Cache miss - calculate similarity
        logger.debug(f"❌ Similarity score cache MISS: {cache_key}")
        
        # Get embeddings (these will be cached separately)
        resume_embedding = await self.embedding_cache.get_text_embedding(resume_text)
        job_embedding = await self.embedding_cache.get_text_embedding(job_text)
        
        # Calculate similarity
        similarity = self._calculate_cosine_similarity(resume_embedding, job_embedding)
        
        # Cache the result
        await self.cache_service.set(
            namespace="similarity_scores",
            identifier=cache_key,
            value=similarity,
            ttl=86400,  # 1 day
            algorithm="cosine_similarity"
        )
        
        return similarity
    
    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    async def get_skills_match(self, resume_skills: List[str], job_skills: List[str]) -> Tuple[List[str], List[str]]:
        """Get skills match with caching"""
        
        # Create cache key from sorted skills
        resume_key = ":".join(sorted([s.lower() for s in resume_skills]))
        job_key = ":".join(sorted([s.lower() for s in job_skills]))
        cache_key = hashlib.sha256(f"{resume_key}|{job_key}".encode()).hexdigest()[:16]
        
        cached_match = await self.cache_service.get(
            namespace="skills_match",
            identifier=cache_key,
            cache_version="v1"
        )
        
        if cached_match is not None:
            return cached_match["matched"], cached_match["missing"]
        
        # Calculate skills match
        job_skills_lower = [s.lower() for s in job_skills]
        matched_skills = [s for s in resume_skills if s.lower() in job_skills_lower]
        missing_skills = [s for s in job_skills if s.lower() not in [rs.lower() for rs in resume_skills]]
        
        result = {"matched": matched_skills, "missing": missing_skills}
        
        await self.cache_service.set(
            namespace="skills_match",
            identifier=cache_key,
            value=result,
            ttl=3600,  # 1 hour
            cache_version="v1"
        )
        
        return matched_skills, missing_skills

class SessionCache:
    """Cache for user session and UI state"""
    
    def __init__(self):
        self.cache_service = get_cache_service()
    
    async def get_dashboard_data(self, user_id: str, db_query_func) -> Dict[str, Any]:
        """Get dashboard data with caching"""
        
        cached_data = await self.cache_service.get(
            namespace="dashboard_data",
            identifier=user_id,
            cache_version="v2"
        )
        
        if cached_data is not None:
            logger.debug(f"✅ Dashboard cache HIT: {user_id}")
            return cached_data
        
        # Cache miss - fetch fresh data
        logger.debug(f"❌ Dashboard cache MISS: {user_id}")
        dashboard_data = await db_query_func(user_id)
        
        # Cache for short time since this is UI data
        await self.cache_service.set(
            namespace="dashboard_data",
            identifier=user_id,
            value=dashboard_data,
            ttl=120,  # 2 minutes
            cache_version="v2"
        )
        
        return dashboard_data
    
    async def cache_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """Cache user preferences"""
        return await self.cache_service.set(
            namespace="user_preferences",
            identifier=user_id,
            value=preferences,
            ttl=86400 * 7,  # 7 days
            cache_version="v1"
        )

# Global instances
_embedding_cache = None
_db_query_cache = None
_file_processing_cache = None
_scoring_cache = None
_session_cache = None

def get_embedding_cache() -> EmbeddingCache:
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache

def get_db_query_cache() -> DatabaseQueryCache:
    global _db_query_cache
    if _db_query_cache is None:
        _db_query_cache = DatabaseQueryCache()
    return _db_query_cache

def get_file_processing_cache() -> FileProcessingCache:
    global _file_processing_cache
    if _file_processing_cache is None:
        _file_processing_cache = FileProcessingCache()
    return _file_processing_cache

def get_scoring_cache() -> ScoringCache:
    global _scoring_cache
    if _scoring_cache is None:
        _scoring_cache = ScoringCache()
    return _scoring_cache

def get_session_cache() -> SessionCache:
    global _session_cache
    if _session_cache is None:
        _session_cache = SessionCache()
    return _session_cache

# Utility function to get all cache statistics
async def get_all_cache_stats() -> Dict[str, Any]:
    """Get statistics from all cache services"""
    
    embedding_cache = get_embedding_cache()
    db_cache = get_db_query_cache()
    
    return {
        "embedding_cache": embedding_cache.stats,
        "database_cache": db_cache.stats,
        "total_cache_services": 5,
        "cache_enabled": settings.CACHE_ENABLED
    }

# Cache warming functions
async def warm_user_cache(user_id: str, db):
    """Warm up cache for a specific user"""
    logger.info(f"🔥 Warming cache for user: {user_id}")
    
    db_cache = get_db_query_cache()
    
    # Preload user data
    await asyncio.gather(
        db_cache.get_user_resumes(user_id, db),
        db_cache.get_user_jobs(user_id, db)
    )
    
    logger.info(f"✅ Cache warmed for user: {user_id}")

async def warm_common_embeddings():
    """Warm up cache with common embeddings"""
    logger.info("🔥 Warming common embeddings cache...")
    
    embedding_cache = get_embedding_cache()
    
    common_texts = [
        "software engineer python react",
        "data scientist machine learning",
        "product manager agile scrum",
        "devops engineer kubernetes aws",
        "frontend developer javascript css"
    ]
    
    await embedding_cache.get_bulk_embeddings(common_texts)
    logger.info("✅ Common embeddings cache warmed")