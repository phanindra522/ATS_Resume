"""
Base Agent Class for Multi-Agent Scoring System

This module defines the base interface that all scoring agents must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


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
    """Base class for all scoring agents"""
    
    def __init__(self, agent_type: AgentType, weight: float):
        self.agent_type = agent_type
        self.weight = weight
    
    @abstractmethod
    async def analyze(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """
        Analyze resume against job description
        
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
