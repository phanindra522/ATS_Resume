"""
Advanced Resume Scoring Service

This module provides sophisticated resume scoring capabilities using multiple factors:
- Keyword matching with taxonomy-based skill extraction
- Skills alignment with LLM-based normalization
- Experience relevance with intelligent parsing
- Education alignment with degree level mapping
- Semantic similarity using embeddings
"""

import json
import re
import os
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.routers.resumes import generate_embedding


@dataclass
class ScoringBreakdown:
    """Structured scoring breakdown"""
    keyword_match: Dict[str, Any]
    skills_alignment: Dict[str, Any]
    experience_relevance: Dict[str, Any]
    education_alignment: Dict[str, Any]
    semantic_similarity: Dict[str, Any]
    total_score: float
    match_percentage: float
    skills_match: List[str]
    missing_skills: List[str]


class SkillTaxonomy:
    """Skill taxonomy manager for intelligent skill matching"""
    
    def __init__(self):
        self.taxonomy = self._load_taxonomy()
        self.skill_mappings = self._build_skill_mappings()
    
    def _load_taxonomy(self) -> Dict:
        """Load skill taxonomy from JSON file"""
        taxonomy_path = Path(__file__).parent / "skill_taxonomy.json"
        try:
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Skill taxonomy file not found at {taxonomy_path}")
            return {}
    
    def _build_skill_mappings(self) -> Dict[str, str]:
        """Build reverse mapping from variations to canonical skill names"""
        mappings = {}
        for category, skills in self.taxonomy.items():
            for canonical, variations in skills.items():
                for variation in variations:
                    mappings[variation.lower()] = canonical
        return mappings
    
    def normalize_skill(self, skill: str) -> Optional[str]:
        """Normalize a skill to its canonical form"""
        skill_lower = skill.lower().strip()
        return self.skill_mappings.get(skill_lower)
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract and normalize skills from text with context awareness"""
        text_lower = text.lower()
        found_skills = set()
        
        # Context-aware skill extraction patterns
        # Look for skills in specific contexts that indicate actual skill possession
        
        # 1. Skills section patterns
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
                # Extract skills from the skills section
                skills_in_section = self._extract_skills_from_section(match)
                found_skills.update(skills_in_section)
        
        # 2. Experience-based skill extraction (more reliable)
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
        
        # 3. Direct skill mentions with context validation (using word boundaries)
        for variation, canonical in self.skill_mappings.items():
            if self._is_skill_in_context_with_boundaries(text_lower, variation):
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
            if len(candidate) < 2 or len(candidate) > 50:  # Reasonable skill name length
                continue
                
            # Check if it matches any known skill
            normalized = self.normalize_skill(candidate)
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
            r'no\s+experience\s+with\s+' + re.escape(skill),
            r'not\s+familiar\s+with\s+' + re.escape(skill),
            r'limited\s+knowledge\s+of\s+' + re.escape(skill),
            r'basic\s+understanding\s+of\s+' + re.escape(skill),
            r'never\s+used\s+' + re.escape(skill),
            r'no\s+exposure\s+to\s+' + re.escape(skill)
        ]
        
        for pattern in negative_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Look for strong positive contexts for technical skills
        strong_positive_contexts = [
            r'(?:expert|proficient|skilled|experienced)\s+(?:in\s+)?' + re.escape(skill),
            r'(?:strong|extensive|deep)\s+(?:knowledge|experience)\s+(?:in\s+)?' + re.escape(skill),
            r'(?:developed|built|created|implemented|programmed|coded)\s+(?:using\s+)?' + re.escape(skill),
            r'(?:worked\s+with|used|utilized|leveraged)\s+' + re.escape(skill),
            r'(?:programming\s+languages?|frameworks?|technologies?|tools?)[:\s]*[^.\n]*' + re.escape(skill),
            r'(?:technical\s+)?skills?[:\s]*[^.\n]*' + re.escape(skill)
        ]
        
        for pattern in strong_positive_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check if it's in a clear technical skills section
        technical_section_patterns = [
            r'(?:technical\s+)?skills?[:\s]*[^.\n]*' + re.escape(skill),
            r'programming\s+languages?[:\s]*[^.\n]*' + re.escape(skill),
            r'frameworks?[:\s]*[^.\n]*' + re.escape(skill),
            r'technologies?[:\s]*[^.\n]*' + re.escape(skill),
            r'tools?[:\s]*[^.\n]*' + re.escape(skill)
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
            r'no\s+experience\s+with\s+' + re.escape(skill),
            r'not\s+familiar\s+with\s+' + re.escape(skill),
            r'limited\s+knowledge\s+of\s+' + re.escape(skill)
        ]
        
        for pattern in negative_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Look for positive contexts
        positive_contexts = [
            r'(?:expert|proficient|skilled|experienced)\s+(?:in\s+)?' + re.escape(skill),
            r'(?:strong|extensive|deep)\s+(?:knowledge|experience)\s+(?:in\s+)?' + re.escape(skill),
            r'(?:developed|built|created|implemented)\s+(?:using\s+)?' + re.escape(skill),
            r'(?:worked\s+with|used|utilized)\s+' + re.escape(skill),
            r'skills?[:\s]*[^.\n]*' + re.escape(skill)
        ]
        
        for pattern in positive_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # If skill appears in a skills section, it's likely valid
        skills_section_pattern = r'skills?[:\s]*[^.\n]*' + re.escape(skill)
        if re.search(skills_section_pattern, text, re.IGNORECASE):
            return True
        
        # Default: be more conservative
        return False
    
    def _is_skill_in_context_with_boundaries(self, text: str, skill: str) -> bool:
        """Check if a skill appears in a meaningful context with word boundaries"""
        # Define technical skills that should be more strictly validated
        technical_skills = {
            'javascript', 'typescript', 'python', 'java', 'react', 'angular', 'vue', 
            'nodejs', 'express', 'django', 'flask', 'spring', 'mysql', 'postgresql', 
            'mongodb', 'redis', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 
            'git', 'jenkins', 'terraform', 'ansible', 'agile', 'scrum', 'devops', 
            'rest', 'graphql', 'microservices', 'tdd', 'bdd', 'ci/cd', 'cicd'
        }
        
        # For technical skills, be very strict about context and word boundaries
        if skill in technical_skills:
            return self._is_technical_skill_in_context_with_boundaries(text, skill)
        
        # For non-technical skills, be more lenient but still use boundaries
        return self._is_general_skill_in_context_with_boundaries(text, skill)
    
    def _is_technical_skill_in_context_with_boundaries(self, text: str, skill: str) -> bool:
        """Strict validation for technical skills with word boundaries"""
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
        
        # Look for strong positive contexts for technical skills with word boundaries
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
        
        # Check if it's in a clear technical skills section with word boundaries
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
    
    def _is_general_skill_in_context_with_boundaries(self, text: str, skill: str) -> bool:
        """More lenient validation for general skills with word boundaries"""
        # Skip if skill appears in negative contexts
        negative_contexts = [
            r'no\s+experience\s+with\s+' + re.escape(skill) + r'\b',
            r'not\s+familiar\s+with\s+' + re.escape(skill) + r'\b',
            r'limited\s+knowledge\s+of\s+' + re.escape(skill) + r'\b'
        ]
        
        for pattern in negative_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Look for positive contexts with word boundaries
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
        
        # If skill appears in a skills section with word boundaries, it's likely valid
        skills_section_pattern = r'skills?[:\s]*[^.\n]*' + re.escape(skill) + r'\b'
        if re.search(skills_section_pattern, text, re.IGNORECASE):
            return True
        
        # Default: be more conservative
        return False


class ExperienceParser:
    """Intelligent experience parsing and matching"""
    
    @staticmethod
    def extract_experience_indicators(text: str) -> Dict[str, Any]:
        """Extract experience indicators from resume text"""
        text_lower = text.lower()
        indicators = {}
        
        # Extract years of experience
        years_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*years?\s*(?:in\s*)?(?:development|programming|coding)',
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:professional|work)',
            r'experience[:\s]*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:total|combined)'
        ]
        
        for pattern in years_patterns:
            match = re.search(pattern, text_lower)
            if match:
                indicators['years'] = int(match.group(1))
                break
        
        # Extract role level
        seniority_keywords = {
            'senior': ['senior', 'sr.', 'lead', 'principal', 'architect', 'staff'],
            'mid': ['mid', 'intermediate', 'experienced', 'level 2', 'l2'],
            'junior': ['junior', 'jr.', 'entry', 'graduate', 'associate', 'level 1', 'l1']
        }
        
        for level, keywords in seniority_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                indicators['level'] = level
                break
        
        if 'level' not in indicators:
            # Default based on years if available
            if 'years' in indicators:
                years = indicators['years']
                if years >= 5:
                    indicators['level'] = 'senior'
                elif years >= 2:
                    indicators['level'] = 'mid'
                else:
                    indicators['level'] = 'junior'
            else:
                indicators['level'] = 'mid'  # Default assumption
        
        return indicators
    
    @staticmethod
    def extract_experience_requirements(job_requirements: List[str]) -> Dict[str, Any]:
        """Extract experience requirements from job description"""
        text = ' '.join(job_requirements).lower()
        requirements = {}
        
        # Extract years requirement
        years_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*years?\s*(?:in\s*)?(?:development|programming)',
            r'minimum[:\s]*(\d+)\+?\s*years?',
            r'at least[:\s]*(\d+)\+?\s*years?'
        ]
        
        for pattern in years_patterns:
            match = re.search(pattern, text)
            if match:
                requirements['years'] = int(match.group(1))
                break
        
        # Extract role level requirement
        seniority_keywords = {
            'senior': ['senior', 'sr.', 'lead', 'principal', 'architect', 'staff'],
            'mid': ['mid', 'intermediate', 'experienced', 'level 2', 'l2'],
            'junior': ['junior', 'jr.', 'entry', 'graduate', 'associate', 'level 1', 'l1']
        }
        
        for level, keywords in seniority_keywords.items():
            if any(keyword in text for keyword in keywords):
                requirements['level'] = level
                break
        
        if 'level' not in requirements:
            # Default based on years if available
            if 'years' in requirements:
                years = requirements['years']
                if years >= 5:
                    requirements['level'] = 'senior'
                elif years >= 2:
                    requirements['level'] = 'mid'
                else:
                    requirements['level'] = 'junior'
            else:
                requirements['level'] = 'mid'  # Default assumption
        
        return requirements


class EducationParser:
    """Education parsing and matching"""
    
    @staticmethod
    def extract_education(text: str) -> Dict[str, Any]:
        """Extract education information from resume text"""
        text_lower = text.lower()
        education = {}
        
        # Extract degree level
        degree_patterns = {
            'phd': ['phd', 'ph.d.', 'doctorate', 'doctoral', 'd.phil'],
            'masters': ['master', 'mba', 'ms', 'ma', 'm.s.', 'm.a.', 'masters', 'm.sc', 'm.eng'],
            'bachelors': ['bachelor', 'bs', 'ba', 'b.s.', 'b.a.', 'bachelor\'s', 'b.tech', 'b.eng', 'b.sc']
        }
        
        for level, patterns in degree_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                education['degree_level'] = level
                break
        
        if 'degree_level' not in education:
            education['degree_level'] = 'bachelors'  # Default assumption
        
        # Extract field of study
        field_patterns = [
            r'(?:bachelor|master|phd|bs|ba|ms|ma|mba).*?(?:in|of)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'degree[:\s]*(?:in|of)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'studied[:\s]*(?:in|at)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)'
        ]
        
        for pattern in field_patterns:
            match = re.search(pattern, text_lower)
            if match:
                field = match.group(1).strip()
                if len(field) > 2 and len(field) < 50:  # Reasonable field length
                    education['field'] = field
                    break
        
        return education
    
    @staticmethod
    def extract_education_requirements(job_requirements: List[str]) -> Dict[str, Any]:
        """Extract education requirements from job description"""
        text = ' '.join(job_requirements).lower()
        requirements = {}
        
        # Extract degree level requirement
        degree_patterns = {
            'phd': ['phd', 'ph.d.', 'doctorate', 'doctoral'],
            'masters': ['master', 'mba', 'ms', 'ma', 'm.s.', 'm.a.', 'masters'],
            'bachelors': ['bachelor', 'bs', 'ba', 'b.s.', 'b.a.', 'bachelor\'s']
        }
        
        for level, patterns in degree_patterns.items():
            if any(pattern in text for pattern in patterns):
                requirements['degree_level'] = level
                break
        
        if 'degree_level' not in requirements:
            requirements['degree_level'] = 'bachelors'  # Default assumption
        
        # Extract field requirement
        field_patterns = [
            r'(?:bachelor|master|phd|bs|ba|ms|ma|mba).*?(?:in|of)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)',
            r'degree[:\s]*(?:in|of)\s+([a-zA-Z\s]+?)(?:\s|,|\.|$)'
        ]
        
        for pattern in field_patterns:
            match = re.search(pattern, text)
            if match:
                field = match.group(1).strip()
                if len(field) > 2 and len(field) < 50:
                    requirements['field'] = field
                    break
        
        return requirements


class SemanticSimilarityCalculator:
    """Calculate semantic similarity using embeddings"""
    
    @staticmethod
    def calculate_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Normalize vectors
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    @staticmethod
    def generate_embeddings(text: str) -> Optional[np.ndarray]:
        """Generate embeddings for text"""
        try:
            embedding = generate_embedding(text)
            if embedding is not None:
                return np.array(embedding)
            return None
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return None


class AdvancedResumeScorer:
    """Advanced resume scoring system with multiple factors"""
    
    def __init__(self):
        self.skill_taxonomy = SkillTaxonomy()
        self.experience_parser = ExperienceParser()
        self.education_parser = EducationParser()
        self.semantic_calculator = SemanticSimilarityCalculator()
        
        # Scoring weights (semantic similarity removed)
        self.weights = {
            'keyword_match': 0.30,
            'skills_alignment': 0.35,
            'experience_relevance': 0.25,
            'education_alignment': 0.10
        }
        
        # Minimum floor for each category (removed to allow proper differentiation)
        self.minimum_floor = 0.0
    
    def calculate_keyword_match_score(self, resume_text: str, job_text: str) -> float:
        """Calculate keyword match score (25% weight)"""
        try:
            # Extract keywords from both texts
            resume_keywords = self._extract_keywords(resume_text)
            job_keywords = self._extract_keywords(job_text)
            
            if not job_keywords:
                return self.minimum_floor
            
            # Calculate overlap
            matched_keywords = set(resume_keywords) & set(job_keywords)
            overlap_ratio = len(matched_keywords) / len(job_keywords)
            
            # Apply floor
            return max(overlap_ratio, self.minimum_floor)
        except Exception as e:
            print(f"Error calculating keyword match: {e}")
            return self.minimum_floor
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        text_lower = text.lower()
        keywords = []
        
        # Technical keywords - more comprehensive list
        tech_keywords = [
            # Programming Languages
            'javascript', 'typescript', 'python', 'java', 'c#', '.net', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl',
            # Web Frameworks
            'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt', 'express', 'django', 'flask', 'spring', 'laravel', 'rails', 'asp.net', 'fastapi',
            # Runtime Environments
            'node.js', 'nodejs', 'deno', 'bun',
            # Databases
            'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'sqlite', 'oracle', 'sql server',
            # Cloud Platforms
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'vercel', 'netlify', 'digitalocean',
            # DevOps Tools
            'docker', 'kubernetes', 'k8s', 'jenkins', 'gitlab', 'github', 'terraform', 'ansible', 'chef', 'puppet', 'vagrant',
            # Version Control
            'git', 'svn', 'subversion', 'mercurial',
            # Testing Frameworks
            'jest', 'mocha', 'chai', 'cypress', 'selenium', 'pytest', 'junit', 'testng', 'rspec', 'phpunit',
            # Methodologies
            'agile', 'scrum', 'kanban', 'devops', 'ci/cd', 'cicd', 'tdd', 'bdd', 'microservices', 'rest', 'graphql', 'soa',
            # Roles and Experience
            'senior', 'junior', 'lead', 'architect', 'manager', 'director', 'full-stack', 'frontend', 'backend', 'mobile', 'web', 'desktop',
            # Soft Skills
            'leadership', 'communication', 'problem-solving', 'teamwork', 'mentoring', 'project management', 'code review', 'testing'
        ]
        
        for keyword in tech_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return keywords
    
    def calculate_skills_alignment_score(self, resume_skills: List[str], job_skills: List[str]) -> float:
        """Calculate skills alignment score (25% weight)"""
        try:
            if not job_skills:
                return self.minimum_floor
            
            # Normalize skills
            resume_normalized = [self.skill_taxonomy.normalize_skill(skill) for skill in resume_skills]
            job_normalized = [self.skill_taxonomy.normalize_skill(skill) for skill in job_skills]
            
            # Remove None values
            resume_normalized = [s for s in resume_normalized if s is not None]
            job_normalized = [s for s in job_normalized if s is not None]
            
            if not job_normalized:
                return self.minimum_floor
            
            # Calculate overlap
            matched_skills = set(resume_normalized) & set(job_normalized)
            alignment_ratio = len(matched_skills) / len(job_normalized)
            
            # Apply floor
            return max(alignment_ratio, self.minimum_floor)
        except Exception as e:
            print(f"Error calculating skills alignment: {e}")
            return self.minimum_floor
    
    def calculate_experience_relevance_score(self, resume_text: str, job_requirements: List[str]) -> float:
        """Calculate experience relevance score (20% weight)"""
        try:
            resume_exp = self.experience_parser.extract_experience_indicators(resume_text)
            job_exp = self.experience_parser.extract_experience_requirements(job_requirements)
            
            if not job_exp:
                return self.minimum_floor
            
            score = 0.0
            
            # Years of experience matching
            if 'years' in resume_exp and 'years' in job_exp:
                resume_years = resume_exp['years']
                job_years = job_exp['years']
                
                if resume_years >= job_years:
                    score += 0.6  # Meets or exceeds
                else:
                    # Partial credit based on ratio
                    ratio = resume_years / job_years
                    score += 0.3 * ratio
            
            # Role level matching
            if 'level' in resume_exp and 'level' in job_exp:
                resume_level = resume_exp['level']
                job_level = job_exp['level']
                
                level_scores = {
                    'junior': 1, 'mid': 2, 'senior': 3
                }
                
                resume_score = level_scores.get(resume_level, 2)
                job_score = level_scores.get(job_level, 2)
                
                if resume_score >= job_score:
                    score += 0.4  # Meets or exceeds level
                else:
                    # Partial credit
                    ratio = resume_score / job_score
                    score += 0.2 * ratio
            
            # Apply floor
            return max(score, self.minimum_floor)
        except Exception as e:
            print(f"Error calculating experience relevance: {e}")
            return self.minimum_floor
    
    def calculate_education_alignment_score(self, resume_text: str, job_requirements: List[str]) -> float:
        """Calculate education alignment score (10% weight)"""
        try:
            resume_edu = self.education_parser.extract_education(resume_text)
            job_edu = self.education_parser.extract_education_requirements(job_requirements)
            
            if not job_edu:
                return self.minimum_floor
            
            score = 0.0
            
            # Degree level matching
            if 'degree_level' in resume_edu and 'degree_level' in job_edu:
                degree_scores = {
                    'bachelors': 1, 'masters': 2, 'phd': 3
                }
                
                resume_degree = degree_scores.get(resume_edu['degree_level'], 1)
                job_degree = degree_scores.get(job_edu['degree_level'], 1)
                
                if resume_degree >= job_degree:
                    score += 0.6  # Meets or exceeds
                else:
                    # Partial credit
                    ratio = resume_degree / job_degree
                    score += 0.3 * ratio
            
            # Field of study matching
            if 'field' in resume_edu and 'field' in job_edu:
                resume_field = resume_edu['field'].lower()
                job_field = job_edu['field'].lower()
                
                if resume_field == job_field:
                    score += 0.4
                elif any(word in resume_field for word in job_field.split()) or any(word in job_field for word in resume_field.split()):
                    score += 0.2  # Partial match
            
            # Apply floor
            return max(score, self.minimum_floor)
        except Exception as e:
            print(f"Error calculating education alignment: {e}")
            return self.minimum_floor
    
    def calculate_semantic_similarity_score(self, resume_text: str, job_text: str) -> float:
        """Calculate semantic similarity score (20% weight)"""
        try:
            # Generate embeddings
            resume_embedding = self.semantic_calculator.generate_embeddings(resume_text)
            job_embedding = self.semantic_calculator.generate_embeddings(job_text)
            
            if resume_embedding is None or job_embedding is None:
                return self.minimum_floor
            
            # Calculate cosine similarity
            similarity = self.semantic_calculator.calculate_cosine_similarity(resume_embedding, job_embedding)
            
            # Normalize to 0-1 range and apply floor
            normalized_similarity = max(0, min(1, (similarity + 1) / 2))  # Convert from [-1,1] to [0,1]
            return max(normalized_similarity, self.minimum_floor)
        except Exception as e:
            print(f"Error calculating semantic similarity: {e}")
            return self.minimum_floor
    
    def score_resume(self, resume: Dict, job: Dict) -> ScoringBreakdown:
        """Score a resume against a job description"""
        try:
            # Prepare texts
            resume_text = f"{resume.get('title', '')} {resume.get('text_content', '')}"
            job_text = f"{job.get('title', '')} {job.get('company', '')} {job.get('description', '')} {' '.join(job.get('requirements', []))} {' '.join(job.get('skills', []))}"
            
            # Extract skills
            resume_skills = self.skill_taxonomy.extract_skills(resume_text)
            job_skills = [skill.lower() for skill in job.get('skills', [])]
            
            # Calculate individual scores (semantic similarity removed)
            keyword_score = self.calculate_keyword_match_score(resume_text, job_text)
            skills_score = self.calculate_skills_alignment_score(resume_skills, job_skills)
            experience_score = self.calculate_experience_relevance_score(resume_text, job.get('requirements', []))
            education_score = self.calculate_education_alignment_score(resume_text, job.get('requirements', []))
            
            # Calculate weighted total (without semantic similarity)
            total_score = (
                keyword_score * self.weights['keyword_match'] +
                skills_score * self.weights['skills_alignment'] +
                experience_score * self.weights['experience_relevance'] +
                education_score * self.weights['education_alignment']
            )
            
            # Calculate skills match/missing
            resume_normalized = [self.skill_taxonomy.normalize_skill(skill) for skill in resume_skills]
            job_normalized = [self.skill_taxonomy.normalize_skill(skill) for skill in job_skills]
            
            resume_normalized = [s for s in resume_normalized if s is not None]
            job_normalized = [s for s in job_normalized if s is not None]
            
            skills_match = list(set(resume_normalized) & set(job_normalized))
            missing_skills = list(set(job_normalized) - set(resume_normalized))
            
            return ScoringBreakdown(
                keyword_match={
                    "score": keyword_score,
                    "percentage": keyword_score * 100,
                    "weight": int(self.weights['keyword_match'] * 100)
                },
                skills_alignment={
                    "score": skills_score,
                    "percentage": skills_score * 100,
                    "weight": int(self.weights['skills_alignment'] * 100)
                },
                experience_relevance={
                    "score": experience_score,
                    "percentage": experience_score * 100,
                    "weight": int(self.weights['experience_relevance'] * 100)
                },
                education_alignment={
                    "score": education_score,
                    "percentage": education_score * 100,
                    "weight": int(self.weights['education_alignment'] * 100)
                },
                semantic_similarity={
                    "score": 0.0,
                    "percentage": 0.0,
                    "weight": 0
                },
                total_score=total_score,
                match_percentage=total_score * 100,
                skills_match=skills_match,
                missing_skills=missing_skills
            )
        except Exception as e:
            print(f"Error scoring resume: {e}")
            # Return default breakdown on error (semantic similarity removed)
            return ScoringBreakdown(
                keyword_match={"score": 0.3, "percentage": 30, "weight": 30},
                skills_alignment={"score": 0.3, "percentage": 30, "weight": 35},
                experience_relevance={"score": 0.3, "percentage": 30, "weight": 25},
                education_alignment={"score": 0.3, "percentage": 30, "weight": 10},
                semantic_similarity={"score": 0.0, "percentage": 0.0, "weight": 0},
                total_score=0.3,
                match_percentage=30.0,
                skills_match=[],
                missing_skills=[]
            )


# Global scorer instance
scorer = AdvancedResumeScorer()
