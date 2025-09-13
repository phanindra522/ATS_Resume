"""
Skill Matching Agent

This agent normalizes skills using LLM taxonomy mapping,
compares JD required skills vs resume skills, and returns
matched/missing skills with score.
"""

import json
import re
from typing import Dict, List, Any, Set, Optional
from pathlib import Path
from .base_agent import BaseAgent, AgentResult, AgentType


class SkillMatchingAgent(BaseAgent):
    """Agent for skill matching with LLM taxonomy normalization"""
    
    def __init__(self, weight: float = 0.25):
        super().__init__(AgentType.SKILL_MATCHING, weight)
        self.skill_taxonomy = self._load_skill_taxonomy()
        self.skill_mappings = self._build_skill_mappings()
    
    def _load_skill_taxonomy(self) -> Dict:
        """Load skill taxonomy from JSON file"""
        taxonomy_path = Path(__file__).parent.parent / "skill_taxonomy.json"
        try:
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load skill taxonomy: {e}")
            return {}
    
    def _build_skill_mappings(self) -> Dict[str, str]:
        """Build skill mappings from taxonomy"""
        mappings = {}
        if self.skill_taxonomy:
            for category, skills in self.skill_taxonomy.items():
                if isinstance(skills, dict):
                    for skill, variations in skills.items():
                        # Add the skill itself
                        mappings[skill.lower()] = skill.lower()
                        # Add all variations
                        if isinstance(variations, list):
                            for variation in variations:
                                mappings[variation.lower()] = skill.lower()
        return mappings
    
    async def analyze(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """Analyze skill alignment between resume and job"""
        try:
            resume_text = self._extract_text_content(resume)
            job_skills = [skill.lower() for skill in job.get('skills', [])]
            
            # Extract skills from resume
            resume_skills = self._extract_skills(resume_text)
            
            if not job_skills:
                return self._create_result(
                    score=0.0,
                    evidence={
                        "resume_skills": resume_skills,
                        "job_skills": [],
                        "matched_skills": [],
                        "missing_skills": [],
                        "total_job_skills": 0,
                        "total_resume_skills": len(resume_skills)
                    },
                    confidence=0.0,
                    error="No skills specified in job description"
                )
            
            # Normalize skills
            resume_normalized = [self._normalize_skill(skill) for skill in resume_skills]
            job_normalized = [self._normalize_skill(skill) for skill in job_skills]
            
            # Remove None values
            resume_normalized = [s for s in resume_normalized if s is not None]
            job_normalized = [s for s in job_normalized if s is not None]
            
            if not job_normalized:
                return self._create_result(
                    score=0.0,
                    evidence={
                        "resume_skills": resume_skills,
                        "job_skills": job_skills,
                        "matched_skills": [],
                        "missing_skills": [],
                        "total_job_skills": 0,
                        "total_resume_skills": len(resume_skills)
                    },
                    confidence=0.0,
                    error="No valid skills found in job description after normalization"
                )
            
            # Calculate overlap
            matched_skills = set(resume_normalized) & set(job_normalized)
            missing_skills = set(job_normalized) - set(resume_normalized)
            
            # Calculate score
            alignment_ratio = len(matched_skills) / len(job_normalized)
            score = min(1.0, alignment_ratio)
            
            # Calculate confidence based on skill coverage
            skill_coverage = len(matched_skills) / max(len(job_normalized), 1)
            confidence = min(1.0, skill_coverage + 0.1)  # Small boost for having any matches
            
            return self._create_result(
                score=score,
                evidence={
                    "resume_skills": resume_skills,
                    "job_skills": job_skills,
                    "resume_skills_normalized": resume_normalized,
                    "job_skills_normalized": job_normalized,
                    "matched_skills": list(matched_skills),
                    "missing_skills": list(missing_skills),
                    "total_job_skills": len(job_normalized),
                    "total_resume_skills": len(resume_normalized),
                    "alignment_ratio": alignment_ratio,
                    "skill_coverage": skill_coverage
                },
                confidence=confidence
            )
            
        except Exception as e:
            return self._create_result(
                score=0.0,
                evidence={},
                confidence=0.0,
                error=f"Error in skill analysis: {str(e)}"
            )
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text with context awareness"""
        text_lower = text.lower()
        found_skills = set()
        
        # Skills section patterns
        skills_section_patterns = [
            r'skills?[:\s]*([^.\n]+?)(?:\n|\.|$)',
            r'technical\s+skills?[:\s]*([^.\n]+?)(?:\n|\.|$)',
            r'technologies?[:\s]*([^.\n]+?)(?:\n|\.|$)',
            r'programming\s+languages?[:\s]*([^.\n]+?)(?:\n|\.|$)',
            r'frameworks?[:\s]*([^.\n]+?)(?:\n|\.|$)',
            r'tools?[:\s]*([^.\n]+?)(?:\n|\.|$)',
            r'expertise\s+in[:\s]*([^.\n]+?)(?:\n|\.|$)',
            r'proficient\s+in[:\s]*([^.\n]+?)(?:\n|\.|$)',
            r'experience\s+with[:\s]*([^.\n]+?)(?:\n|\.|$)',
            r'familiar\s+with[:\s]*([^.\n]+?)(?:\n|\.|$)'
        ]
        
        for pattern in skills_section_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                skills_in_section = self._extract_skills_from_section(match)
                found_skills.update(skills_in_section)
        
        # Experience-based skill extraction
        experience_patterns = [
            r'(?:developed|built|created|implemented|designed|architected|programmed|coded)\s+(?:using\s+)?([^.\n]+?)(?:\s|,|\.|$)',
            r'(?:worked\s+with|used|utilized|leveraged)\s+([^.\n]+?)(?:\s|,|\.|$)',
            r'(?:experience\s+in|expertise\s+in|proficient\s+in)\s+([^.\n]+?)(?:\s|,|\.|$)',
            r'(?:technologies?|tools?|frameworks?|languages?)[:\s]*([^.\n]+?)(?:\n|\.|$)'
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                skills_in_experience = self._extract_skills_from_section(match)
                found_skills.update(skills_in_experience)
        
        # Direct skill mentions with context validation
        for variation, canonical in self.skill_mappings.items():
            if self._is_skill_in_context(text_lower, variation):
                found_skills.add(canonical)
        
        return list(found_skills)
    
    def _extract_skills_from_section(self, section_text: str) -> List[str]:
        """Extract skills from a specific section of text"""
        skills = set()
        section_lower = section_text.lower()
        
        # Split by common separators
        skill_candidates = re.split(r'[,;|•\n\t]+', section_lower)
        
        for candidate in skill_candidates:
            candidate = candidate.strip()
            if len(candidate) < 2 or len(candidate) > 50:
                continue
                
            # Check if it matches any known skill
            normalized = self._normalize_skill(candidate)
            if normalized:
                skills.add(normalized)
        
        return list(skills)
    
    def _is_skill_in_context(self, text: str, skill: str) -> bool:
        """Check if a skill appears in a meaningful context"""
        # Define technical skills that should be more strictly validated
        technical_skills = {
            'javascript', 'typescript', 'python', 'java', 'react', 'angular', 'vue', 
            'nodejs', 'express', 'django', 'flask', 'spring', 'mysql', 'postgresql', 
            'mongodb', 'redis', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 
            'git', 'jenkins', 'terraform', 'ansible', 'agile', 'scrum', 'devops', 
            'rest', 'graphql', 'microservices', 'tdd', 'bdd', 'ci/cd', 'cicd'
        }
        
        # For technical skills, be very strict about context
        if skill in technical_skills:
            return self._is_technical_skill_in_context(text, skill)
        
        # For non-technical skills, be more lenient
        return self._is_general_skill_in_context(text, skill)
    
    def _is_technical_skill_in_context(self, text: str, skill: str) -> bool:
        """Strict validation for technical skills"""
        # Skip if skill appears in negative contexts
        negative_contexts = [
            r'no\s+experience\s+with\s+' + re.escape(skill) + r'\b',
            r'not\s+familiar\s+with\s+' + re.escape(skill) + r'\b',
            r'limited\s+knowledge\s+of\s+' + re.escape(skill) + r'\b',
            r'basic\s+understanding\s+of\s+' + re.escape(skill) + r'\b',
            r'never\s+used\s+' + re.escape(skill) + r'\b',
            r'no\s+exposure\s+to\s+' + re.escape(skill) + r'\b'
        ]
        
        for pattern in negative_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Look for strong positive contexts for technical skills
        strong_positive_contexts = [
            r'(?:expert|proficient|skilled|experienced)\s+(?:in\s+)?' + re.escape(skill) + r'\b',
            r'(?:strong|extensive|deep)\s+(?:knowledge|experience)\s+(?:in\s+)?' + re.escape(skill) + r'\b',
            r'(?:developed|built|created|implemented|programmed|coded)\s+(?:using\s+)?' + re.escape(skill) + r'\b',
            r'(?:worked\s+with|used|utilized|leveraged)\s+' + re.escape(skill) + r'\b',
            r'(?:programming\s+languages?|frameworks?|technologies?|tools?)[:\s]*[^.\n]*' + re.escape(skill) + r'\b',
            r'(?:technical\s+)?skills?[:\s]*[^.\n]*' + re.escape(skill) + r'\b'
        ]
        
        for pattern in strong_positive_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check if it's in a clear technical skills section
        technical_section_patterns = [
            r'(?:technical\s+)?skills?[:\s]*[^.\n]*' + re.escape(skill) + r'\b',
            r'programming\s+languages?[:\s]*[^.\n]*' + re.escape(skill) + r'\b',
            r'frameworks?[:\s]*[^.\n]*' + re.escape(skill) + r'\b',
            r'technologies?[:\s]*[^.\n]*' + re.escape(skill) + r'\b',
            r'tools?[:\s]*[^.\n]*' + re.escape(skill) + r'\b'
        ]
        
        for pattern in technical_section_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Default: be very conservative for technical skills
        return False
    
    def _is_general_skill_in_context(self, text: str, skill: str) -> bool:
        """More lenient validation for general skills"""
        # Skip if skill appears in negative contexts
        negative_contexts = [
            r'no\s+experience\s+with\s+' + re.escape(skill) + r'\b',
            r'not\s+familiar\s+with\s+' + re.escape(skill) + r'\b',
            r'limited\s+knowledge\s+of\s+' + re.escape(skill) + r'\b'
        ]
        
        for pattern in negative_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Look for positive contexts
        positive_contexts = [
            r'(?:expert|proficient|skilled|experienced)\s+(?:in\s+)?' + re.escape(skill) + r'\b',
            r'(?:strong|extensive|deep)\s+(?:knowledge|experience)\s+(?:in\s+)?' + re.escape(skill) + r'\b',
            r'(?:developed|built|created|implemented)\s+(?:using\s+)?' + re.escape(skill) + r'\b',
            r'(?:worked\s+with|used|utilized)\s+' + re.escape(skill) + r'\b',
            r'skills?[:\s]*[^.\n]*' + re.escape(skill) + r'\b'
        ]
        
        for pattern in positive_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # If skill appears in a skills section, it's likely valid
        skills_section_pattern = r'skills?[:\s]*[^.\n]*' + re.escape(skill) + r'\b'
        if re.search(skills_section_pattern, text, re.IGNORECASE):
            return True
        
        # Default: be more conservative
        return False
    
    def _normalize_skill(self, skill: str) -> Optional[str]:
        """Normalize a skill to its canonical form"""
        skill_lower = skill.lower().strip()
        return self.skill_mappings.get(skill_lower)
