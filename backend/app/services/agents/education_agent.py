"""
Enhanced Education Alignment Agent

This agent extracts degree level and field of study from resume and job,
compares them, and returns score (full/partial/underqualified).
Enhanced with LLM capabilities for better education extraction and analysis.
"""

import re
import json
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent, AgentResult, AgentType
from app.services.llm_service import LLMServiceFactory
from app.core.config import settings


class EducationAlignmentAgent(BaseAgent):
    """Enhanced agent for education alignment analysis with LLM capabilities and caching"""
    
    def __init__(self, weight: float = 0.10, use_cache: bool = True):
        super().__init__(AgentType.EDUCATION_ALIGNMENT, weight, use_cache)
        self.degree_levels = self._init_degree_levels()
        self.field_mappings = self._init_field_mappings()
        self.llm_service = None
        self.use_llm = getattr(settings, 'USE_LLM_FOR_EDUCATION', True)
        self._initialize_llm_service()
    
    def get_meta_prompt(self):
        """Chain-of-thought meta prompt for education extraction"""
        return (
            "Think step by step about what makes a good prompt for education extraction:\n"
            "1. What information should it capture (degree level, field of study, related fields)?\n"
            "2. What edge cases (synonyms, ambiguous names, multiple degrees) should it handle?\n"
            "3. What output format is most useful?\n"
            "Now create a detailed prompt for extracting degree level and field of study from a resume or job description."
        )

    def _initialize_llm_service(self):
        """Initialize LLM service if available"""
        try:
            if self.use_llm and settings.is_llm_configured():
                self.llm_service = LLMServiceFactory.get_default_service()
                print(f"✅ LLM service initialized for Education Agent: {settings.LLM_PROVIDER}")
            else:
                print(f"⚠️ LLM service not available for Education Agent. Using rule-based approach.")
                self.use_llm = False
        except Exception as e:
            print(f"❌ Failed to initialize LLM service for Education Agent: {e}")
            self.use_llm = False
    
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
    
    async def _analyze_impl(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """Analyze education alignment between resume and job using enhanced LLM methods"""
        try:
            resume_text = self._extract_text_content(resume)
            job_requirements = job.get('requirements', [])
            job_text = self._extract_job_content(job)
            
            # Extract education using enhanced method (LLM + rule-based)
            resume_education = await self._extract_education_enhanced(resume_text, "resume")
            
            # Extract education requirements using enhanced method
            job_education = await self._extract_education_requirements_enhanced(job_text, job_requirements)
            
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

    async def _extract_education_enhanced(self, text: str, source_type: str) -> Dict[str, Any]:
        """Extract education using LLM + rule-based approach"""
        # Start with rule-based extraction as fallback
        rule_based_education = self._extract_education(text)
        
        # If LLM is available, enhance with LLM analysis
        if self.use_llm and self.llm_service:
            try:
                llm_education = await self._extract_education_with_llm(text, source_type)
                # Combine rule-based and LLM results, prioritizing LLM when available
                enhanced_education = self._combine_education_results(rule_based_education, llm_education)
                return enhanced_education
            except Exception as e:
                print(f"⚠️ LLM education extraction failed, using rule-based: {e}")
                return rule_based_education
        
        return rule_based_education

    async def _extract_education_requirements_enhanced(self, job_text: str, requirements: List[str]) -> Dict[str, Any]:
        """Extract education requirements using LLM + rule-based approach"""
        # Start with rule-based extraction as fallback
        rule_based_education = self._extract_education_requirements(requirements)
        
        # If LLM is available, enhance with LLM analysis
        if self.use_llm and self.llm_service:
            try:
                full_text = f"{job_text}\n\nRequirements: {' '.join(requirements)}"
                llm_education = await self._extract_education_with_llm(full_text, "job_requirements")
                # Combine rule-based and LLM results
                enhanced_education = self._combine_education_results(rule_based_education, llm_education)
                return enhanced_education
            except Exception as e:
                print(f"⚠️ LLM education requirements extraction failed, using rule-based: {e}")
                return rule_based_education
        
        return rule_based_education

    async def _extract_education_with_llm(self, text: str, source_type: str) -> Dict[str, Any]:
        """Extract education information using LLM"""
        prompt = f"""Analyze the following {source_type} text and extract education information.

Text: {text}

Please extract and return ONLY a valid JSON object with the following structure:
{{
    "degree_level": "one of: phd, masters, bachelors, associate, high_school, or null",
    "level": "numeric value: 4=phd, 3=masters, 2=bachelors, 1=associate, 0=high_school",
    "field": "main field of study (e.g., computer_science, engineering, business)",
    "specific_degree": "specific degree name if mentioned (e.g., Bachelor of Science in Computer Science)",
    "institutions": ["list of educational institutions mentioned"],
    "certifications": ["relevant certifications or professional qualifications"],
    "confidence": "float between 0.0-1.0 indicating extraction confidence"
}}

Focus on:
- Highest degree level mentioned
- Primary field of study
- Professional certifications
- Educational institutions
- Requirements vs achievements (based on source_type)

Return only the JSON, no additional text."""

        try:
            response = await self.llm_service.generate_completion(prompt, temperature=0.1, max_tokens=800)
            
            # Validate response is not empty
            if not response or not response.strip():
                print("⚠️ LLM returned empty response for education extraction")
                return {}
            
            # Clean the response - remove any markdown formatting
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Try to find JSON in the response
            json_start = cleaned_response.find('{')
            json_end = cleaned_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = cleaned_response[json_start:json_end]
                education_data = json.loads(json_content)
            else:
                # If no JSON found, try parsing the whole response
                education_data = json.loads(cleaned_response)
            
            # Validate and normalize the response
            return self._validate_llm_education_response(education_data)
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse LLM education response as JSON: {e}")
            print(f"Raw response: {response[:200]}...")  # Log first 200 chars for debugging
            return {}
        except Exception as e:
            error_str = str(e).lower()
            if "llm_quota_exceeded" in error_str or "quota exceeded" in error_str:
                print("⚠️ LLM quota exceeded for education extraction. Using rule-based fallback.")
                return {}  # Return empty dict to use rule-based only
            print(f"⚠️ LLM education extraction error: {e}")
            return {}

    def _combine_education_results(self, rule_based: Dict[str, Any], llm_based: Dict[str, Any]) -> Dict[str, Any]:
        """Combine rule-based and LLM-based education extraction results"""
        combined = rule_based.copy()
        
        # LLM results take priority if they exist and have confidence
        if llm_based and llm_based.get('confidence', 0) > 0.3:
            # Use LLM degree level if more specific or higher confidence
            if llm_based.get('degree_level') and llm_based.get('confidence', 0) > 0.5:
                combined['degree_level'] = llm_based['degree_level']
                combined['level'] = llm_based.get('level', self.degree_levels.get(llm_based['degree_level'], 0))
            
            # Use LLM field if available and confident
            if llm_based.get('field') and llm_based.get('confidence', 0) > 0.4:
                combined['field'] = llm_based['field']
            
            # Add LLM-specific information
            if llm_based.get('specific_degree'):
                combined['specific_degree'] = llm_based['specific_degree']
            
            if llm_based.get('institutions'):
                combined['institutions'] = llm_based['institutions']
            
            if llm_based.get('certifications'):
                combined['certifications'] = llm_based['certifications']
            
            # Set extraction method
            combined['extraction_method'] = 'llm_enhanced'
            combined['llm_confidence'] = llm_based.get('confidence', 0)
        else:
            combined['extraction_method'] = 'rule_based'
        
        return combined

    def _validate_llm_education_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize LLM education response"""
        validated = {}
        
        # Validate degree level
        if data.get('degree_level') in self.degree_levels:
            validated['degree_level'] = data['degree_level']
            validated['level'] = self.degree_levels[data['degree_level']]
        elif data.get('level') is not None:
            # Try to map numeric level back to degree level
            level_mapping = {v: k for k, v in self.degree_levels.items()}
            if data['level'] in level_mapping:
                validated['degree_level'] = level_mapping[data['level']]
                validated['level'] = data['level']
        
        # Validate field
        if data.get('field') and isinstance(data['field'], str):
            validated['field'] = data['field'].lower().replace(' ', '_')
        
        # Additional information
        for key in ['specific_degree', 'institutions', 'certifications', 'confidence']:
            if data.get(key) is not None:
                validated[key] = data[key]
        
        return validated

    def _extract_job_content(self, job: Dict[str, Any]) -> str:
        """Extract full job content for LLM analysis"""
        content_parts = []
        
        if job.get('title'):
            content_parts.append(f"Title: {job['title']}")
        if job.get('description'):
            content_parts.append(f"Description: {job['description']}")
        if job.get('requirements'):
            content_parts.append(f"Requirements: {' '.join(job['requirements'])}")
        if job.get('experience_level'):
            content_parts.append(f"Experience Level: {job['experience_level']}")
        
        return '\n'.join(content_parts)
