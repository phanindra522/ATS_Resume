"""
Cached LLM Service - Wrapper around existing LLM service with intelligent caching
Reduces token usage and improves response times significantly
"""
import hashlib
import json
import asyncio
from typing import Dict, Any, Optional
import logging
from app.services.llm_service import parse_job_with_llm, LLMProvider, LLMServiceFactory
from app.services.cache_service import get_cache_service, cached, cache_stats
from app.core.config import settings

logger = logging.getLogger(__name__)

class CachedLLMService:
    """Cached wrapper around LLM service for token optimization"""
    
    def __init__(self):
        self.cache_service = get_cache_service()
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "tokens_saved": 0  # Estimated
        }
    
    async def parse_job_description(self, text: str, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """
        Parse job description with intelligent caching
        
        Args:
            text: Job description text to parse
            provider: LLM provider to use (optional)
        
        Returns:
            Dictionary with parsed job information
        """
        self.stats["total_requests"] += 1
        
        # Clean and normalize text for consistent caching
        normalized_text = self._normalize_text(text)
        
        # Generate cache key based on text content and provider
        provider_name = provider.value if provider else settings.LLM_PROVIDER
        cache_key = self._generate_content_hash(normalized_text, provider_name)
        
        # Try to get from cache first
        cached_result = await self.cache_service.get(
            namespace="llm_job_parse",
            identifier=cache_key,
            provider=provider_name,
            text_length=len(normalized_text)
        )
        
        if cached_result is not None:
            self.stats["cache_hits"] += 1
            cache_stats.hit()
            # Estimate tokens saved (rough calculation)
            self.stats["tokens_saved"] += self._estimate_tokens(text)
            logger.info(f"✅ LLM Cache HIT for job parsing (saved ~{self._estimate_tokens(text)} tokens)")
            return cached_result
        
        # Cache miss - call actual LLM API
        cache_stats.miss()
        self.stats["api_calls"] += 1
        logger.info(f"❌ LLM Cache MISS - calling API (~{self._estimate_tokens(text)} tokens)")
        
        try:
            # Call the actual LLM service
            result = await parse_job_with_llm(normalized_text, provider)
            
            # Cache the successful result
            await self.cache_service.set(
                namespace="llm_job_parse",
                identifier=cache_key,
                value=result,
                ttl=settings.CACHE_LLM_TTL_SECONDS,
                provider=provider_name,
                text_length=len(normalized_text)
            )
            
            cache_stats.set_operation()
            logger.info(f"💾 LLM result cached for future use")
            
            return result
            
        except Exception as e:
            cache_stats.error()
            logger.error(f"LLM API call failed: {e}")
            raise
    
    async def parse_job_with_similarity_check(self, text: str, similarity_threshold: float = 0.95) -> Dict[str, Any]:
        """
        Parse job with similarity-based caching for near-duplicate content
        
        Args:
            text: Job description text
            similarity_threshold: Threshold for considering content similar (0.0-1.0)
        
        Returns:
            Dictionary with parsed job information
        """
        # TODO: Implement semantic similarity caching
        # This would check against previously parsed similar content
        # For now, fall back to exact match caching
        return await self.parse_job_description(text)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent caching"""
        # Remove extra whitespace, normalize line endings
        normalized = " ".join(text.split())
        # Convert to lowercase for case-insensitive caching
        normalized = normalized.lower().strip()
        return normalized
    
    def _generate_content_hash(self, text: str, provider: str) -> str:
        """Generate deterministic hash from content and provider"""
        content = f"{provider}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token for English)"""
        return len(text) // 4
    
    def get_stats(self) -> Dict[str, Any]:
        """Get caching statistics"""
        hit_ratio = self.stats["cache_hits"] / max(1, self.stats["total_requests"])
        
        return {
            **self.stats,
            "cache_hit_ratio": hit_ratio,
            "api_call_ratio": 1 - hit_ratio,
            "estimated_cost_savings": f"${(self.stats['tokens_saved'] * 0.000001):.4f}",  # Rough estimate
            "cache_service_stats": cache_stats.get_stats()
        }
    
    async def clear_cache(self) -> bool:
        """Clear LLM cache"""
        return await self.cache_service.clear_namespace("llm_job_parse")
    
    async def warmup_cache(self, job_samples: list) -> Dict[str, int]:
        """
        Warm up cache with common job descriptions
        
        Args:
            job_samples: List of job description texts to pre-cache
        
        Returns:
            Dictionary with warmup statistics
        """
        warmup_stats = {"processed": 0, "cached": 0, "errors": 0}
        
        for i, text in enumerate(job_samples):
            try:
                logger.info(f"Warming up cache: {i+1}/{len(job_samples)}")
                await self.parse_job_description(text)
                warmup_stats["processed"] += 1
                warmup_stats["cached"] += 1
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Cache warmup failed for sample {i}: {e}")
                warmup_stats["errors"] += 1
        
        return warmup_stats

# Skill extraction caching
class CachedSkillExtractor:
    """Cached skill extraction service"""
    
    def __init__(self):
        self.cache_service = get_cache_service()
        
        # Common skills cache (in-memory for speed)
        self.common_skills = {
            "programming": ["python", "javascript", "java", "c++", "sql", "html", "css"],
            "frameworks": ["react", "angular", "django", "flask", "spring", "express"],
            "tools": ["git", "docker", "kubernetes", "aws", "jenkins", "jira"],
            "databases": ["mysql", "postgresql", "mongodb", "redis", "elasticsearch"]
        }
    
    async def extract_skills(self, text: str, use_llm: bool = False) -> list:
        """Extract skills with caching"""
        normalized_text = text.lower().strip()
        cache_key = hashlib.sha256(normalized_text.encode()).hexdigest()[:12]
        
        # Try cache first
        cached_skills = await self.cache_service.get(
            namespace="skill_extraction",
            identifier=cache_key,
            method="llm" if use_llm else "rule_based"
        )
        
        if cached_skills is not None:
            logger.debug(f"Skills cache HIT: {len(cached_skills)} skills")
            return cached_skills
        
        # Extract skills
        if use_llm and settings.USE_LLM_FOR_SKILLS:
            # TODO: Implement LLM-based skill extraction
            skills = self._extract_skills_rule_based(text)
        else:
            skills = self._extract_skills_rule_based(text)
        
        # Cache results
        await self.cache_service.set(
            namespace="skill_extraction",
            identifier=cache_key,
            value=skills,
            ttl=settings.CACHE_TTL_SECONDS,
            method="llm" if use_llm else "rule_based"
        )
        
        logger.debug(f"Skills extracted and cached: {len(skills)} skills")
        return skills
    
    def _extract_skills_rule_based(self, text: str) -> list:
        """Rule-based skill extraction (fast, cached)"""
        text_lower = text.lower()
        found_skills = []
        
        # Check all common skills
        for category, skills in self.common_skills.items():
            for skill in skills:
                if skill in text_lower and skill not in found_skills:
                    found_skills.append(skill)
        
        return found_skills[:20]  # Limit results

# Global instances
_cached_llm_service = None
_cached_skill_extractor = None

def get_cached_llm_service() -> CachedLLMService:
    """Get global cached LLM service instance"""
    global _cached_llm_service
    if _cached_llm_service is None:
        _cached_llm_service = CachedLLMService()
        logger.info("🚀 Cached LLM service initialized")
    return _cached_llm_service

def get_cached_skill_extractor() -> CachedSkillExtractor:
    """Get global cached skill extractor instance"""
    global _cached_skill_extractor
    if _cached_skill_extractor is None:
        _cached_skill_extractor = CachedSkillExtractor()
        logger.info("🚀 Cached skill extractor initialized")
    return _cached_skill_extractor

# Convenience functions for easy replacement
async def parse_job_with_cached_llm(text: str, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
    """Drop-in replacement for parse_job_with_llm with caching"""
    service = get_cached_llm_service()
    return await service.parse_job_description(text, provider)

async def extract_skills_cached(text: str, use_llm: bool = False) -> list:
    """Extract skills with caching"""
    extractor = get_cached_skill_extractor()
    return await extractor.extract_skills(text, use_llm)