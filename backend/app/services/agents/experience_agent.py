"""
Enhanced Experience Relevance Agent

This agent extracts years and seniority from resume and job description,
compares them, and returns structured score (meets/partial/underqualified).
Enhanced with LLM capabilities for better experience extraction and analysis.
"""

import re
import json
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent, AgentResult, AgentType
from app.services.llm_service import LLMServiceFactory
from app.core.config import settings


class ExperienceRelevanceAgent(BaseAgent):
    """Enhanced agent for experience relevance analysis with LLM capabilities and caching"""
    
    def __init__(self, weight: float = 0.20, use_cache: bool = True):
        super().__init__(AgentType.EXPERIENCE_RELEVANCE, weight, use_cache)
        self.llm_service = None
        self.use_llm = getattr(settings, 'USE_LLM_FOR_EXPERIENCE', True)
        self._initialize_llm_service()
    
    def get_meta_prompt(self):
        """Chain-of-thought meta prompt for experience extraction"""
        return (
            "Think step by step about what makes a good prompt for experience extraction:\n"
            "1. What information should it capture (years, seniority, employment type)?\n"
            "2. What edge cases (date ranges, part-time, freelance, ambiguous titles) should it handle?\n"
            "3. What output format is most useful?\n"
            "Now create a detailed prompt for extracting years of experience and seniority from a resume or job description."
        )

    def _initialize_llm_service(self):
        """Initialize LLM service if available"""
        try:
            if self.use_llm and settings.is_llm_configured():
                self.llm_service = LLMServiceFactory.get_default_service()
                print(f"✅ LLM service initialized for Experience Agent: {settings.LLM_PROVIDER}")
            else:
                print(f"⚠️ LLM service not available for Experience Agent. Using rule-based approach.")
                self.use_llm = False
        except Exception as e:
            print(f"❌ Failed to initialize LLM service for Experience Agent: {e}")
            self.use_llm = False
    
    async def _analyze_impl(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """Analyze experience relevance between resume and job using enhanced LLM methods"""
        try:
            resume_text = self._extract_text_content(resume)
            job_requirements = job.get('requirements', [])
            job_text = self._extract_job_content(job)
            
            # Extract experience using enhanced method (LLM + rule-based)
            resume_experience = await self._extract_experience_enhanced(resume_text, "resume")
            
            # Extract experience requirements using enhanced method
            job_experience = await self._extract_experience_requirements_enhanced(job_text, job_requirements)
            
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
        
        # Extract years of experience with enhanced patterns
        years_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*years?\s*(?:in|of)',
            r'(\d+)\+?\s*years?\s*(?:working|developing|building)',
            r'experience[:\s]*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:professional|relevant)',
            r'(\d+)\+?\s*years?\s*(?:marketing|business|management|industry)',
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:work|career)',
            r'with\s*(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)'
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
        
        # Extract years requirement with enhanced patterns
        years_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*years?\s*(?:in|of)',
            r'(\d+)\+?\s*years?\s*(?:working|developing|building)',
            r'experience[:\s]*(\d+)\+?\s*years?',
            r'minimum[:\s]*(\d+)\+?\s*years?',
            r'at\s*least[:\s]*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:marketing|business|management|industry)',
            r'(\d+)[-–](\d+)\s*years?\s*(?:of\s*)?(?:experience|exp|marketing|business)',  # Range like 4-6 years
            r'(\d+)\+?\s*years?\s*(?:relevant|professional|work)',
            r'minimum\s*of\s*(\d+)\+?\s*years?',
            r'require[ds]?\s*(\d+)\+?\s*years?'
        ]
        
        years_found = []
        for pattern in years_patterns:
            matches = re.findall(pattern, requirements_text)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        # Handle range patterns like "4-6 years" 
                        years = int(match[0])  # Take the minimum of the range
                    else:
                        years = int(match)
                    
                    if 0 <= years <= 50:  # Reasonable range
                        years_found.append(years)
                except (ValueError, IndexError):
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
        if job_years == 0 and resume_years == 0:
            # Both unclear - give moderate score based on level matching
            years_score = 0.5  # Neutral score when both are unclear
        elif job_years == 0:
            # Job requirement unclear but resume has experience - give moderate credit
            years_score = min(0.7, 0.3 + (resume_years * 0.05))  # Cap at 0.7
        elif resume_years == 0:
            # Resume unclear but job has requirement - penalize heavily
            years_score = 0.2  # Low score for unclear resume experience
        elif resume_years >= job_years:
            years_score = 1.0  # Meets or exceeds requirement
        else:
            # Partial credit for underqualified
            years_score = max(0.1, resume_years / job_years)  # Minimum 0.1 score
        
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

    async def _extract_experience_enhanced(self, text: str, source_type: str) -> Dict[str, Any]:
        """Extract experience using LLM + rule-based approach"""
        # Start with rule-based extraction as fallback
        rule_based_experience = self._extract_experience_indicators(text)
        
        # If LLM is available, enhance with LLM analysis
        if self.use_llm and self.llm_service:
            try:
                llm_experience = await self._extract_experience_with_llm(text, source_type)
                # Combine rule-based and LLM results, prioritizing LLM when available
                enhanced_experience = self._combine_experience_results(rule_based_experience, llm_experience)
                return enhanced_experience
            except Exception as e:
                print(f"⚠️ LLM experience extraction failed, using rule-based: {e}")
                return rule_based_experience
        
        return rule_based_experience

    async def _extract_experience_requirements_enhanced(self, job_text: str, requirements: List[str]) -> Dict[str, Any]:
        """Extract experience requirements using LLM + rule-based approach"""
        # Start with rule-based extraction as fallback
        rule_based_experience = self._extract_experience_requirements(requirements)
        
        # If LLM is available, enhance with LLM analysis
        if self.use_llm and self.llm_service:
            try:
                full_text = f"{job_text}\n\nRequirements: {' '.join(requirements)}"
                llm_experience = await self._extract_experience_with_llm(full_text, "job_requirements")
                # Combine rule-based and LLM results
                enhanced_experience = self._combine_experience_results(rule_based_experience, llm_experience)
                return enhanced_experience
            except Exception as e:
                print(f"⚠️ LLM experience requirements extraction failed, using rule-based: {e}")
                return rule_based_experience
        
        return rule_based_experience

    async def _extract_experience_with_llm(self, text: str, source_type: str) -> Dict[str, Any]:
        """Extract experience information using LLM"""
        prompt = f"""Analyze the following {source_type} text and extract work experience information.

Text: {text}

Please extract and return ONLY a valid JSON object with the following structure:
{{
    "years": "total years of relevant work experience (integer)",
    "level": "seniority level: junior, mid, senior, or lead",
    "positions": ["list of job titles/positions mentioned"],
    "companies": ["list of companies/organizations mentioned"],
    "technologies": ["relevant technologies/tools used"],
    "industries": ["relevant industries worked in"],
    "achievements": ["key accomplishments or responsibilities"],
    "leadership_experience": "boolean indicating management/leadership roles",
    "confidence": "float between 0.0-1.0 indicating extraction confidence"
}}

Focus on:
- Total years of professional experience
- Seniority level indicators (junior, mid-level, senior, lead, manager, director)
- Relevant work positions and companies
- Technical skills and tools used
- Leadership or management experience
- Requirements vs achievements (based on source_type)

For job requirements, focus on minimum required experience.
For resumes, focus on actual experience achieved.

Return only the JSON, no additional text."""

        try:
            response = await self.llm_service.generate_completion(prompt, temperature=0.1, max_tokens=1000)
            
            # Validate response is not empty
            if not response or not response.strip():
                print("⚠️ LLM returned empty response for experience extraction")
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
                experience_data = json.loads(json_content)
            else:
                # If no JSON found, try parsing the whole response
                experience_data = json.loads(cleaned_response)
            
            # Validate and normalize the response
            return self._validate_llm_experience_response(experience_data)
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse LLM experience response as JSON: {e}")
            print(f"Raw response: {response[:200]}...")  # Log first 200 chars for debugging
            return {}
        except Exception as e:
            error_str = str(e).lower()
            if "llm_quota_exceeded" in error_str or "quota exceeded" in error_str:
                print("⚠️ LLM quota exceeded for experience extraction. Using rule-based fallback.")
                return {}  # Return empty dict to use rule-based only
            print(f"⚠️ LLM experience extraction error: {e}")
            return {}

    def _combine_experience_results(self, rule_based: Dict[str, Any], llm_based: Dict[str, Any]) -> Dict[str, Any]:
        """Combine rule-based and LLM-based experience extraction results"""
        combined = rule_based.copy()
        
        # LLM results take priority if they exist and have confidence
        if llm_based and llm_based.get('confidence', 0) > 0.3:
            # Use LLM years if more specific or higher confidence
            if llm_based.get('years') is not None and llm_based.get('confidence', 0) > 0.5:
                combined['years'] = max(llm_based['years'], rule_based.get('years', 0))
            
            # Use LLM level if available and confident
            if llm_based.get('level') and llm_based.get('confidence', 0) > 0.4:
                combined['level'] = llm_based['level']
            
            # Add LLM-specific information
            for key in ['positions', 'companies', 'technologies', 'industries', 'achievements']:
                if llm_based.get(key):
                    combined[key] = llm_based[key]
            
            if llm_based.get('leadership_experience') is not None:
                combined['leadership_experience'] = llm_based['leadership_experience']
            
            # Set extraction method
            combined['extraction_method'] = 'llm_enhanced'
            combined['llm_confidence'] = llm_based.get('confidence', 0)
        else:
            combined['extraction_method'] = 'rule_based'
        
        return combined

    def _validate_llm_experience_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize LLM experience response"""
        validated = {}
        
        # Validate years
        if data.get('years') is not None:
            try:
                validated['years'] = int(data['years'])
            except (ValueError, TypeError):
                # Try to extract number from string
                years_str = str(data['years'])
                years_match = re.search(r'(\d+)', years_str)
                if years_match:
                    validated['years'] = int(years_match.group(1))
        
        # Validate level
        valid_levels = ['junior', 'mid', 'senior', 'lead']
        if data.get('level') and data['level'].lower() in valid_levels:
            validated['level'] = data['level'].lower()
        
        # Additional information
        for key in ['positions', 'companies', 'technologies', 'industries', 'achievements']:
            if data.get(key) and isinstance(data[key], list):
                validated[key] = data[key]
        
        if data.get('leadership_experience') is not None:
            validated['leadership_experience'] = bool(data['leadership_experience'])
        
        if data.get('confidence') is not None:
            try:
                validated['confidence'] = float(data['confidence'])
            except (ValueError, TypeError):
                validated['confidence'] = 0.5
        
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
        if job.get('skills'):
            content_parts.append(f"Skills: {', '.join(job['skills'])}")
        
        return '\n'.join(content_parts)
