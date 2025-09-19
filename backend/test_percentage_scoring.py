#!/usr/bin/env python3
"""
Test script to demonstrate percentage scoring with 2 decimal place rounding
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.scoring_coordinator import MultiAgentScoringCoordinator
from app.services.agents.keyword_agent import KeywordMatchingAgent
from app.services.agents.skill_agent import SkillMatchingAgent
from app.services.agents.experience_agent import ExperienceRelevanceAgent
from app.services.agents.education_agent import EducationAlignmentAgent
from app.services.agents.semantic_agent import SemanticSimilarityAgent

async def test_percentage_scoring():
    """Test the percentage scoring system"""
    
    print("🧪 Testing Percentage Scoring System")
    print("=" * 50)
    
    # Initialize scoring coordinator
    coordinator = MultiAgentScoringCoordinator()
    
    # Sample resume data
    resume_data = {
        "id": "test-resume-1",
        "title": "Senior Software Engineer",
        "text_content": """
        John Doe
        Senior Software Engineer with 8+ years of experience
        
        Skills:
        - Python, JavaScript, React, Node.js
        - AWS, Docker, Kubernetes
        - PostgreSQL, MongoDB
        - Agile, Scrum, DevOps
        
        Experience:
        - 8+ years in software development
        - Led multiple teams of 5+ developers
        - Built scalable web applications
        - Experience with microservices architecture
        
        Education:
        - Bachelor's in Computer Science
        - Master's in Software Engineering
        """
    }
    
    # Sample job data
    job_data = {
        "id": "test-job-1",
        "title": "Senior Full Stack Developer",
        "description": """
        We are looking for a Senior Full Stack Developer with 5+ years of experience.
        
        Required Skills:
        - Python, JavaScript, React, Node.js
        - AWS, Docker, Kubernetes
        - PostgreSQL, MongoDB
        - Agile, Scrum, DevOps
        
        Experience Requirements:
        - 5+ years in software development
        - Team leadership experience
        - Experience with scalable applications
        - Microservices architecture knowledge
        
        Education Requirements:
        - Bachelor's degree in Computer Science or related field
        """
    }
    
    print("📊 Running scoring analysis...")
    
    try:
        # Run the scoring analysis
        breakdown = await coordinator.score_resume(resume_data, job_data)
        
        print("\n🎯 SCORING RESULTS (with 2 decimal place percentages)")
        print("=" * 60)
        
        # Display individual agent scores
        print(f"📝 Keyword Matching: {breakdown.keyword_match['percentage']}% (Score: {breakdown.keyword_match['score']}, Weight: {breakdown.keyword_match['weight']}%)")
        print(f"🔧 Skills Alignment: {breakdown.skills_alignment['percentage']}% (Score: {breakdown.skills_alignment['score']}, Weight: {breakdown.skills_alignment['weight']}%)")
        print(f"💼 Experience Relevance: {breakdown.experience_relevance['percentage']}% (Score: {breakdown.experience_relevance['score']}, Weight: {breakdown.experience_relevance['weight']}%)")
        print(f"🎓 Education Alignment: {breakdown.education_alignment['percentage']}% (Score: {breakdown.education_alignment['score']}, Weight: {breakdown.education_alignment['weight']}%)")
        print(f"🧠 Semantic Similarity: {breakdown.semantic_similarity['percentage']}% (Score: {breakdown.semantic_similarity['score']}, Weight: {breakdown.semantic_similarity['weight']}%)")
        
        print("\n" + "=" * 60)
        print(f"🏆 TOTAL SCORE: {breakdown.total_score} (Decimal)")
        print(f"📈 MATCH PERCENTAGE: {breakdown.match_percentage}%")
        print(f"🎯 CONFIDENCE: {breakdown.confidence}%")
        print("=" * 60)
        
        # Display confidence breakdown
        print("\n🔍 CONFIDENCE BREAKDOWN:")
        print(f"   Keyword Matching: {breakdown.keyword_match['confidence']}%")
        print(f"   Skills Alignment: {breakdown.skills_alignment['confidence']}%")
        print(f"   Experience Relevance: {breakdown.experience_relevance['confidence']}%")
        print(f"   Education Alignment: {breakdown.education_alignment['confidence']}%")
        print(f"   Semantic Similarity: {breakdown.semantic_similarity['confidence']}%")
        
        # Display skills information
        if breakdown.skills_match:
            print(f"\n✅ MATCHED SKILLS ({len(breakdown.skills_match)}):")
            for skill in breakdown.skills_match[:10]:  # Show first 10
                print(f"   - {skill}")
            if len(breakdown.skills_match) > 10:
                print(f"   ... and {len(breakdown.skills_match) - 10} more")
        
        if breakdown.missing_skills:
            print(f"\n❌ MISSING SKILLS ({len(breakdown.missing_skills)}):")
            for skill in breakdown.missing_skills[:10]:  # Show first 10
                print(f"   - {skill}")
            if len(breakdown.missing_skills) > 10:
                print(f"   ... and {len(breakdown.missing_skills) - 10} more")
        
        # Test with different scenarios
        print("\n" + "=" * 60)
        print("🧪 TESTING DIFFERENT SCENARIOS")
        print("=" * 60)
        
        # Test with lower match scenario
        low_match_job = {
            "id": "test-job-2",
            "title": "Data Scientist",
            "description": """
            We are looking for a Data Scientist with expertise in:
            - Machine Learning, Deep Learning
            - Python, R, SQL
            - TensorFlow, PyTorch
            - Statistics, Mathematics
            - PhD in Data Science or related field
            """
        }
        
        print("\n📊 Testing with Data Scientist role (lower match)...")
        breakdown2 = await coordinator.score_resume(resume_data, low_match_job)
        
        print(f"   Total Score: {breakdown2.total_score}")
        print(f"   Match Percentage: {breakdown2.match_percentage}%")
        print(f"   Confidence: {breakdown2.confidence}%")
        
        # Test with perfect match scenario
        perfect_match_job = {
            "id": "test-job-3",
            "title": "Senior Software Engineer",
            "description": """
            We are looking for a Senior Software Engineer with:
            - Python, JavaScript, React, Node.js
            - AWS, Docker, Kubernetes
            - PostgreSQL, MongoDB
            - Agile, Scrum, DevOps
            - 8+ years experience
            - Bachelor's in Computer Science
            - Team leadership experience
            """
        }
        
        print("\n📊 Testing with perfect match role...")
        breakdown3 = await coordinator.score_resume(resume_data, perfect_match_job)
        
        print(f"   Total Score: {breakdown3.total_score}")
        print(f"   Match Percentage: {breakdown3.match_percentage}%")
        print(f"   Confidence: {breakdown3.confidence}%")
        
        print("\n✅ Percentage scoring test completed successfully!")
        print("🎯 All scores are now rounded to 2 decimal places")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_percentage_scoring())
