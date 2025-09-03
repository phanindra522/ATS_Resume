from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database, get_chroma_collection
from app.models.resume import ResumeWithScore
from app.routers.auth import get_current_user
import numpy as np
from bson import ObjectId
import re
from datetime import datetime

router = APIRouter()

# TODO: Replace with OpenAI embeddings when OpenAI integration is complete
def generate_placeholder_embedding(text: str, dimension: int = 1536) -> np.ndarray:
    """Generate a placeholder embedding for now - will be replaced with OpenAI"""
    return np.random.rand(dimension)

def extract_skills(text):
    """Extract skills from text using common skill patterns"""
    # Common technical skills
    skills = [
        'python', 'javascript', 'java', 'react', 'node.js', 'mongodb', 'sql',
        'aws', 'docker', 'kubernetes', 'git', 'agile', 'scrum', 'machine learning',
        'data analysis', 'project management', 'ui/ux', 'figma', 'photoshop',
        'excel', 'powerpoint', 'word', 'salesforce', 'hubspot', 'marketing',
        'seo', 'content creation', 'social media', 'email marketing'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return found_skills

def calculate_similarity_score(resume_embedding, job_embedding):
    """Calculate cosine similarity between resume and job embeddings"""
    resume_vec = np.array(resume_embedding)
    job_vec = np.array(job_embedding)
    
    # Normalize vectors
    resume_norm = np.linalg.norm(resume_vec)
    job_norm = np.linalg.norm(job_vec)
    
    if resume_norm == 0 or job_norm == 0:
        return 0.0
    
    # Calculate cosine similarity
    similarity = np.dot(resume_vec, job_vec) / (resume_norm * job_norm)
    return float(similarity)

@router.post("/score/{job_id}")
async def score_resumes_for_job(
    job_id: str,
    current_user = Depends(get_current_user)
):
    db = get_database()
    
    # Get job description
    job = await db.jobs.find_one({
        "_id": ObjectId(job_id),
        "user_id": current_user["_id"]
    })
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get all resumes for the user
    resumes = await db.resumes.find({"user_id": current_user["_id"]}).to_list(length=100)
    
    if not resumes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resumes found"
        )
    
    # Generate placeholder job embedding (will be replaced with OpenAI)
    job_text = f"{job['title']} {job['company']} {job['description']} {' '.join(job['requirements'])} {' '.join(job['skills'])}"
    job_embedding = generate_placeholder_embedding(job_text)
    
    scored_resumes = []
    
    for resume in resumes:
        # Generate placeholder resume embedding (will be replaced with OpenAI)
        resume_text = f"{resume['title']} {resume['content']}"
        resume_embedding = generate_placeholder_embedding(resume_text)
        
        # Calculate similarity score
        similarity_score = calculate_similarity_score(resume_embedding, job_embedding)
        
        # Extract skills from resume
        resume_skills = extract_skills(resume['content'])
        job_skills = [skill.lower() for skill in job['skills']]
        
        # Calculate skills match
        skills_match = [skill for skill in resume_skills if skill.lower() in job_skills]
        missing_skills = [skill for skill in job_skills if skill not in [s.lower() for s in resume_skills]]
        
        # Calculate match percentage (placeholder for now)
        match_percentage = min(100.0, max(0.0, similarity_score * 100))
        
        scored_resume = {
            **resume,
            "score": similarity_score,
            "match_percentage": match_percentage,
            "skills_match": skills_match,
            "missing_skills": missing_skills
        }
        scored_resumes.append(scored_resume)
    
    # Sort by score (highest first)
    scored_resumes.sort(key=lambda x: x["score"], reverse=True)
    
    # Save scoring results
    scoring_result = {
        "user_id": current_user["_id"],
        "job_id": ObjectId(job_id),
        "scored_resumes": scored_resumes,
        "created_at": datetime.utcnow()
    }
    
    await db.scoring_results.insert_one(scoring_result)
    
    return {
        "job": job,
        "scored_resumes": [ResumeWithScore(**resume) for resume in scored_resumes]
    }

@router.get("/results/{job_id}")
async def get_scoring_results(job_id: str, current_user = Depends(get_current_user)):
    db = get_database()
    
    scoring_result = await db.scoring_results.find_one({
        "job_id": ObjectId(job_id),
        "user_id": current_user["_id"]
    }, sort=[("created_at", -1)])
    
    if not scoring_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scoring results found for this job"
        )
    
    return scoring_result

@router.get("/history")
async def get_scoring_history(current_user = Depends(get_current_user)):
    db = get_database()
    
    # Get scoring history with job details
    pipeline = [
        {"$match": {"user_id": current_user["_id"]}},
        {"$sort": {"created_at": -1}},
        {
            "$lookup": {
                "from": "jobs",
                "localField": "job_id",
                "foreignField": "_id",
                "as": "job"
            }
        },
        {"$unwind": "$job"},
        {
            "$project": {
                "scoring_id": "$_id",
                "job": "$job",
                "scored_resumes_count": {"$size": "$scored_resumes"},
                "created_at": "$created_at"
            }
        }
    ]
    
    history = await db.scoring_results.aggregate(pipeline).to_list(length=100)
    return history