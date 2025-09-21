"""
Resume scoring endpoints - Updated to use advanced scoring service
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database, get_chroma_collection
from app.models.resume import ResumeWithScore, ScoringResponse
from app.routers.auth import get_current_user
from app.services.scoring_coordinator import coordinator
from app.autogen_orchestrator import get_autogen_orchestrator
import numpy as np
from bson import ObjectId
import uuid
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
        
        # Validate job data to ensure it has skills for scoring
        if not job.get('skills') or len(job['skills']) == 0:
            # Extract skills from job title and description
            job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            skill_keywords = ['python', 'javascript', 'react', 'java', 'aws', 'docker', 
                             'sql', 'node.js', 'angular', 'vue', 'typescript', 'git', 'html', 'css']
            found_skills = [skill for skill in skill_keywords if skill in job_text]
            job['skills'] = found_skills[:8] if found_skills else ['programming', 'software development']
        
        for resume in resumes:
            # Validate resume data to ensure it has content for scoring
            if not resume.get('content') or len(resume.get('content', '').strip()) < 20:
                # Use title and filename as fallback content
                title = resume.get('title', '')
                filename = resume.get('filename', '')
                resume['content'] = f"{title} {filename} experienced professional with relevant skills and background"
            
            # Ensure text_content field exists (some agents may look for this)
            if 'text_content' not in resume:
                resume['text_content'] = resume['content']
            
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

@router.post(
    "/score-autogen/{job_id}",
    summary="Score resumes using AutoGen multi-agent orchestration",
    description="""
    Advanced resume scoring using AutoGen framework for collaborative agent analysis.
    
    **AutoGen Multi-Agent Orchestration:**
    This endpoint uses AutoGen's conversation-based approach where AI agents collaborate:
    
    - **Collaborative Analysis**: Agents discuss and build upon each other's insights
    - **Chain-of-Thought Reasoning**: Multi-step analysis with explicit reasoning
    - **Consensus Building**: Agents work together to reach final scoring decisions  
    - **Advanced Caching**: Results cached with 1-hour TTL for performance
    - **Fallback Support**: Graceful degradation to direct agent analysis if needed
    
    **Agent Participants:**
    - Keyword Analysis Agent
    - Skill Matching Agent  
    - Experience Relevance Agent
    - Education Alignment Agent
    - Semantic Similarity Agent
    - Coordinator Agent (synthesis)
    
    **Returns:**
    - Comprehensive multi-agent analysis
    - Final consensus score (0-100)
    - Individual agent contributions
    - Chat history and reasoning process
    """,
    response_model=ScoringResponse,
    responses={
        200: {"description": "Resumes scored successfully using AutoGen orchestration"},
        404: {"description": "Job not found"},
        500: {"description": "Internal server error during AutoGen analysis"}
    }
)
async def score_resumes_with_autogen(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """Score all user resumes against a job using AutoGen multi-agent orchestration."""
    
    try:
        # Get database
        db = get_database()
        
        # Validate job exists and get job details
        job = await db.jobs.find_one({"_id": job_id})
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get job description with fallback handling
        job_description = job.get("description", "").strip()
        job_skills = job.get("skills", [])
        
        if not job_description and not job_skills:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job has no description or skills to analyze against"
            )
        
        # Use skills as fallback if no description
        if not job_description and job_skills:
            job_description = f"Required skills: {', '.join(job_skills)}"
        
        # Get user's resumes
        resumes_cursor = await db.resumes.find({"user_id": current_user["_id"]})
        resumes = list(resumes_cursor)
        
        if not resumes:
            return []
        
        # Initialize AutoGen orchestrator
        autogen_orchestrator = get_autogen_orchestrator()
        
        scored_resumes = []
        
        for resume in resumes:
            try:
                # Get resume content with validation
                content = resume.get("content", "").strip()
                
                if not content:
                    # Skip resumes without content but don't fail entirely
                    print(f"⚠️  Skipping resume {resume['_id']} - no content")
                    continue
                
                # Use AutoGen orchestration for scoring
                print(f"🤖 AutoGen analyzing resume {resume['_id']}...")
                
                autogen_result = await autogen_orchestrator.orchestrate_analysis(
                    resume_content=content,
                    job_description=job_description,
                    job_skills=job_skills
                )
                
                if autogen_result["status"] in ["success", "success_fallback"]:
                    result_data = autogen_result["result"]
                    
                    # Extract final score
                    final_score = result_data.get("final_score", 0.0)
                    
                    # Debug: Print agent scores and skills analysis
                    print(f"🔍 DEBUG - Resume {resume['_id']} AutoGen Results:")
                    print(f"  Final Score: {final_score}")
                    
                    agent_analyses = result_data.get("agent_analyses", {})
                    for agent_name, analysis in agent_analyses.items():
                        if isinstance(analysis, dict) and 'score' in analysis:
                            print(f"  {agent_name}: {analysis['score']}")
                            if agent_name == "SkillAgent" and 'analysis_data' in analysis:
                                skills_data = analysis['analysis_data']
                                print(f"    Matched Skills: {skills_data.get('matched_skills', [])}")
                                print(f"    Missing Skills: {skills_data.get('missing_skills', [])}")
                                print(f"    Resume Skills Found: {len(skills_data.get('resume_skills_normalized', []))}")
                                print(f"    Job Skills Found: {len(skills_data.get('job_skills_normalized', []))}")
                    
                    print(f"  Skills Match from result: {result_data.get('skills_match', [])}")
                    print(f"  Missing Skills from result: {result_data.get('missing_skills', [])}")
                    print("---")
                    
                    # Create scoring result with AutoGen details
                    scoring_result = {
                        "_id": str(uuid.uuid4()),
                        "user_id": current_user["_id"],
                        "job_id": job_id,
                        "resume_id": str(resume["_id"]),
                        "overall_score": final_score,
                        "method": "autogen_orchestration",
                        "agent_analyses": result_data.get("agent_analyses", {}),
                        "summary": result_data.get("summary", ""),
                        "cached": autogen_result.get("cached", False),
                        "fallback_used": result_data.get("fallback_used", False),
                        "chat_history": autogen_result.get("chat_history", []),
                        "created_at": datetime.utcnow(),
                        "processing_time": 0  # AutoGen handles timing internally
                    }
                    
                    # Save scoring result
                    await db.scoring_results.insert_one(scoring_result)
                    
                    # Parse datetime strings if needed
                    try:
                        created_at = resume["created_at"]
                        if isinstance(created_at, str):
                            try:
                                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            except Exception as e1:
                                print(f"Warning: fromisoformat failed for '{created_at}': {e1}")
                                try:
                                    created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
                                except Exception as e2:
                                    print(f"Warning: strptime failed for '{created_at}': {e2}")
                                    created_at = datetime.utcnow()
                        
                        updated_at = resume.get("updated_at", resume["created_at"])
                        if isinstance(updated_at, str):
                            try:
                                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            except Exception as e1:
                                print(f"Warning: fromisoformat failed for updated_at '{updated_at}': {e1}")
                                try:
                                    updated_at = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S.%f')
                                except Exception as e2:
                                    print(f"Warning: strptime failed for updated_at '{updated_at}': {e2}")
                                    updated_at = created_at
                        elif updated_at == created_at and isinstance(created_at, datetime):
                            # If updated_at is the same string as created_at, use the parsed datetime
                            updated_at = created_at
                            
                    except Exception as dt_error:
                        print(f"Critical datetime parsing error: {dt_error}")
                        created_at = datetime.utcnow()
                        updated_at = created_at
                    
                    # Convert agent_analyses to score_breakdown format
                    score_breakdown = {}
                    agent_analyses = result_data.get("agent_analyses", {})
                    
                    agent_name_mapping = {
                        "KeywordAgent": "keyword_match",
                        "SkillAgent": "skills_alignment", 
                        "ExperienceAgent": "experience_relevance",
                        "EducationAgent": "education_alignment",
                        "SemanticAgent": "semantic_similarity"
                    }
                    
                    for agent_name, analysis in agent_analyses.items():
                        if isinstance(analysis, dict) and 'score' in analysis:
                            frontend_name = agent_name_mapping.get(agent_name, agent_name.lower())
                            score_breakdown[frontend_name] = {
                                "score": analysis.get('score', 0.0),
                                "percentage": analysis.get('percentage', analysis.get('score', 0.0) * 100),
                                "weight": analysis.get('weight', 0.2) * 100,  # Convert to percentage
                                "confidence": analysis.get('confidence'),
                                "evidence": analysis.get('evidence'),
                                "error": analysis.get('error')
                            }
                    
                    # Prepare response
                    resume_with_score = ResumeWithScore(
                        id=str(resume["_id"]),
                        title=resume["title"],
                        user_id=resume["user_id"],
                        filename=resume["filename"],
                        file_path=resume["file_path"],
                        file_size=resume["file_size"],
                        text_content=resume["text_content"],
                        file_hash=resume.get("file_hash"),
                        text_hash=resume.get("text_hash"),
                        skills=resume.get("skills", []),
                        experience_years=resume.get("experience_years"),
                        education=resume.get("education"),
                        created_at=created_at,
                        updated_at=updated_at,
                        score=final_score,
                        match_percentage=final_score * 100,
                        skills_match=result_data.get("skills_match", []),
                        missing_skills=result_data.get("missing_skills", []),
                        score_breakdown=score_breakdown
                    )
                    
                    scored_resumes.append(resume_with_score)
                    
                    print(f"✅ AutoGen scored resume {resume['_id']}: {final_score * 100:.1f}% (cached: {autogen_result.get('cached', False)})")
                
                else:
                    # AutoGen failed, log error but continue
                    error_msg = autogen_result.get("error", "Unknown AutoGen error")
                    print(f"❌ AutoGen failed for resume {resume['_id']}: {error_msg}")
                    
            except Exception as resume_error:
                # Log individual resume errors but continue processing
                print(f"❌ Error processing resume {resume['_id']} with AutoGen: {resume_error}")
                continue
        
        # Sort by score descending
        scored_resumes.sort(key=lambda x: x.score, reverse=True)
        
        return {
            "job": job,
            "scored_resumes": scored_resumes,
            "total_resumes": len(scored_resumes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ AutoGen scoring error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AutoGen scoring failed: {str(e)}"
        )
