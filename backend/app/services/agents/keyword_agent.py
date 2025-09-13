"""
Keyword Matching Agent

This agent extracts keywords from both resume and job description,
calculates overlap, and returns matched/missing keywords with score.
"""

import re
from typing import Dict, List, Any, Set
from .base_agent import BaseAgent, AgentResult, AgentType


class KeywordMatchingAgent(BaseAgent):
    """Agent for keyword matching between resume and job description"""
    
    def __init__(self, weight: float = 0.20):
        super().__init__(AgentType.KEYWORD_MATCHING, weight)
        self.technical_keywords = self._load_technical_keywords()
    
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
    
    async def analyze(self, resume: Dict[str, Any], job: Dict[str, Any]) -> AgentResult:
        """Analyze keyword overlap between resume and job"""
        try:
            resume_text = self._extract_text_content(resume).lower()
            job_text = self._extract_job_content(job).lower()
            
            # Extract keywords from both texts
            resume_keywords = self._extract_keywords(resume_text)
            job_keywords = self._extract_keywords(job_text)
            
            if not job_keywords:
                return self._create_result(
                    score=0.0,
                    evidence={
                        "resume_keywords": list(resume_keywords),
                        "job_keywords": [],
                        "matched_keywords": [],
                        "missing_keywords": [],
                        "total_job_keywords": 0,
                        "total_resume_keywords": len(resume_keywords)
                    },
                    confidence=0.0,
                    error="No keywords found in job description"
                )
            
            # Calculate overlap
            matched_keywords = resume_keywords & job_keywords
            missing_keywords = job_keywords - resume_keywords
            
            # Calculate score
            overlap_ratio = len(matched_keywords) / len(job_keywords)
            score = min(1.0, overlap_ratio)  # Cap at 1.0
            
            # Calculate confidence based on keyword density
            total_words_resume = len(resume_text.split())
            total_words_job = len(job_text.split())
            keyword_density_resume = len(resume_keywords) / max(total_words_resume, 1)
            keyword_density_job = len(job_keywords) / max(total_words_job, 1)
            confidence = min(1.0, (keyword_density_resume + keyword_density_job) / 2)
            
            return self._create_result(
                score=score,
                evidence={
                    "resume_keywords": list(resume_keywords),
                    "job_keywords": list(job_keywords),
                    "matched_keywords": list(matched_keywords),
                    "missing_keywords": list(missing_keywords),
                    "total_job_keywords": len(job_keywords),
                    "total_resume_keywords": len(resume_keywords),
                    "overlap_ratio": overlap_ratio,
                    "keyword_density_resume": keyword_density_resume,
                    "keyword_density_job": keyword_density_job
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
