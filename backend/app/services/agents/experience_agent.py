"""
Experience Relevance Agent

This agent extracts years and seniority from resume and job description,
compares them, and returns structured score (meets/partial/underqualified).
"""

import re
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent, AgentResult, AgentType


class ExperienceRelevanceAgent(BaseAgent):
    """Agent for experience relevance analysis"""
    
    def __init__(self, weight: float = 0.20):
        super().__init__(AgentType.EXPERIENCE_RELEVANCE, weight)
    
    async def analyze(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """Analyze experience relevance between resume and job"""
        try:
            resume_text = self._extract_text_content(resume)
            job_requirements = job.get('requirements', [])
            
            # Extract experience from resume
            resume_experience = self._extract_experience_indicators(resume_text)
            
            # Extract experience requirements from job
            job_experience = self._extract_experience_requirements(job_requirements)
            
            # Calculate experience score
            score, confidence = self._calculate_experience_score(resume_experience, job_experience)
            
            return self._create_result(
                score=score,
                evidence={
                    "resume_experience": resume_experience,
                    "job_experience": job_experience,
                    "years_match": resume_experience.get('years', 0) >= job_experience.get('years', 0),
                    "level_match": self._compare_seniority_levels(
                        resume_experience.get('level', 'junior'),
                        job_experience.get('level', 'junior')
                    ),
                    "experience_gap": max(0, job_experience.get('years', 0) - resume_experience.get('years', 0))
                },
                confidence=confidence
            )
            
        except Exception as e:
            return self._create_result(
                score=0.0,
                evidence={},
                confidence=0.0,
                error=f"Error in experience analysis: {str(e)}"
            )
    
    def _extract_experience_indicators(self, text: str) -> Dict[str, Any]:
        """Extract experience indicators from resume text"""
        text_lower = text.lower()
        experience = {}
        
        # Extract years of experience
        years_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*years?\s*(?:in|of)',
            r'(\d+)\+?\s*years?\s*(?:working|developing|building)',
            r'experience[:\s]*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:professional|relevant)'
        ]
        
        years_found = []
        for pattern in years_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    years = int(match)
                    if 0 <= years <= 50:  # Reasonable range
                        years_found.append(years)
                except ValueError:
                    continue
        
        if years_found:
            experience['years'] = max(years_found)  # Take the highest number
        else:
            # Try to infer from job history
            experience['years'] = self._infer_years_from_jobs(text_lower)
        
        # Extract seniority level
        seniority_patterns = {
            'senior': [r'senior', r'sr\.', r'lead', r'principal', r'staff'],
            'mid': [r'mid-level', r'mid level', r'intermediate', r'experienced'],
            'junior': [r'junior', r'jr\.', r'entry-level', r'entry level', r'associate']
        }
        
        for level, patterns in seniority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    experience['level'] = level
                    break
            if 'level' in experience:
                break
        
        if 'level' not in experience:
            # Infer from years
            years = experience.get('years', 0)
            if years >= 5:
                experience['level'] = 'senior'
            elif years >= 2:
                experience['level'] = 'mid'
            else:
                experience['level'] = 'junior'
        
        return experience
    
    def _extract_experience_requirements(self, requirements: List[str]) -> Dict[str, Any]:
        """Extract experience requirements from job description"""
        experience = {}
        requirements_text = ' '.join(requirements).lower()
        
        # Extract years requirement
        years_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*years?\s*(?:in|of)',
            r'(\d+)\+?\s*years?\s*(?:working|developing|building)',
            r'experience[:\s]*(\d+)\+?\s*years?',
            r'minimum[:\s]*(\d+)\+?\s*years?',
            r'at\s*least[:\s]*(\d+)\+?\s*years?'
        ]
        
        years_found = []
        for pattern in years_patterns:
            matches = re.findall(pattern, requirements_text)
            for match in matches:
                try:
                    years = int(match)
                    if 0 <= years <= 50:  # Reasonable range
                        years_found.append(years)
                except ValueError:
                    continue
        
        if years_found:
            experience['years'] = max(years_found)  # Take the highest requirement
        else:
            experience['years'] = 0  # Default assumption
        
        # Extract seniority level requirement
        seniority_patterns = {
            'senior': [r'senior', r'sr\.', r'lead', r'principal', r'staff'],
            'mid': [r'mid-level', r'mid level', r'intermediate', r'experienced'],
            'junior': [r'junior', r'jr\.', r'entry-level', r'entry level', r'associate']
        }
        
        for level, patterns in seniority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, requirements_text):
                    experience['level'] = level
                    break
            if 'level' in experience:
                break
        
        if 'level' not in experience:
            # Infer from years
            years = experience.get('years', 0)
            if years >= 5:
                experience['level'] = 'senior'
            elif years >= 2:
                experience['level'] = 'mid'
            else:
                experience['level'] = 'junior'  # Default assumption
        
        return experience
    
    def _infer_years_from_jobs(self, text: str) -> int:
        """Infer years of experience from job history"""
        # Look for date patterns in job history
        date_patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4})',  # 2020 - 2023
            r'(\d{4})\s*[-–]\s*present',  # 2020 - present
            r'(\d{4})\s*[-–]\s*current',  # 2020 - current
            r'(\d{4})\s*[-–]\s*now'       # 2020 - now
        ]
        
        years_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    start_year = int(match[0])
                    if len(match) > 1 and match[1].lower() not in ['present', 'current', 'now']:
                        end_year = int(match[1])
                        years_found.append(end_year - start_year)
                    else:
                        # Current job - estimate based on current year
                        from datetime import datetime
                        current_year = datetime.now().year
                        years_found.append(current_year - start_year)
                except (ValueError, IndexError):
                    continue
        
        if years_found:
            return max(years_found)
        
        return 0  # Default if no dates found
    
    def _calculate_experience_score(self, resume_exp: Dict[str, Any], job_exp: Dict[str, Any]) -> tuple[float, float]:
        """Calculate experience relevance score"""
        resume_years = resume_exp.get('years', 0)
        job_years = job_exp.get('years', 0)
        resume_level = resume_exp.get('level', 'junior')
        job_level = job_exp.get('level', 'junior')
        
        # Calculate years score
        if job_years == 0:
            years_score = 1.0  # No requirement specified
        elif resume_years >= job_years:
            years_score = 1.0  # Meets or exceeds requirement
        else:
            # Partial credit for underqualified
            years_score = resume_years / job_years
        
        # Calculate level score
        level_scores = {
            'junior': {'junior': 1.0, 'mid': 0.5, 'senior': 0.2},
            'mid': {'junior': 1.0, 'mid': 1.0, 'senior': 0.6},
            'senior': {'junior': 1.0, 'mid': 1.0, 'senior': 1.0}
        }
        
        level_score = level_scores.get(resume_level, {}).get(job_level, 0.5)
        
        # Combine scores (70% years, 30% level)
        total_score = (years_score * 0.7) + (level_score * 0.3)
        
        # Calculate confidence based on how clear the experience indicators are
        confidence = 1.0
        if resume_years == 0 and job_years == 0:
            confidence = 0.3  # Low confidence when no clear indicators
        elif resume_years == 0 or job_years == 0:
            confidence = 0.6  # Medium confidence when one side is unclear
        
        return min(1.0, total_score), confidence
    
    def _compare_seniority_levels(self, resume_level: str, job_level: str) -> str:
        """Compare seniority levels and return match status"""
        level_hierarchy = {'junior': 1, 'mid': 2, 'senior': 3}
        
        resume_rank = level_hierarchy.get(resume_level, 1)
        job_rank = level_hierarchy.get(job_level, 1)
        
        if resume_rank >= job_rank:
            return "meets"
        elif resume_rank == job_rank - 1:
            return "partial"
        else:
            return "underqualified"
