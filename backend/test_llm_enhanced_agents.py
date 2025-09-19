#!/usr/bin/env python3
"""
Test script for LLM-enhanced education and experience agents
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.agents.education_agent import EducationAlignmentAgent
from app.services.agents.experience_agent import ExperienceRelevanceAgent


async def test_education_agent():
    """Test the enhanced education agent"""
    print("🎓 Testing Enhanced Education Agent")
    print("=" * 50)
    
    agent = EducationAlignmentAgent()
    
    # Test resume with education
    resume = {
        "content": """
        John Doe
        Software Engineer
        
        Education:
        Master of Science in Computer Science
        Stanford University (2020-2022)
        
        Bachelor of Science in Software Engineering  
        University of California, Berkeley (2016-2020)
        GPA: 3.8/4.0
        
        Certifications:
        - AWS Certified Solutions Architect
        - Google Cloud Professional Developer
        """
    }
    
    # Test job with education requirements
    job = {
        "title": "Senior Software Engineer",
        "description": "We are looking for a senior software engineer to join our team.",
        "requirements": [
            "Bachelor's degree in Computer Science or related field",
            "Master's degree preferred",
            "3+ years of software development experience",
            "AWS certification preferred"
        ],
        "experience_level": "Senior Level"
    }
    
    result = await agent.analyze(resume, job)
    
    print(f"📊 Education Score: {result.score:.3f}")
    print(f"📊 Percentage: {result.percentage:.1f}%")
    print(f"🎯 Confidence: {result.confidence:.3f}")
    
    if result.evidence:
        print("\n📋 Evidence:")
        resume_edu = result.evidence.get('resume_education', {})
        job_edu = result.evidence.get('job_education', {})
        
        print(f"   Resume Education Level: {resume_edu.get('degree_level', 'Unknown')}")
        print(f"   Resume Field: {resume_edu.get('field', 'Unknown')}")
        print(f"   Job Required Level: {job_edu.get('degree_level', 'Unknown')}")
        print(f"   Job Required Field: {job_edu.get('field', 'Unknown')}")
        print(f"   Degree Match: {result.evidence.get('degree_level_match', False)}")
        print(f"   Field Match: {result.evidence.get('field_match', 'Unknown')}")
        
        # Show LLM-specific information if available
        if resume_edu.get('extraction_method') == 'llm_enhanced':
            print(f"   LLM Confidence: {resume_edu.get('llm_confidence', 0):.3f}")
            if resume_edu.get('institutions'):
                print(f"   Institutions: {', '.join(resume_edu['institutions'])}")
            if resume_edu.get('certifications'):
                print(f"   Certifications: {', '.join(resume_edu['certifications'])}")
    
    if result.error:
        print(f"❌ Error: {result.error}")
    
    print()


async def test_experience_agent():
    """Test the enhanced experience agent"""
    print("💼 Testing Enhanced Experience Agent")
    print("=" * 50)
    
    agent = ExperienceRelevanceAgent()
    
    # Test resume with experience
    resume = {
        "content": """
        Jane Smith
        Senior Software Engineer
        
        Experience:
        Senior Software Engineer | Google | 2021-Present (3 years)
        - Led a team of 5 developers on cloud infrastructure projects
        - Architected microservices handling 10M+ requests/day
        - Mentored junior developers and conducted code reviews
        
        Software Engineer | Meta | 2019-2021 (2 years)
        - Developed full-stack web applications using React and Node.js
        - Optimized database queries reducing response time by 40%
        - Collaborated with product managers on feature requirements
        
        Junior Developer | Startup Inc | 2018-2019 (1 year)
        - Built REST APIs using Python and Django
        - Implemented automated testing frameworks
        """
    }
    
    # Test job with experience requirements
    job = {
        "title": "Lead Software Engineer",
        "description": "We need a lead software engineer with strong technical leadership skills.",
        "requirements": [
            "5+ years of software development experience",
            "3+ years in senior or lead roles",
            "Experience with cloud platforms (AWS, GCP, Azure)",
            "Leadership and mentoring experience required",
            "Full-stack development experience"
        ],
        "experience_level": "Senior Level"
    }
    
    result = await agent.analyze(resume, job)
    
    print(f"📊 Experience Score: {result.score:.3f}")
    print(f"📊 Percentage: {result.percentage:.1f}%")
    print(f"🎯 Confidence: {result.confidence:.3f}")
    
    if result.evidence:
        print("\n📋 Evidence:")
        resume_exp = result.evidence.get('resume_experience', {})
        job_exp = result.evidence.get('job_experience', {})
        
        print(f"   Resume Years: {resume_exp.get('years', 0)}")
        print(f"   Resume Level: {resume_exp.get('level', 'Unknown')}")
        print(f"   Job Required Years: {job_exp.get('years', 0)}")
        print(f"   Job Required Level: {job_exp.get('level', 'Unknown')}")
        print(f"   Years Match: {result.evidence.get('years_match', False)}")
        print(f"   Level Match: {result.evidence.get('level_match', 'Unknown')}")
        print(f"   Experience Gap: {result.evidence.get('experience_gap', 0)} years")
        
        # Show LLM-specific information if available
        if resume_exp.get('extraction_method') == 'llm_enhanced':
            print(f"   LLM Confidence: {resume_exp.get('llm_confidence', 0):.3f}")
            if resume_exp.get('positions'):
                print(f"   Positions: {', '.join(resume_exp['positions'])}")
            if resume_exp.get('companies'):
                print(f"   Companies: {', '.join(resume_exp['companies'])}")
            if resume_exp.get('leadership_experience'):
                print(f"   Leadership Experience: Yes")
    
    if result.error:
        print(f"❌ Error: {result.error}")
    
    print()


async def main():
    """Run all tests"""
    print("🚀 Testing LLM-Enhanced Education and Experience Agents")
    print("=" * 60)
    print()
    
    try:
        await test_education_agent()
        await test_experience_agent()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())