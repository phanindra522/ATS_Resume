"""
Resume scoring endpoints - Updated to use advanced scoring service
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database, get_chroma_collection
from app.models.resume import ResumeWithScore
from app.routers.auth import get_current_user
from app.services.scoring_coordinator import coordinator
import numpy as np
from bson import ObjectId
import re
from datetime import datetime

router = APIRouter()

@router.post(
    "/score/{job_id}",
    summary="Score resumes against a job description",
    description="""
    Analyze and score all user resumes against a specific job description using the multi-agent scoring system.
    
    **Multi-Agent Scoring Process:**
    This endpoint uses 5 specialized AI agents to provide comprehensive analysis:
    
    1. **Keyword Matching Agent (20%)**: Identifies exact keyword matches between resume and job description
    2. **Skill Matching Agent (25%)**: Matches technical and soft skills using intelligent taxonomy
    3. **Experience Relevance Agent (20%)**: Analyzes years of experience and seniority level alignment
    4. **Education Alignment Agent (10%)**: Matches educational background with job requirements
    5. **Semantic Similarity Agent (25%)**: Analyzes semantic similarity using vector embeddings
    
    **Scoring Algorithm:**
    ```
    Total Score = (Keyword × 0.20) + (Skills × 0.25) + (Experience × 0.20) + (Education × 0.10) + (Semantic × 0.25)
    ```
    
    **Processing:**
    - All agents run in parallel for optimal performance
    - Results include detailed breakdown and evidence
    - Confidence scores indicate reliability of analysis
    - Results are automatically saved for future reference
    
    **Authentication Required:**
    This endpoint requires a valid JWT token and the job must belong to the authenticated user.
    """,
    responses={
        200: {
            "description": "Scoring completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Scoring completed successfully",
                        "job_id": "507f1f77bcf86cd799439011",
                        "total_resumes_scored": 5,
                        "results": [
                            {
                                "resume_id": "507f1f77bcf86cd799439012",
                                "resume_title": "Software Engineer Resume",
                                "total_score": 0.85,
                                "match_percentage": 85.0,
                                "confidence": 0.92,
                                "agent_breakdown": {
                                    "keyword_matching": {"score": 0.80, "percentage": 80.0},
                                    "skill_matching": {"score": 0.90, "percentage": 90.0},
                                    "experience_relevance": {"score": 0.75, "percentage": 75.0},
                                    "education_alignment": {"score": 0.95, "percentage": 95.0},
                                    "semantic_similarity": {"score": 0.88, "percentage": 88.0}
                                },
                                "skills_match": ["Python", "React", "AWS", "Docker"],
                                "missing_skills": ["Kubernetes", "GraphQL"]
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Job not found or no resumes available",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Job not found"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing token"
        }
    }
)
async def score_resumes_for_job(job_id: str, current_user = Depends(get_current_user)):
    """Score all resumes against a specific job description using advanced scoring"""
    try:
        db = get_database()
        
        # Get the job
        job = await db.jobs.find_one({
            "_id": job_id,
            "user_id": current_user["_id"]
        })
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get all resumes for the user
        resumes_cursor = await db.resumes.find({"user_id": current_user["_id"]})
        resumes = await resumes_cursor.to_list(length=100)
        
        if not resumes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resumes found"
            )
        
        # Use the multi-agent scoring coordinator
        scored_resumes = []
        
        for resume in resumes:
            # Score resume using the multi-agent coordinator
            scoring_breakdown = await coordinator.score_resume(resume, job)
            
            # Create scored resume with the breakdown
            scored_resume = {
                **resume,
                "score": scoring_breakdown.total_score,
                "match_percentage": scoring_breakdown.match_percentage,
                "skills_match": scoring_breakdown.skills_match,
                "missing_skills": scoring_breakdown.missing_skills,
                "score_breakdown": {
                    "keyword_match": scoring_breakdown.keyword_match,
                    "skills_alignment": scoring_breakdown.skills_alignment,
                    "experience_relevance": scoring_breakdown.experience_relevance,
                    "education_alignment": scoring_breakdown.education_alignment,
                    "semantic_similarity": scoring_breakdown.semantic_similarity
                },
                "confidence": scoring_breakdown.confidence,
                "timestamp": scoring_breakdown.timestamp.isoformat()
            }
            scored_resumes.append(scored_resume)
        
        # Sort by score (highest first)
        scored_resumes.sort(key=lambda x: x["score"], reverse=True)
        
        # Save scoring results
        scoring_result = {
            "user_id": current_user["_id"],
            "job_id": job_id,
            "scored_resumes": scored_resumes,
            "created_at": datetime.utcnow()
        }
        
        # Save to database
        await db.scoring_results.insert_one(scoring_result)
        
        return {
            "job": job,
            "scored_resumes": scored_resumes,
            "total_resumes": len(scored_resumes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error scoring resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to score resumes: {str(e)}"
        )

@router.get("/results/{job_id}")
async def get_scoring_results(job_id: str, current_user = Depends(get_current_user)):
    """Get scoring results for a specific job"""
    try:
        db = get_database()
        
        # Get the most recent scoring result for this job
        result = await db.scoring_results.find_one({
            "job_id": job_id,
            "user_id": current_user["_id"]
        }, sort=[("created_at", -1)])
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scoring results found for this job"
            )
        
        # Get the job details
        job = await db.jobs.find_one({
            "_id": job_id,
            "user_id": current_user["_id"]
        })
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return {
            "job": job,
            "scored_resumes": result["scored_resumes"],
            "total_resumes": len(result["scored_resumes"]),
            "created_at": result["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting scoring results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scoring results: {str(e)}"
        )

@router.get("/results")
async def get_all_scoring_results(current_user = Depends(get_current_user)):
    """Get all scoring results for the current user"""
    try:
        db = get_database()
        
        # Get all scoring results for the user
        results_cursor = await db.scoring_results.find({"user_id": current_user["_id"]})
        results = await results_cursor.to_list(length=100)
        
        # Sort by creation date (newest first)
        results.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "scoring_results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        print(f"Error getting all scoring results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scoring results: {str(e)}"
        )


@router.get("/formula")
async def get_scoring_formula():
    """Get the scoring formula used by the multi-agent system"""
    try:
        formula = coordinator.get_scoring_formula()
        agent_status = await coordinator.get_agent_status()
        
        return {
            "formula": formula,
            "agents": agent_status,
            "total_weight": sum(agent["weight"] for agent in agent_status.values())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scoring formula: {str(e)}"
        )
