"""
Test script to demonstrate enhanced agents with LLM capabilities
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from app.services.agents.keyword_agent import KeywordMatchingAgent
from app.services.agents.skill_agent import SkillMatchingAgent
from app.core.config import settings

async def test_enhanced_agents():
    """Test the enhanced agents with sample data"""
    
    print("🚀 Testing Enhanced Multi-Agent System")
    print("=" * 50)
    
    # Sample resume data
    sample_resume = {
        "id": "test_resume_1",
        "title": "Software Engineer Resume",
        "content": """
        John Doe - Software Engineer
        
        Experience:
        - 5+ years developing web applications using React, Node.js, and Python
        - Built scalable microservices with Docker and Kubernetes
        - Experience with AWS cloud services including EC2, S3, and Lambda
        - Proficient in JavaScript, TypeScript, and modern web frameworks
        - Strong background in agile development and CI/CD pipelines
        
        Skills:
        - Programming: JavaScript, TypeScript, Python, Java
        - Frameworks: React, Angular, Node.js, Express, Django
        - Cloud: AWS, Azure, Google Cloud Platform
        - Tools: Docker, Kubernetes, Jenkins, Git, Terraform
        - Databases: MySQL, PostgreSQL, MongoDB, Redis
        - Methodologies: Agile, Scrum, TDD, DevOps
        """
    }
    
    # Sample job data
    sample_job = {
        "id": "test_job_1",
        "title": "Senior Full Stack Developer",
        "description": "We are looking for a Senior Full Stack Developer...",
        "requirements": [
            "5+ years of experience in web development",
            "Strong proficiency in JavaScript and TypeScript",
            "Experience with React and Node.js",
            "Knowledge of cloud platforms (AWS preferred)",
            "Experience with containerization (Docker, Kubernetes)",
            "Understanding of CI/CD practices",
            "Strong problem-solving and communication skills"
        ],
        "skills": [
            "JavaScript", "TypeScript", "React", "Node.js", "AWS", 
            "Docker", "Kubernetes", "CI/CD", "Agile", "Communication"
        ]
    }
    
    print(f"📊 LLM Configuration Status:")
    print(f"   Provider: {settings.LLM_PROVIDER}")
    print(f"   API Key Configured: {'✅' if settings.LLM_PROVIDER_API_KEY else '❌'}")
    print(f"   Use LLM for Keywords: {'✅' if getattr(settings, 'USE_LLM_FOR_KEYWORDS', True) else '❌'}")
    print(f"   Use LLM for Skills: {'✅' if getattr(settings, 'USE_LLM_FOR_SKILLS', True) else '❌'}")
    print()
    
    # Test Keyword Matching Agent
    print("🔍 Testing Enhanced Keyword Matching Agent")
    print("-" * 40)
    
    keyword_agent = KeywordMatchingAgent()
    keyword_result = await keyword_agent.analyze(sample_resume, sample_job)
    
    print(f"   Score: {keyword_result.score:.2f} ({keyword_result.percentage:.1f}%)")
    print(f"   Confidence: {keyword_result.confidence:.2f}")
    print(f"   Method: {keyword_result.evidence.get('extraction_method', 'unknown')}")
    print(f"   Resume Keywords: {len(keyword_result.evidence.get('resume_keywords', []))}")
    print(f"   Job Keywords: {len(keyword_result.evidence.get('job_keywords', []))}")
    print(f"   Matched Keywords: {len(keyword_result.evidence.get('matched_keywords', []))}")
    print()
    
    # Test Skill Matching Agent
    print("🛠️ Testing Enhanced Skill Matching Agent")
    print("-" * 40)
    
    skill_agent = SkillMatchingAgent()
    skill_result = await skill_agent.analyze(sample_resume, sample_job)
    
    print(f"   Score: {skill_result.score:.2f} ({skill_result.percentage:.1f}%)")
    print(f"   Confidence: {skill_result.confidence:.2f}")
    print(f"   Method: {skill_result.evidence.get('extraction_method', 'unknown')}")
    print(f"   Resume Skills: {len(skill_result.evidence.get('resume_skills', []))}")
    print(f"   Job Skills: {len(skill_result.evidence.get('job_skills', []))}")
    print(f"   Matched Skills: {len(skill_result.evidence.get('matched_skills', []))}")
    print()
    
    # Summary
    print("📈 Enhancement Summary")
    print("-" * 40)
    print(f"✅ Keyword Matching Agent: Enhanced with LLM-powered extraction")
    print(f"✅ Skill Matching Agent: Enhanced with LLM-powered normalization")
    print(f"✅ Fallback Mechanisms: Rule-based approaches as backup")
    print(f"✅ Configuration: Flexible LLM enable/disable settings")
    print()
    
    if keyword_result.evidence.get('extraction_method') == 'llm_enhanced':
        print("🎯 LLM Enhancement Status: ACTIVE")
        print("   - Dynamic keyword discovery enabled")
        print("   - Intelligent skill normalization enabled")
        print("   - Context-aware analysis active")
    else:
        print("⚠️ LLM Enhancement Status: FALLBACK MODE")
        print("   - Using rule-based approaches")
        print("   - Check LLM configuration if needed")
    
    print("\n🚀 Enhanced Multi-Agent System Ready!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_agents())

