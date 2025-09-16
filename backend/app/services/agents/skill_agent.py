"""
Enhanced Skill Matching Agent

This agent normalizes skills using both LLM-powered intelligent analysis
and traditional taxonomy mapping, compares JD required skills vs resume skills, 
and returns matched/missing skills with enhanced scoring.
"""

import json
import re
from typing import Dict, List, Any, Set, Optional
from pathlib import Path
from .base_agent import BaseAgent, AgentResult, AgentType
from app.services.llm_service import LLMServiceFactory
from app.core.config import settings


class SkillMatchingAgent(BaseAgent):
    """Enhanced agent for skill matching with LLM-powered normalization"""
    
    def __init__(self, weight: float = 0.25):
        super().__init__(AgentType.SKILL_MATCHING, weight)
        self.skill_taxonomy = self._load_skill_taxonomy()
        self.skill_mappings = self._build_skill_mappings()
        self.llm_service = None
        self.use_llm = getattr(settings, 'USE_LLM_FOR_SKILLS', True)
        self._initialize_llm_service()
    
    def _initialize_llm_service(self):
        """Initialize LLM service if available"""
        try:
            if self.use_llm and settings.is_llm_configured():
                self.llm_service = LLMServiceFactory.get_default_service()
                print(f"✅ LLM service initialized for Skill Matching Agent: {settings.LLM_PROVIDER}")
            else:
                print(f"⚠️ LLM service not available for Skill Matching Agent. Using rule-based approach.")
                self.use_llm = False
        except Exception as e:
            print(f"❌ Failed to initialize LLM service for Skill Matching Agent: {e}")
            self.use_llm = False
    
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
        """Analyze skill alignment between resume and job using enhanced methods"""
        try:
            resume_text = self._extract_text_content(resume)
            job_skills = [skill.lower() for skill in job.get('skills', [])]
            
            # Extract skills from resume using enhanced method
            resume_skills = await self._extract_skills_enhanced(resume_text)
            
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
            
            # Normalize skills using enhanced method
            resume_normalized = await self._normalize_skills_enhanced(resume_skills, "resume")
            job_normalized = await self._normalize_skills_enhanced(job_skills, "job_requirements")
            
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
                    "skill_coverage": skill_coverage,
                    "extraction_method": "llm_enhanced" if self.use_llm else "rule_based"
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
    
    async def _extract_skills_enhanced(self, text: str) -> List[str]:
        """Extract skills using LLM + rule-based hybrid approach"""
        try:
            if self.use_llm and self.llm_service:
                # Try LLM extraction first
                llm_skills = await self._extract_skills_with_llm(text)
                if llm_skills:
                    return llm_skills
            
            # Fallback to rule-based extraction
            return self._extract_skills(text)
            
        except Exception as e:
            print(f"Error in enhanced skill extraction: {e}")
            # Fallback to rule-based
            return self._extract_skills(text)
    
    async def _extract_skills_with_llm(self, text: str) -> Optional[List[str]]:
        """Extract skills using LLM with intelligent categorization"""
        try:
            prompt = self._create_skill_extraction_prompt(text)
            response = await self._call_llm_with_custom_prompt(prompt)
            return self._parse_skill_response(response)
        except Exception as e:
            print(f"LLM skill extraction failed: {e}")
            return None
    
    def _create_skill_extraction_prompt(self, text: str) -> str:
        """Create prompt for LLM skill extraction"""
        return f"""
        Analyze the following resume text and extract all technical and professional skills.
        Focus on programming languages, frameworks, tools, methodologies, and soft skills.
        
        Text: {text[:2000]}  # Limit text length
        
        Return ONLY a valid JSON object with this structure:
        {{
            "skills": [
                {{"skill": "Python", "category": "programming", "confidence": 0.9}},
                {{"skill": "React", "category": "framework", "confidence": 0.8}},
                {{"skill": "Project Management", "category": "soft_skill", "confidence": 0.7}}
            ]
        }}
        
        Rules:
        - Extract skills mentioned in the text
        - Categories: programming, framework, tool, database, cloud, methodology, soft_skill, certification
        - Confidence: 1.0 = explicitly mentioned, 0.8 = clearly implied, 0.6 = contextually suggested
        - Include both technical and soft skills
        - Return ONLY the JSON object, no additional text
        """
    
    async def _call_llm_with_custom_prompt(self, prompt: str) -> str:
        """Call LLM with custom prompt using the enhanced LLM service"""
        try:
            if self.llm_service and hasattr(self.llm_service, 'generate_completion'):
                response = await self.llm_service.generate_completion(prompt, temperature=0.1, max_tokens=1000)
                return response
            return None
        except Exception as e:
            print(f"Custom LLM call failed: {e}")
            return None
    
    def _parse_skill_response(self, response: str) -> Optional[List[str]]:
        """Parse LLM response for skills"""
        if not response:
            return None
            
        try:
            data = json.loads(response)
            skills = []
            for item in data.get("skills", []):
                skill = item.get("skill", "").strip()
                if skill:
                    skills.append(skill.lower())
            return skills
        except Exception as e:
            print(f"Failed to parse skill response: {e}")
            return None
    
    async def _normalize_skills_enhanced(self, skills: List[str], context: str) -> List[str]:
        """Normalize skills using LLM + rule-based hybrid approach"""
        try:
            if self.use_llm and self.llm_service:
                # Try LLM normalization first
                llm_normalized = await self._normalize_skills_with_llm(skills, context)
                if llm_normalized:
                    return llm_normalized
            
            # Fallback to rule-based normalization
            return [self._normalize_skill(skill) for skill in skills]
            
        except Exception as e:
            print(f"Error in enhanced skill normalization: {e}")
            # Fallback to rule-based
            return [self._normalize_skill(skill) for skill in skills]
    
    async def _normalize_skills_with_llm(self, skills: List[str], context: str) -> Optional[List[str]]:
        """Normalize skills using LLM with intelligent mapping"""
        try:
            prompt = self._create_skill_normalization_prompt(skills, context)
            response = await self._call_llm_with_custom_prompt(prompt)
            return self._parse_normalization_response(response)
        except Exception as e:
            print(f"LLM skill normalization failed: {e}")
            return None
    
    def _create_skill_normalization_prompt(self, skills: List[str], context: str) -> str:
        """Create prompt for LLM skill normalization"""
        skills_text = ", ".join(skills[:20])  # Limit to first 20 skills
        
        return f"""
        Normalize and standardize the following {context} skills to their canonical forms.
        Map variations, abbreviations, and related terms to standard skill names.
        
        Skills: {skills_text}
        
        Return ONLY a valid JSON object with this structure:
        {{
            "normalized_skills": [
                {{"original": "JS", "normalized": "JavaScript", "confidence": 0.9}},
                {{"original": "React.js", "normalized": "React", "confidence": 0.95}},
                {{"original": "AWS Cloud", "normalized": "AWS", "confidence": 0.8}}
            ]
        }}
        
        Rules:
        - Map abbreviations to full names (JS → JavaScript, ML → Machine Learning)
        - Standardize framework names (React.js → React, Node.js → Node.js)
        - Group related technologies (AWS Cloud → AWS, Google Cloud → GCP)
        - Keep original if no clear mapping exists
        - Confidence: 1.0 = exact match, 0.9 = clear abbreviation, 0.8 = related term
        - Return ONLY the JSON object, no additional text
        """
    
    def _parse_normalization_response(self, response: str) -> Optional[List[str]]:
        """Parse LLM response for normalized skills"""
        if not response:
            return None
            
        try:
            data = json.loads(response)
            normalized_skills = []
            for item in data.get("normalized_skills", []):
                normalized = item.get("normalized", "").strip()
                if normalized:
                    normalized_skills.append(normalized.lower())
            return normalized_skills
        except Exception as e:
            print(f"Failed to parse normalization response: {e}")
            return None
