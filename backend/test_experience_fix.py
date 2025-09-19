#!/usr/bin/env python3
"""
Test script to verify the experience matching fix for marketing manager scenario
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.agents.experience_agent import ExperienceRelevanceAgent


async def test_marketing_manager_experience():
    """Test experience agent with marketing manager scenario"""
    print("🧪 Testing Marketing Manager Experience Matching")
    print("=" * 60)
    
    agent = ExperienceRelevanceAgent()
    
    # Marketing manager job (from actual job description)
    job = {
        "title": "Marketing Manager - Digital Marketing",
        "description": """
        We are seeking an experienced Marketing Manager to lead our digital marketing initiatives 
        and drive brand awareness and customer acquisition.
        """,
        "requirements": [
            "Bachelor's degree in Marketing, Business, or related field",
            "4-6 years of marketing experience",  # This should be extracted!
            "Experience with digital marketing channels and tools",
            "Strong analytical skills and data-driven mindset",
            "Excellent written and verbal communication skills",
            "Experience with marketing automation platforms",
            "Knowledge of SEO, SEM, and social media marketing",
            "Project management and leadership skills"
        ],
        "experience_level": "Mid Level"
    }
    
    # Test with different resume scenarios
    test_scenarios = [
        {
            "name": "Software Engineer Resume (Mismatch)",
            "resume": {
                "text_content": """
                John Doe
                Senior Software Engineer with 8+ years of experience
                
                Experience:
                - 8+ years in software development
                - Led multiple teams of 5+ developers
                - Built scalable web applications
                - Experience with microservices architecture
                
                Skills:
                - Python, JavaScript, React, Node.js
                - AWS, Docker, Kubernetes
                - PostgreSQL, MongoDB
                """
            }
        },
        {
            "name": "Marketing Manager Resume (Good Match)",
            "resume": {
                "text_content": """
                Jane Smith
                Digital Marketing Manager
                
                Experience:
                - 5 years of marketing experience
                - 3 years in digital marketing roles
                - Led marketing campaigns with $500K+ budgets
                - Managed social media marketing across multiple platforms
                
                Skills:
                - Digital Marketing, Content Marketing
                - SEO, SEM, Google Analytics
                - Marketing Automation, Email Marketing
                - Social Media Marketing, Facebook Ads
                """
            }
        },
        {
            "name": "Junior Marketing Resume (Underqualified)",
            "resume": {
                "text_content": """
                Alex Johnson
                Marketing Coordinator
                
                Experience:
                - 2 years of marketing experience
                - Assisted with social media campaigns
                - Created content for marketing materials
                
                Skills:
                - Social Media Marketing
                - Content Creation
                - Basic Google Analytics
                """
            }
        },
        {
            "name": "No Experience Resume (Poor Match)",
            "resume": {
                "text_content": """
                Sam Davis
                Recent Graduate
                
                Education:
                - Bachelor's in Marketing
                - Marketing internship (3 months)
                
                Skills:
                - Basic marketing knowledge
                - Social media familiarity
                """
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📊 Testing: {scenario['name']}")
        print("-" * 40)
        
        result = await agent.analyze(scenario['resume'], job)
        
        print(f"   Score: {result.score:.3f}")
        print(f"   Percentage: {result.percentage:.1f}%")
        print(f"   Confidence: {result.confidence:.3f}")
        
        if result.evidence:
            resume_exp = result.evidence.get('resume_experience', {})
            job_exp = result.evidence.get('job_experience', {})
            
            print(f"   Resume Years: {resume_exp.get('years', 0)}")
            print(f"   Job Required Years: {job_exp.get('years', 0)}")
            print(f"   Resume Level: {resume_exp.get('level', 'Unknown')}")
            print(f"   Job Required Level: {job_exp.get('level', 'Unknown')}")
            print(f"   Years Match: {result.evidence.get('years_match', False)}")
            print(f"   Level Match: {result.evidence.get('level_match', 'Unknown')}")
            
            if result.evidence.get('experience_gap', 0) > 0:
                print(f"   Experience Gap: {result.evidence['experience_gap']} years")
        
        if result.error:
            print(f"   ❌ Error: {result.error}")


async def test_experience_extraction():
    """Test the experience extraction improvements"""
    print("\n🔍 Testing Experience Extraction Improvements")
    print("=" * 60)
    
    agent = ExperienceRelevanceAgent()
    
    test_requirements = [
        "4-6 years of marketing experience",
        "Minimum 5 years of experience",
        "At least 3 years in digital marketing",
        "Experience: 7+ years required",
        "Minimum of 2 years professional experience",
        "Requires 4+ years of relevant experience"
    ]
    
    print("📝 Testing Requirements Extraction:")
    for req in test_requirements:
        result = agent._extract_experience_requirements([req])
        print(f"   '{req}' → {result.get('years', 0)} years, {result.get('level', 'unknown')} level")


async def main():
    """Run all tests"""
    try:
        await test_experience_extraction()
        await test_marketing_manager_experience()
        
        print("\n✅ Experience matching tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())