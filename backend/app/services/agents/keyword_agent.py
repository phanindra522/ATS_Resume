"""
Enhanced Keyword Matching Agent

This agent extracts keywords from both resume and job description using
both rule-based and LLM-powered approaches, calculates overlap, and 
returns matched/missing keywords with score.
"""

import re
import json
from typing import Dict, List, Any, Set, Optional
from .base_agent import BaseAgent, AgentResult, AgentType
from app.services.llm_service import LLMServiceFactory
from app.core.config import settings


class KeywordMatchingAgent(BaseAgent):
    """Enhanced agent for keyword matching with LLM capabilities and caching"""
    
    def __init__(self, weight: float = 0.20, use_cache: bool = True):
        super().__init__(AgentType.KEYWORD_MATCHING, weight, use_cache)
        self.technical_keywords = self._load_technical_keywords()
        self.llm_service = None
        self.use_llm = getattr(settings, 'USE_LLM_FOR_KEYWORDS', True)
        self._initialize_llm_service()
    
    def get_meta_prompt(self):
        """Chain-of-thought meta prompt for keyword extraction"""
        return (
            "Think step by step about what makes a good prompt for keyword extraction:\n"
            "1. What types of keywords should be captured (technical, business, soft skills)?\n"
            "2. What edge cases (synonyms, abbreviations, irrelevant words) should be handled?\n"
            "3. What output format is most useful?\n"
            "Now create a detailed prompt for extracting keywords from a resume or job description."
        )

    def _initialize_llm_service(self):
        """Initialize LLM service if available"""
        try:
            if self.use_llm and settings.is_llm_configured():
                self.llm_service = LLMServiceFactory.get_default_service()
                print(f"✅ LLM service initialized for Keyword Matching Agent: {settings.LLM_PROVIDER}")
            else:
                print(f"⚠️ LLM service not available for Keyword Matching Agent. Using rule-based approach.")
                self.use_llm = False
        except Exception as e:
            print(f"❌ Failed to initialize LLM service for Keyword Matching Agent: {e}")
            self.use_llm = False
    
    def _load_technical_keywords(self) -> Set[str]:
        """Load comprehensive technical keywords"""
        return {
            # Programming Languages
            'javascript', 'typescript', 'python', 'java', 'c#', '.net', 'php', 'ruby', 
            'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'c++', 'c',
            
            # Web Frameworks
            'react', 'angular', 'vue', 'nodejs', 'node.js', 'express', 'django', 'flask', 
            'fastapi', 'spring', 'springboot', 'laravel', 'rails', 'asp.net', 'next.js',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'sql server',
            'cassandra', 'elasticsearch', 'dynamodb', 'firebase',
            
            # Cloud Platforms
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digital ocean', 'linode',
            
            # DevOps & Tools
            'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'terraform',
            'ansible', 'ci/cd', 'cicd', 'devops', 'agile', 'scrum', 'kanban',
            
            # Testing
            'tdd', 'bdd', 'test driven', 'unit testing', 'integration testing',
            'selenium', 'jest', 'pytest', 'junit',
            
            # APIs & Protocols
            'rest', 'graphql', 'api', 'microservices', 'micro services', 'soap',
            
            # Data & Analytics
            'data science', 'machine learning', 'ai', 'artificial intelligence',
            'deep learning', 'nlp', 'computer vision', 'pandas', 'numpy', 'tensorflow',
            'pytorch', 'scikit-learn', 'spark', 'hadoop',
            
            # Business & Soft Skills
            'leadership', 'management', 'communication', 'teamwork', 'collaboration',
            'project management', 'agile', 'scrum', 'product management', 'strategy',
            'analytics', 'business intelligence', 'reporting', 'presentation'
        }
    
    async def _analyze_impl(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """Analyze keyword overlap between resume and job using enhanced methods"""
        try:
            resume_text = self._extract_text_content(resume)
            job_text = self._extract_job_content(job)
            
            # Extract keywords using enhanced method (LLM + rule-based)
            resume_keywords = await self._extract_keywords_enhanced(resume_text, "resume")
            job_keywords = await self._extract_keywords_enhanced(job_text, "job_description")
            
            if not job_keywords:
                return self._create_result(
                    score=0.0,
                    evidence={
                        "resume_keywords": self._format_keywords_for_evidence(resume_keywords),
                        "job_keywords": [],
                        "matched_keywords": [],
                        "missing_keywords": [],
                        "total_job_keywords": 0,
                        "total_resume_keywords": len(resume_keywords),
                        "extraction_method": "llm_enhanced" if self.use_llm else "rule_based"
                    },
                    confidence=0.0,
                    error="No keywords found in job description"
                )
            
            # Calculate overlap with importance weighting
            matched_keywords, missing_keywords, weighted_score = self._calculate_enhanced_overlap(
                resume_keywords, job_keywords
            )
            
            # Calculate confidence based on extraction quality and keyword density
            confidence = self._calculate_enhanced_confidence(resume_keywords, job_keywords, resume_text, job_text)
            
            return self._create_result(
                score=weighted_score,
                evidence={
                    "resume_keywords": self._format_keywords_for_evidence(resume_keywords),
                    "job_keywords": self._format_keywords_for_evidence(job_keywords),
                    "matched_keywords": self._format_keywords_for_evidence(matched_keywords),
                    "missing_keywords": self._format_keywords_for_evidence(missing_keywords),
                    "total_job_keywords": len(job_keywords),
                    "total_resume_keywords": len(resume_keywords),
                    "weighted_score": weighted_score,
                    "extraction_method": "llm_enhanced" if self.use_llm else "rule_based",
                    "keyword_density_resume": len(resume_keywords) / max(len(resume_text.split()), 1),
                    "keyword_density_job": len(job_keywords) / max(len(job_text.split()), 1)
                },
                confidence=confidence
            )
            
        except Exception as e:
            return self._create_result(
                score=0.0,
                evidence={},
                confidence=0.0,
                error=f"Error in keyword analysis: {str(e)}"
            )
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract relevant keywords from text"""
        found_keywords = set()
        
        # Direct keyword matching with word boundaries
        for keyword in self.technical_keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_keywords.add(keyword.lower())
        
        # Additional pattern-based extraction for compound terms
        compound_patterns = [
            r'\b(?:machine learning|deep learning|artificial intelligence)\b',
            r'\b(?:data science|business intelligence)\b',
            r'\b(?:project management|product management)\b',
            r'\b(?:unit testing|integration testing)\b',
            r'\b(?:ci/cd|cicd|continuous integration)\b'
        ]
        
        for pattern in compound_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                found_keywords.add(match.lower())
        
        return found_keywords
    
    async def _extract_keywords_enhanced(self, text: str, context: str) -> Dict[str, float]:
        """Extract keywords using LLM + rule-based hybrid approach"""
        try:
            if self.use_llm and self.llm_service:
                # Try LLM extraction first
                llm_keywords = await self._extract_keywords_with_llm(text, context)
                if llm_keywords:
                    return llm_keywords
            
            # Fallback to rule-based extraction
            rule_based_keywords = self._extract_keywords(text.lower())
            # Convert to weighted format (all keywords get equal weight)
            return {keyword: 1.0 for keyword in rule_based_keywords}
            
        except Exception as e:
            print(f"Error in enhanced keyword extraction: {e}")
            # Fallback to rule-based
            rule_based_keywords = self._extract_keywords(text.lower())
            return {keyword: 1.0 for keyword in rule_based_keywords}
    
    async def _extract_keywords_with_llm(self, text: str, context: str) -> Optional[Dict[str, float]]:
        """Extract keywords using LLM with importance scoring"""
        try:
            prompt = self._create_keyword_extraction_prompt(text, context)
            
            # Use the existing LLM service but with a custom prompt
            if hasattr(self.llm_service, 'parse_job_description'):
                # We'll need to extend the LLM service to support custom prompts
                # For now, let's use a workaround
                response = await self._call_llm_with_custom_prompt(prompt)
                return self._parse_keyword_response(response)
            
            return None
            
        except Exception as e:
            print(f"LLM keyword extraction failed: {e}")
            return None
    
    def _create_keyword_extraction_prompt(self, text: str, context: str) -> str:
        """Create prompt for LLM keyword extraction"""
        return f"""
        Analyze the following {context} text and extract relevant technical keywords.
        For each keyword, provide an importance score (0.0-1.0) based on relevance to the role.
        
        Text: {text[:2000]}  # Limit text length
        
        Return ONLY a valid JSON object with this structure:
        {{
            "keywords": [
                {{"term": "keyword", "importance": 0.8, "category": "programming"}},
                {{"term": "framework", "importance": 0.9, "category": "web"}}
            ]
        }}
        
        Rules:
        - Extract technical skills, tools, frameworks, languages, methodologies
        - Importance: 1.0 = critical, 0.8 = important, 0.6 = nice-to-have, 0.4 = mentioned
        - Categories: programming, framework, tool, database, cloud, methodology, soft_skill
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
            error_str = str(e).lower()
            if "llm_quota_exceeded" in error_str or "quota exceeded" in error_str:
                print("Custom LLM call failed: Quota exceeded. Using rule-based extraction.")
            else:
                print(f"Custom LLM call failed: {e}")
            return None
    
    def _parse_keyword_response(self, response: str) -> Optional[Dict[str, float]]:
        """Parse LLM response for keywords"""
        if not response or not response.strip():
            print("⚠️ LLM returned empty response for keyword extraction")
            return None
            
        try:
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
                data = json.loads(json_content)
            else:
                # If no JSON found, try parsing the whole response
                data = json.loads(cleaned_response)
            
            keywords = {}
            for item in data.get("keywords", []):
                term = item.get("term", "").lower().strip()
                importance = float(item.get("importance", 0.5))
                if term:
                    keywords[term] = importance
            return keywords
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse LLM keyword response as JSON: {e}")
            print(f"Raw response: {response[:200]}...")  # Log first 200 chars for debugging
            return None
        except Exception as e:
            print(f"Failed to parse keyword response: {e}")
            return None
    
    def _calculate_enhanced_overlap(self, resume_keywords: Dict[str, float], job_keywords: Dict[str, float]) -> tuple:
        """Calculate overlap with importance weighting"""
        matched_keywords = {}
        missing_keywords = {}
        
        # Find matches
        for job_keyword, job_importance in job_keywords.items():
            if job_keyword in resume_keywords:
                # Use the higher importance score
                matched_importance = max(job_importance, resume_keywords[job_keyword])
                matched_keywords[job_keyword] = matched_importance
            else:
                missing_keywords[job_keyword] = job_importance
        
        # Calculate weighted score
        if not job_keywords:
            return matched_keywords, missing_keywords, 0.0
        
        total_importance = sum(job_keywords.values())
        matched_importance = sum(matched_keywords.values())
        weighted_score = matched_importance / total_importance if total_importance > 0 else 0.0
        
        return matched_keywords, missing_keywords, min(1.0, weighted_score)
    
    def _calculate_enhanced_confidence(self, resume_keywords: Dict[str, float], job_keywords: Dict[str, float], 
                                     resume_text: str, job_text: str) -> float:
        """Calculate confidence based on extraction quality"""
        base_confidence = 0.5
        
        # Boost confidence if using LLM
        if self.use_llm:
            base_confidence += 0.2
        
        # Boost confidence based on keyword density
        resume_density = len(resume_keywords) / max(len(resume_text.split()), 1)
        job_density = len(job_keywords) / max(len(job_text.split()), 1)
        density_boost = min(0.3, (resume_density + job_density) / 2)
        
        # Boost confidence based on importance variance (indicates quality extraction)
        if job_keywords:
            importances = list(job_keywords.values())
            variance = max(importances) - min(importances) if len(importances) > 1 else 0
            variance_boost = min(0.2, variance)
        else:
            variance_boost = 0
        
        return min(1.0, base_confidence + density_boost + variance_boost)
    
    def _format_keywords_for_evidence(self, keywords: Dict[str, float]) -> List[Dict[str, Any]]:
        """Format keywords for evidence display"""
        if isinstance(keywords, dict):
            return [{"term": term, "importance": importance} for term, importance in keywords.items()]
        else:
            # Handle legacy format (set of strings)
            return [{"term": keyword, "importance": 1.0} for keyword in keywords]
