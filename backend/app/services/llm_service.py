"""
Flexible LLM Service supporting multiple providers
Supports OpenAI, Google Gemini, and other LLM providers
"""
import os
import json
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.core.config import settings, LLMProvider

class LLMService(ABC):
    """Abstract base class for LLM services"""
    
    @abstractmethod
    async def parse_job_description(self, text: str) -> Dict[str, Any]:
        """Parse job description text and return structured data"""
        pass
    
    @abstractmethod
    async def generate_completion(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1000) -> str:
        """Generate completion for custom prompts"""
        pass

class OpenAIService(LLMService):
    """OpenAI GPT service implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.LLM_PROVIDER_API_KEY
        if not self.api_key:
            raise ValueError("LLM API key not found. Set LLM_PROVIDER_API_KEY in .env file.")
    
    async def parse_job_description(self, text: str) -> Dict[str, Any]:
        """Parse job description using OpenAI GPT with rate limiting"""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                import openai
                
                client = openai.AsyncOpenAI(api_key=self.api_key)
                
                prompt = self._create_job_parsing_prompt(text)
                
                # Use Chat Completions API with max_completion_tokens (SDK-compatible)
                api_params = {
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are an expert at parsing job descriptions and extracting structured information."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_completion_tokens": 1000
                }
                
                # Handle temperature based on model - only gpt-5 family needs temperature=1.0
                if "gpt-5" in settings.LLM_MODEL.lower():
                    api_params["temperature"] = 1.0
                    print(f"⚠️ Using {settings.LLM_MODEL} with default temperature=1.0")
                else:
                    # GPT-4.1 and other models support custom temperature
                    api_params["temperature"] = 0.1
                    print(f"ℹ️ Using {settings.LLM_MODEL} with temperature=0.1")
                
                response = await client.chat.completions.create(**api_params)
                
                result_text = response.choices[0].message.content
                
                # Debug logging for empty responses
                if not result_text or not result_text.strip():
                    print(f"⚠️ OpenAI job parsing returned empty content. Response: {response}")
                    print(f"⚠️ Model: {settings.LLM_MODEL}, Prompt length: {len(prompt)} chars")
                    return {}
                
                return self._parse_llm_response(result_text)
                
            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit" in error_str or "429" in str(e):
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + (attempt * 0.5)  # Exponential backoff
                        print(f"⚠️ Rate limit hit in job parsing (attempt {attempt + 1}/{max_retries}), waiting {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"⚠️ Job parsing rate limit exceeded after {max_retries} attempts, returning empty result")
                        return {}
                else:
                    # Re-raise non-rate-limit errors immediately
                    raise e
        
        # If we get here, all retries failed
        return {}
    
    async def generate_completion(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1000) -> str:
        """Generate completion for custom prompts using OpenAI with rate limiting"""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                import openai
                
                client = openai.AsyncOpenAI(api_key=self.api_key)
                
                # Prepare API parameters - handle gpt-5 temperature restrictions
                api_params = {
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are an expert at analyzing text and extracting structured information."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_completion_tokens": max_tokens
                }
                
                # Handle temperature based on model - only gpt-5 family needs temperature=1.0
                if "gpt-5" in settings.LLM_MODEL.lower():
                    api_params["temperature"] = 1.0
                    print(f"⚠️ Using {settings.LLM_MODEL} with default temperature=1.0")
                else:
                    # GPT-4.1 and other models support custom temperature
                    temperature = max(0.0, min(2.0, temperature))
                    api_params["temperature"] = temperature
                    print(f"ℹ️ Using {settings.LLM_MODEL} with temperature={temperature}")
                
                response = await client.chat.completions.create(**api_params)
                
                # Debug logging for empty responses
                content = response.choices[0].message.content
                if not content or not content.strip():
                    print(f"⚠️ OpenAI returned empty content. Response: {response}")
                    print(f"⚠️ Full response object: {response.model_dump() if hasattr(response, 'model_dump') else str(response)}")
                    return ""
                
                return content
                
            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit" in error_str or "429" in str(e):
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + (attempt * 0.5)  # Exponential backoff with jitter
                        print(f"⚠️ Rate limit hit (attempt {attempt + 1}/{max_retries}), waiting {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"⚠️ Rate limit exceeded after {max_retries} attempts, falling back to rule-based processing")
                        return ""
                else:
                    # Re-raise non-rate-limit errors immediately
                    raise e
        
        # If we get here, all retries failed
        return ""
    
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
    """Google Gemini service implementation with rate limiting and error handling"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.LLM_PROVIDER_API_KEY
        if not self.api_key:
            raise ValueError("LLM API key not found. Set LLM_PROVIDER_API_KEY in .env file.")
        
        # Rate limiting: 30 requests per minute for free tier
        self.requests_per_minute = 30
        self.request_times = []
        self.min_delay = 2.0  # Minimum delay between requests (seconds)
        self.last_request_time = 0
        
        # Retry configuration
        self.max_retries = getattr(settings, 'LLM_RETRY_ATTEMPTS', 2)
        self.retry_delay = getattr(settings, 'LLM_TIMEOUT_SECONDS', 10)
    
    async def _rate_limit(self):
        """Implement rate limiting to avoid quota exceeded errors"""
        current_time = time.time()
        
        # Remove old requests outside the 1-minute window
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Check if we're at the limit
        if len(self.request_times) >= self.requests_per_minute:
            # Wait until the oldest request is outside the window
            wait_time = 60 - (current_time - self.request_times[0])
            if wait_time > 0:
                print(f"⚠️ Rate limit reached. Waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
        
        # Ensure minimum delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            await asyncio.sleep(self.min_delay - time_since_last)
        
        # Record this request
        self.request_times.append(current_time)
        self.last_request_time = current_time
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff on quota errors"""
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a quota/rate limit error
                if any(keyword in error_str for keyword in ['quota', 'rate limit', '429', 'exceeded']):
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"⚠️ Quota exceeded. Retrying in {wait_time} seconds... (attempt {attempt + 1}/{self.max_retries + 1})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print("❌ Max retries reached. Falling back to rule-based extraction.")
                        raise Exception("LLM quota exceeded - falling back to rule-based extraction")
                else:
                    # Not a quota error, re-raise immediately
                    raise e
        
        raise Exception("Max retries exceeded")
    
    async def parse_job_description(self, text: str) -> Dict[str, Any]:
        """Parse job description using Google Gemini with rate limiting and error handling"""
        async def _parse():
            await self._rate_limit()
            
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(settings.LLM_MODEL)
            
            prompt = self._create_job_parsing_prompt(text)
            
            response = await model.generate_content_async(prompt)
            result_text = response.text
            
            return self._parse_llm_response(result_text)
        
        try:
            return await self._retry_with_backoff(_parse)
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
        except Exception as e:
            if "quota exceeded" in str(e).lower() or "falling back" in str(e).lower():
                raise Exception("LLM_QUOTA_EXCEEDED")
            raise Exception(f"Gemini API error: {str(e)}")
    
    async def generate_completion(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1000) -> str:
        """Generate completion for custom prompts using Gemini with rate limiting and error handling"""
        async def _generate():
            await self._rate_limit()
            
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(settings.LLM_MODEL)
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = await model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        
        try:
            return await self._retry_with_backoff(_generate)
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
        except Exception as e:
            if "quota exceeded" in str(e).lower() or "falling back" in str(e).lower():
                raise Exception("LLM_QUOTA_EXCEEDED")
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
