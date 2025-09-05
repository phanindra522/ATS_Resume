"""
Resume scoring endpoints - Updated to use advanced scoring service
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database, get_chroma_collection
from app.models.resume import ResumeWithScore
from app.routers.auth import get_current_user
from app.services.scoring import scorer
import numpy as np
from bson import ObjectId
import re
from datetime import datetime

router = APIRouter()

@router.post("/score/{job_id}")
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
        
        # Use the advanced scoring service
        scored_resumes = []
        
        for resume in resumes:
            # Score resume using the advanced scoring service
            scoring_breakdown = scorer.score_resume(resume, job)
            
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
                }
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
