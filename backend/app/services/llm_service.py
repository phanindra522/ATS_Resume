"""
Flexible LLM Service supporting multiple providers
Supports OpenAI, Google Gemini, and other LLM providers
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.core.config import settings, LLMProvider

class LLMService(ABC):
    """Abstract base class for LLM services"""
    
    @abstractmethod
    async def parse_job_description(self, text: str) -> Dict[str, Any]:
        """Parse job description text and return structured data"""
        pass

class OpenAIService(LLMService):
    """OpenAI GPT service implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.LLM_PROVIDER_API_KEY
        if not self.api_key:
            raise ValueError("LLM API key not found. Set LLM_PROVIDER_API_KEY in .env file.")
    
    async def parse_job_description(self, text: str) -> Dict[str, Any]:
        """Parse job description using OpenAI GPT"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            prompt = self._create_job_parsing_prompt(text)
            
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,  # Configurable model for OpenAI
                messages=[
                    {"role": "system", "content": "You are an expert at parsing job descriptions and extracting structured information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content
            return self._parse_llm_response(result_text)
            
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _create_job_parsing_prompt(self, text: str) -> str:
        """Create structured prompt for job parsing"""
        return f"""
Parse the following job description and extract the information in JSON format:

Job Description Text:
{text}

Please extract and return ONLY a valid JSON object with the following structure:
{{
    "title": "Job title (e.g., 'Software Engineer')",
    "company": "Company name (if mentioned)",
    "description": "Job description/summary",
    "requirements": ["List of requirements as strings"],
    "skills": ["List of technical skills as strings"],
    "experience_level": "Experience level (Entry Level, Mid Level, Senior Level, Lead/Manager, or empty string)",
    "location": "Job location (e.g., 'San Francisco, CA', 'Remote', 'Hybrid')",
    "salary_range": "Salary range if mentioned (e.g., '$80,000 - $120,000')"
}}

Rules:
- If information is not found, use empty string for strings or empty array for arrays
- Extract skills from the text (programming languages, frameworks, tools, etc.)
- Extract requirements as individual items
- Be accurate and only include information explicitly mentioned
- Return ONLY the JSON object, no additional text
"""

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and return structured data"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # Fallback parsing if JSON is malformed
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsing if JSON parsing fails"""
        return {
            "title": "",
            "company": "",
            "description": text[:2000] if text else "",
            "requirements": [],
            "skills": [],
            "experience_level": "",
            "location": "",
            "salary_range": ""
        }

class GeminiService(LLMService):
    """Google Gemini service implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.LLM_PROVIDER_API_KEY
        if not self.api_key:
            raise ValueError("LLM API key not found. Set LLM_PROVIDER_API_KEY in .env file.")
    
    async def parse_job_description(self, text: str) -> Dict[str, Any]:
        """Parse job description using Google Gemini"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(settings.LLM_MODEL)  # Configurable model for Gemini
            
            prompt = self._create_job_parsing_prompt(text)
            
            response = await model.generate_content_async(prompt)
            result_text = response.text
            
            return self._parse_llm_response(result_text)
            
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _create_job_parsing_prompt(self, text: str) -> str:
        """Create structured prompt for job parsing (same as OpenAI)"""
        return f"""
Parse the following job description and extract the information in JSON format:

Job Description Text:
{text}

Please extract and return ONLY a valid JSON object with the following structure:
{{
    "title": "Job title (e.g., 'Software Engineer')",
    "company": "Company name",
    "description": "Job description/summary",
    "requirements": ["List of requirements as strings"],
    "skills": ["List of technical skills as strings"],
    "experience_level": "Experience level (Entry Level, Mid Level, Senior Level, Lead/Manager, or empty string)",
    "location": "Job location (e.g., 'San Francisco, CA', 'Remote', 'Hybrid')",
    "salary_range": "Salary range if mentioned (e.g., '$80,000 - $120,000')"
}}

Rules:
- If information is not found, use empty string for strings or empty array for arrays
- Extract skills from the text (programming languages, frameworks, tools, etc.)
- Extract requirements as individual items
- Be accurate and only include information explicitly mentioned
- Return ONLY the JSON object, no additional text
"""

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and return structured data (same as OpenAI)"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # Fallback parsing if JSON is malformed
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsing if JSON parsing fails"""
        return {
            "title": "",
            "company": "",
            "description": text[:2000] if text else "",
            "requirements": [],
            "skills": [],
            "experience_level": "",
            "location": "",
            "salary_range": ""
        }

class LLMServiceFactory:
    """Factory class to create LLM service instances"""
    
    @staticmethod
    def create_service(provider: LLMProvider, **kwargs) -> LLMService:
        """Create LLM service instance based on provider"""
        if provider == LLMProvider.OPENAI:
            return OpenAIService(**kwargs)
        elif provider == LLMProvider.GEMINI:
            return GeminiService(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def get_default_service() -> LLMService:
        """Get default LLM service based on configuration"""
        provider = settings.get_llm_provider()
        return LLMServiceFactory.create_service(provider)

# Convenience function for easy usage
async def parse_job_with_llm(text: str, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
    """
    Parse job description using LLM
    
    Args:
        text: Job description text to parse
        provider: LLM provider to use (defaults to environment setting)
    
    Returns:
        Dictionary with parsed job information
    """
    if provider:
        service = LLMServiceFactory.create_service(provider)
    else:
        service = LLMServiceFactory.get_default_service()
    
    return await service.parse_job_description(text)
