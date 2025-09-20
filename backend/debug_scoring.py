"""
Debug Scoring System - Real Data Test

Test the scoring system with actual database data to see why 
web interface is showing 0% matches.
"""

import asyncio
from app.database import get_database
from app.services.scoring_coordinator import coordinator
import json

async def debug_scoring_with_real_data():
    """Debug scoring using real database data"""
    print("🔍 Debugging Scoring System with Real Data")
    print("=" * 50)
    
    try:
        # Get database connection
        db = get_database()
        
        # Get a real job from database
        jobs = await db.jobs.find().limit(1).to_list(1)
        if not jobs:
            print("❌ No jobs found in database")
            return
        
        job = jobs[0]
        print(f"✅ Found job: {job.get('title', 'Unknown')}")
        print(f"   Company: {job.get('company', 'N/A')}")
        print(f"   Skills: {job.get('skills', [])}")
        
        # Get a real resume from database
        resumes = await db.resumes.find().limit(1).to_list(1)
        if not resumes:
            print("❌ No resumes found in database")
            return
            
        resume = resumes[0]
        print(f"✅ Found resume: {resume.get('title', 'Unknown')}")
        print(f"   Filename: {resume.get('filename', 'N/A')}")
        print(f"   Content length: {len(resume.get('content', ''))}")
        
        # Debug the resume content
        content = resume.get('content', '')
        if len(content) < 50:
            print(f"⚠️ Resume content seems very short: '{content}'")
        else:
            print(f"✅ Resume content preview: {content[:200]}...")
        
        # Test scoring
        print("\n🧪 Testing Scoring System...")
        
        try:
            result = await coordinator.score_resume(resume, job)
            
            print(f"\n📊 Scoring Results:")
            print(f"   Total Score: {result.total_score:.3f}")
            print(f"   Match Percentage: {result.match_percentage:.1f}%")
            print(f"   Confidence: {result.confidence:.3f}")
            
            print(f"\n🔍 Agent Breakdown:")
            print(f"   Keyword Match: {result.keyword_match}")
            print(f"   Skills Alignment: {result.skills_alignment}")  
            print(f"   Experience Relevance: {result.experience_relevance}")
            print(f"   Education Alignment: {result.education_alignment}")
            print(f"   Semantic Similarity: {result.semantic_similarity}")
            
            print(f"\n🎯 Skills Analysis:")
            print(f"   Matched Skills: {result.skills_match}")
            print(f"   Missing Skills: {result.missing_skills}")
            
            if result.total_score == 0.0:
                print("\n❌ PROBLEM: Total score is 0!")
                print("   Checking individual agent results...")
                
                # Check individual agent results
                for agent_name, agent_result in result.agent_results.items():
                    print(f"   {agent_name}: score={agent_result.score:.3f}, error='{agent_result.error}'")
            else:
                print(f"\n✅ Scoring working properly: {result.match_percentage:.1f}%")
                
        except Exception as e:
            print(f"❌ Scoring failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()

async def test_with_mock_data():
    """Test with mock data to compare"""
    print("\n🧪 Testing with Mock Data")
    print("=" * 30)
    
    mock_resume = {
        "_id": "mock_resume",
        "title": "Software Engineer",
        "content": "Experienced software engineer with 5 years of Python, JavaScript, React, and AWS experience. Strong background in web development and cloud technologies. Bachelor's degree in Computer Science. Led team of 3 developers on multiple projects using agile methodologies.",
        "skills": ["Python", "JavaScript", "React", "AWS"],
        "experience_years": 5,
        "education": "Bachelor's Computer Science"
    }
    
    mock_job = {
        "_id": "mock_job",
        "title": "Senior Developer",
        "company": "Tech Corp", 
        "description": "Looking for experienced developer to build web applications.",
        "requirements": [
            "3+ years of software development experience",
            "Strong Python and JavaScript skills",
            "Experience with React and AWS"
        ],
        "skills": ["Python", "JavaScript", "React", "AWS", "Docker"],
        "experience_level": "Senior Level"
    }
    
    try:
        result = await coordinator.score_resume(mock_resume, mock_job)
        print(f"✅ Mock scoring result: {result.match_percentage:.1f}%")
        print(f"   Skills matched: {result.skills_match}")
        return result.total_score > 0
    except Exception as e:
        print(f"❌ Mock scoring failed: {e}")
        return False

def main():
    """Run the debugging tests"""
    print("🚀 Starting Scoring System Debug")
    
    # Test with mock data first
    mock_success = asyncio.run(test_with_mock_data())
    
    if mock_success:
        print("✅ Mock data works - testing real data...")
        asyncio.run(debug_scoring_with_real_data())
    else:
        print("❌ Mock data failed - scoring system has fundamental issues")

if __name__ == "__main__":
    main()