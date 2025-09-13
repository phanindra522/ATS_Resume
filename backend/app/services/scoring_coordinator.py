"""
Multi-Agent Resume Scoring Coordinator

This module coordinates multiple specialized agents to provide comprehensive
resume scoring using a multi-agent architecture.
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from app.services.agents import (
    KeywordMatchingAgent,
    SkillMatchingAgent,
    ExperienceRelevanceAgent,
    EducationAlignmentAgent,
    SemanticSimilarityAgent,
    AgentResult,
    AgentType
)


@dataclass
class ScoringBreakdown:
    """Structured scoring breakdown from multi-agent system"""
    keyword_match: Dict[str, Any]
    skills_alignment: Dict[str, Any]
    experience_relevance: Dict[str, Any]
    education_alignment: Dict[str, Any]
    semantic_similarity: Dict[str, Any]
    total_score: float
    match_percentage: float
    skills_match: List[str]
    missing_skills: List[str]
    agent_results: Dict[str, AgentResult]
    confidence: float
    timestamp: datetime


class MultiAgentScoringCoordinator:
    """Coordinates multiple agents for comprehensive resume scoring"""
    
    def __init__(self):
        # Initialize all agents with their weights
        self.agents = {
            AgentType.KEYWORD_MATCHING: KeywordMatchingAgent(weight=0.20),
            AgentType.SKILL_MATCHING: SkillMatchingAgent(weight=0.25),
            AgentType.EXPERIENCE_RELEVANCE: ExperienceRelevanceAgent(weight=0.20),
            AgentType.EDUCATION_ALIGNMENT: EducationAlignmentAgent(weight=0.10),
            AgentType.SEMANTIC_SIMILARITY: SemanticSimilarityAgent(weight=0.25)
        }
        
        # Verify weights sum to 1.0
        total_weight = sum(agent.weight for agent in self.agents.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Agent weights must sum to 1.0, got {total_weight}")
    
    async def score_resume(self, resume: Dict[str, Any], job: Dict[str, Any]) -> ScoringBreakdown:
        """
        Score a resume against a job description using multi-agent system
        
        Args:
            resume: Resume data dictionary
            job: Job description data dictionary
            
        Returns:
            ScoringBreakdown with comprehensive scoring results
        """
        try:
            # Run all agents in parallel for efficiency
            agent_tasks = []
            for agent_type, agent in self.agents.items():
                task = asyncio.create_task(agent.analyze(resume, job))
                agent_tasks.append((agent_type, task))
            
            # Wait for all agents to complete
            agent_results = {}
            for agent_type, task in agent_tasks:
                try:
                    result = await task
                    agent_results[agent_type.value] = result
                except Exception as e:
                    # Create error result for failed agent
                    agent_results[agent_type.value] = AgentResult(
                        agent_type=agent_type,
                        score=0.0,
                        percentage=0.0,
                        weight=self.agents[agent_type].weight,
                        evidence={},
                        confidence=0.0,
                        error=f"Agent failed: {str(e)}"
                    )
            
            # Calculate weighted total score
            total_score = 0.0
            total_confidence = 0.0
            valid_agents = 0
            
            for agent_type, result in agent_results.items():
                if result.error is None:
                    total_score += result.score * result.weight
                    total_confidence += result.confidence * result.weight
                    valid_agents += 1
            
            # Normalize confidence
            if valid_agents > 0:
                total_confidence = total_confidence / sum(result.weight for result in agent_results.values() if result.error is None)
            else:
                total_confidence = 0.0
            
            # Extract skills information from skill matching agent
            skill_result = agent_results.get(AgentType.SKILL_MATCHING.value)
            skills_match = []
            missing_skills = []
            
            if skill_result and skill_result.error is None:
                evidence = skill_result.evidence
                skills_match = evidence.get('matched_skills', [])
                missing_skills = evidence.get('missing_skills', [])
            
            # Create structured breakdown
            breakdown = ScoringBreakdown(
                keyword_match=self._format_agent_result(agent_results.get(AgentType.KEYWORD_MATCHING.value)),
                skills_alignment=self._format_agent_result(agent_results.get(AgentType.SKILL_MATCHING.value)),
                experience_relevance=self._format_agent_result(agent_results.get(AgentType.EXPERIENCE_RELEVANCE.value)),
                education_alignment=self._format_agent_result(agent_results.get(AgentType.EDUCATION_ALIGNMENT.value)),
                semantic_similarity=self._format_agent_result(agent_results.get(AgentType.SEMANTIC_SIMILARITY.value)),
                total_score=total_score,
                match_percentage=total_score * 100,
                skills_match=skills_match,
                missing_skills=missing_skills,
                agent_results=agent_results,
                confidence=total_confidence,
                timestamp=datetime.utcnow()
            )
            
            return breakdown
            
        except Exception as e:
            # Return error breakdown
            return ScoringBreakdown(
                keyword_match={"score": 0.0, "percentage": 0.0, "weight": 20, "error": str(e)},
                skills_alignment={"score": 0.0, "percentage": 0.0, "weight": 25, "error": str(e)},
                experience_relevance={"score": 0.0, "percentage": 0.0, "weight": 20, "error": str(e)},
                education_alignment={"score": 0.0, "percentage": 0.0, "weight": 10, "error": str(e)},
                semantic_similarity={"score": 0.0, "percentage": 0.0, "weight": 25, "error": str(e)},
                total_score=0.0,
                match_percentage=0.0,
                skills_match=[],
                missing_skills=[],
                agent_results={},
                confidence=0.0,
                timestamp=datetime.utcnow()
            )
    
    def _format_agent_result(self, result: Optional[AgentResult]) -> Dict[str, Any]:
        """Format agent result for API response"""
        if result is None:
            return {
                "score": 0.0,
                "percentage": 0.0,
                "weight": 0,
                "error": "Agent not available"
            }
        
        return {
            "score": result.score,
            "percentage": result.percentage,
            "weight": int(result.weight * 100),
            "confidence": result.confidence,
            "evidence": result.evidence,
            "error": result.error
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {}
        for agent_type, agent in self.agents.items():
            status[agent_type.value] = {
                "weight": agent.weight,
                "type": agent_type.value,
                "available": True
            }
        return status
    
    def get_scoring_formula(self) -> str:
        """Get the scoring formula used by the coordinator"""
        formula_parts = []
        for agent_type, agent in self.agents.items():
            formula_parts.append(f"({agent_type.value.replace('_', ' ').title()} × {agent.weight:.2f})")
        
        return " + ".join(formula_parts)


# Global coordinator instance
coordinator = MultiAgentScoringCoordinator()
