"""
Education Alignment Agent

This agent extracts degree level and field of study from resume and job,
compares them, and returns score (full/partial/underqualified).
"""

import re
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent, AgentResult, AgentType


class EducationAlignmentAgent(BaseAgent):
    """Agent for education alignment analysis"""
    
    def __init__(self, weight: float = 0.10):
        super().__init__(AgentType.EDUCATION_ALIGNMENT, weight)
        self.degree_levels = self._init_degree_levels()
        self.field_mappings = self._init_field_mappings()
    
    def _init_degree_levels(self) -> Dict[str, int]:
        """Initialize degree level hierarchy"""
        return {
            'phd': 4,
            'doctorate': 4,
            'doctoral': 4,
            'ph.d.': 4,
            'd.phil': 4,
            'master': 3,
            'mba': 3,
            'ms': 3,
            'ma': 3,
            'm.s.': 3,
            'm.a.': 3,
            'masters': 3,
            'm.sc': 3,
            'm.eng': 3,
            'bachelor': 2,
            'bs': 2,
            'ba': 2,
            'b.s.': 2,
            'b.a.': 2,
            'bachelor\'s': 2,
            'b.tech': 2,
            'b.eng': 2,
            'b.sc': 2,
            'associate': 1,
            'diploma': 1,
            'certificate': 1,
            'high school': 0,
            'secondary': 0
        }
    
    def _init_field_mappings(self) -> Dict[str, List[str]]:
        """Initialize field of study mappings for related fields"""
        return {
            'computer science': ['computer science', 'cs', 'computing', 'software engineering', 'computer engineering'],
            'engineering': ['engineering', 'mechanical engineering', 'electrical engineering', 'civil engineering', 'computer engineering'],
            'business': ['business', 'business administration', 'mba', 'management', 'marketing', 'finance', 'economics'],
            'data science': ['data science', 'statistics', 'mathematics', 'applied mathematics', 'analytics'],
            'design': ['design', 'graphic design', 'ui/ux design', 'industrial design', 'visual design'],
            'marketing': ['marketing', 'business', 'communications', 'advertising', 'public relations'],
            'finance': ['finance', 'accounting', 'economics', 'business', 'financial engineering'],
            'healthcare': ['medicine', 'nursing', 'pharmacy', 'healthcare', 'public health', 'biology'],
            'education': ['education', 'teaching', 'pedagogy', 'educational technology'],
            'psychology': ['psychology', 'counseling', 'social work', 'human resources']
        }
    
    async def analyze(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """Analyze education alignment between resume and job"""
        try:
            resume_text = self._extract_text_content(resume)
            job_requirements = job.get('requirements', [])
            
            # Extract education from resume
            resume_education = self._extract_education(resume_text)
            
            # Extract education requirements from job
            job_education = self._extract_education_requirements(job_requirements)
            
            # Calculate education score
            score, confidence = self._calculate_education_score(resume_education, job_education)
            
            return self._create_result(
                score=score,
                evidence={
                    "resume_education": resume_education,
                    "job_education": job_education,
                    "degree_level_match": resume_education.get('level', 0) >= job_education.get('level', 0),
                    "field_match": self._compare_fields(
                        resume_education.get('field', ''),
                        job_education.get('field', '')
                    ),
                    "education_gap": max(0, job_education.get('level', 0) - resume_education.get('level', 0))
                },
                confidence=confidence
            )
            
        except Exception as e:
            return self._create_result(
                score=0.0,
                evidence={},
                confidence=0.0,
                error=f"Error in education analysis: {str(e)}"
            )
    
    def _extract_education(self, text: str) -> Dict[str, Any]:
        """Extract education information from resume text"""
        text_lower = text.lower()
        education = {}
        
        # Extract degree level
        degree_patterns = {
            'phd': [r'phd', r'ph\.d\.', r'doctorate', r'doctoral', r'd\.phil'],
            'masters': [r'master', r'mba', r'ms', r'ma', r'm\.s\.', r'm\.a\.', r'masters', r'm\.sc', r'm\.eng'],
            'bachelors': [r'bachelor', r'bs', r'ba', r'b\.s\.', r'b\.a\.', r'bachelor\'s', r'b\.tech', r'b\.eng', r'b\.sc'],
            'associate': [r'associate', r'diploma', r'certificate'],
            'high school': [r'high school', r'secondary', r'gce', r'a-levels']
        }
        
        for level, patterns in degree_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    education['degree_level'] = level
                    education['level'] = self.degree_levels.get(level, 0)
                    break
            if 'degree_level' in education:
                break
        
        if 'degree_level' not in education:
            education['degree_level'] = 'bachelor'  # Default assumption
            education['level'] = 2
        
        # Extract field of study
        field_patterns = [
            r'(?:bachelor|master|phd|bs|ba|ms|ma|mba).*?(?:in|of)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'degree[:\s]*(?:in|of)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'studied[:\s]*(?:in|at)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'major[:\s]*in\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'field[:\s]*of\s+study[:\s]*([a-zA-Z\s]+?)(?:\s|,|\.|$)'
        ]
        
        for pattern in field_patterns:
            match = re.search(pattern, text_lower)
            if match:
                field = match.group(1).strip()
                if len(field) > 2 and len(field) < 50:  # Reasonable field length
                    education['field'] = field
                    break
        
        if 'field' not in education:
            education['field'] = 'general'  # Default assumption
        
        return education
    
    def _extract_education_requirements(self, requirements: List[str]) -> Dict[str, Any]:
        """Extract education requirements from job description"""
        education = {}
        requirements_text = ' '.join(requirements).lower()
        
        # Extract degree level requirement
        degree_patterns = {
            'phd': [r'phd', r'ph\.d\.', r'doctorate', r'doctoral'],
            'masters': [r'master', r'mba', r'ms', r'ma', r'm\.s\.', r'm\.a\.', r'masters'],
            'bachelors': [r'bachelor', r'bs', r'ba', r'b\.s\.', r'b\.a\.', r'bachelor\'s', r'degree'],
            'associate': [r'associate', r'diploma', r'certificate'],
            'high school': [r'high school', r'secondary']
        }
        
        for level, patterns in degree_patterns.items():
            for pattern in patterns:
                if re.search(pattern, requirements_text):
                    education['degree_level'] = level
                    education['level'] = self.degree_levels.get(level, 0)
                    break
            if 'degree_level' in education:
                break
        
        if 'degree_level' not in education:
            # Look for general degree requirement
            if re.search(r'degree', requirements_text):
                education['degree_level'] = 'bachelor'
                education['level'] = 2
            else:
                education['degree_level'] = 'high school'
                education['level'] = 0
        
        # Extract field requirement
        field_patterns = [
            r'(?:degree|bachelor|master|phd).*?(?:in|of)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'education[:\s]*(?:in|of)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'background[:\s]*(?:in|of)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'studied[:\s]*(?:in|at)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)'
        ]
        
        for pattern in field_patterns:
            match = re.search(pattern, requirements_text)
            if match:
                field = match.group(1).strip()
                if len(field) > 2 and len(field) < 50:
                    education['field'] = field
                    break
        
        if 'field' not in education:
            education['field'] = 'general'  # Default assumption
        
        return education
    
    def _calculate_education_score(self, resume_edu: Dict[str, Any], job_edu: Dict[str, Any]) -> tuple[float, float]:
        """Calculate education alignment score"""
        resume_level = resume_edu.get('level', 0)
        job_level = job_edu.get('level', 0)
        resume_field = resume_edu.get('field', '').lower()
        job_field = job_edu.get('field', '').lower()
        
        # Calculate level score
        if job_level == 0:
            level_score = 1.0  # No education requirement
        elif resume_level >= job_level:
            level_score = 1.0  # Meets or exceeds requirement
        else:
            # Partial credit for underqualified
            level_score = resume_level / max(job_level, 1)
        
        # Calculate field score
        field_score = self._calculate_field_score(resume_field, job_field)
        
        # Combine scores (70% level, 30% field)
        total_score = (level_score * 0.7) + (field_score * 0.3)
        
        # Calculate confidence based on how clear the education indicators are
        confidence = 1.0
        if resume_level == 0 and job_level == 0:
            confidence = 0.3  # Low confidence when no clear indicators
        elif resume_level == 0 or job_level == 0:
            confidence = 0.6  # Medium confidence when one side is unclear
        
        return min(1.0, total_score), confidence
    
    def _calculate_field_score(self, resume_field: str, job_field: str) -> float:
        """Calculate field of study alignment score"""
        if not resume_field or not job_field or resume_field == 'general' or job_field == 'general':
            return 0.5  # Neutral score for unclear fields
        
        # Check for exact match
        if resume_field == job_field:
            return 1.0
        
        # Check for related fields
        for category, related_fields in self.field_mappings.items():
            if resume_field in related_fields and job_field in related_fields:
                return 0.8  # High score for related fields
            
            if resume_field in related_fields or job_field in related_fields:
                # Check if they're in the same category
                if any(field in resume_field for field in related_fields) and any(field in job_field for field in related_fields):
                    return 0.6  # Medium score for same category
        
        # Check for partial matches
        resume_words = set(resume_field.split())
        job_words = set(job_field.split())
        common_words = resume_words & job_words
        
        if common_words:
            return 0.4  # Low score for partial matches
        
        return 0.2  # Very low score for unrelated fields
    
    def _compare_fields(self, resume_field: str, job_field: str) -> str:
        """Compare fields and return match status"""
        if not resume_field or not job_field:
            return "unclear"
        
        field_score = self._calculate_field_score(resume_field.lower(), job_field.lower())
        
        if field_score >= 0.8:
            return "exact"
        elif field_score >= 0.6:
            return "related"
        elif field_score >= 0.4:
            return "partial"
        else:
            return "unrelated"
