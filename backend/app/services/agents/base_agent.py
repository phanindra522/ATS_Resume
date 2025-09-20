"""
Base Agent Class for Multi-Agent Scoring System

This module defines the base interface that all scoring agents must implement.
Enhanced with comprehensive caching capabilities for optimal performance.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time


class AgentType(Enum):
    """Types of scoring agents"""
    KEYWORD_MATCHING = "keyword_matching"
    SKILL_MATCHING = "skill_matching"
    EXPERIENCE_RELEVANCE = "experience_relevance"
    EDUCATION_ALIGNMENT = "education_alignment"
    SEMANTIC_SIMILARITY = "semantic_similarity"


@dataclass
class AgentResult:
    """Standardized result format for all agents"""
    agent_type: AgentType
    score: float  # Normalized score (0-1)
    percentage: float  # Percentage (0-100)
    weight: float  # Weight in final calculation
    evidence: Dict[str, Any]  # Raw evidence (matched/missing items, etc.)
    confidence: float = 1.0  # Confidence level (0-1)
    error: Optional[str] = None  # Error message if any


class BaseAgent(ABC):
    """Base class for all scoring agents with caching support"""
    
    def __init__(self, agent_type: AgentType, weight: float, use_cache: bool = True):
        self.agent_type = agent_type
        self.weight = weight
        self.use_cache = use_cache
        self._agent_cache = None  # Will be initialized when needed
    
    async def analyze(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """
        Analyze resume against job description with caching support
        
        Args:
            resume: Resume data dictionary
            job: Job description data dictionary
            
        Returns:
            AgentResult with score, evidence, and metadata
        """
        # Try cache first if enabled
        if self.use_cache:
            cached_result = await self._get_cached_result(resume, job)
            if cached_result is not None:
                return cached_result
        
        # Perform actual analysis
        start_time = time.time()
        result = await self._analyze_impl(resume, job)
        analysis_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Add performance metadata
        if result.evidence is None:
            result.evidence = {}
        result.evidence["analysis_time_ms"] = analysis_time
        result.evidence["cached"] = False
        
        # Cache the result if enabled
        if self.use_cache and result.error is None:
            await self._cache_result(resume, job, result)
        
        return result

    @abstractmethod
    async def _analyze_impl(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """
        Implementation of the actual analysis logic (to be implemented by subclasses)
        
        Args:
            resume: Resume data dictionary
            job: Job description data dictionary
            
        Returns:
            AgentResult with score, evidence, and metadata
        """
        pass
    
    def _create_result(
        self, 
        score: float, 
        evidence: Dict[str, Any], 
        confidence: float = 1.0,
        error: Optional[str] = None
    ) -> AgentResult:
        """Helper method to create standardized AgentResult"""
        return AgentResult(
            agent_type=self.agent_type,
            score=max(0.0, min(1.0, score)),  # Clamp to [0, 1]
            percentage=score * 100,
            weight=self.weight,
            evidence=evidence,
            confidence=confidence,
            error=error
        )
    
    def _extract_text_content(self, resume: Dict[str, Any]) -> str:
        """Extract text content from resume"""
        title = resume.get('title', '')
        text_content = resume.get('text_content', '')
        return f"{title} {text_content}".strip()
    
    def _extract_job_content(self, job: Dict[str, Any]) -> str:
        """Extract text content from job description"""
        title = job.get('title', '')
        company = job.get('company', '')
        description = job.get('description', '')
        requirements = ' '.join(job.get('requirements', []))
        skills = ' '.join(job.get('skills', []))
        return f"{title} {company} {description} {requirements} {skills}".strip()

    @property
    def agent_cache(self):
        """Lazy initialization of cache service"""
        if self._agent_cache is None:
            try:
                from app.services.agent_cache import agent_cache_service
                self._agent_cache = agent_cache_service
            except ImportError:
                print(f"Warning: Agent cache service not available for {self.agent_type.value}")
                self._agent_cache = None
        return self._agent_cache

    async def _get_cached_result(self, resume: Dict[str, Any], job: Dict[str, Any]) -> Optional[AgentResult]:
        """Get cached result for this agent"""
        if not self.agent_cache:
            return None
        
        try:
            cached = await self.agent_cache.get_agent_result(
                self.agent_type, resume, job, self._get_cache_context()
            )
            
            if cached is not None:
                # Mark as cached and update metadata
                if cached.evidence is None:
                    cached.evidence = {}
                cached.evidence["cached"] = True
                cached.evidence["analysis_time_ms"] = 0  # Cached results are instant
                
            return cached
        except Exception as e:
            print(f"Error getting cached result for {self.agent_type.value}: {e}")
            return None

    async def _cache_result(self, resume: Dict[str, Any], job: Dict[str, Any], result: AgentResult) -> bool:
        """Cache result for this agent"""
        if not self.agent_cache:
            return False
        
        try:
            return await self.agent_cache.set_agent_result(
                self.agent_type, resume, job, result, self._get_cache_context()
            )
        except Exception as e:
            print(f"Error caching result for {self.agent_type.value}: {e}")
            return False

    def _get_cache_context(self) -> Optional[str]:
        """
        Get additional context for cache key generation (override in subclasses if needed)
        
        Returns:
            Optional context string that affects caching (e.g., model version, configuration)
        """
        return None

    async def clear_cache(self) -> Dict[str, int]:
        """Clear cache for this agent"""
        if not self.agent_cache:
            return {"error": "Cache service not available"}
        
        try:
            return await self.agent_cache.clear_agent_cache(self.agent_type)
        except Exception as e:
            return {"error": str(e)}

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for this agent"""
        if not self.agent_cache:
            return {"error": "Cache service not available"}
        
        try:
            all_stats = await self.agent_cache.get_cache_stats()
            agent_stats = all_stats["multi_agent_stats"]["agent_hit_rates"].get(
                self.agent_type.value, 0
            )
            
            return {
                "agent_type": self.agent_type.value,
                "hit_rate_percentage": agent_stats,
                "cache_enabled": self.use_cache,
                "ttl_seconds": self.agent_cache.agent_ttls.get(self.agent_type, 3600)
            }
        except Exception as e:
            return {"error": str(e)}
