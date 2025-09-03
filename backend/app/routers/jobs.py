from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
import json
import PyPDF2
from docx import Document
import io
from app.database import get_database
from app.models.job import JobCreate, JobResponse, JobUpdate
from app.routers.auth import get_current_user
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    current_user = Depends(get_current_user)
):
    db = get_database()
    
    job_data = job.dict()
    job_data["user_id"] = current_user["_id"]
    job_data["created_at"] = datetime.utcnow()
    job_data["updated_at"] = datetime.utcnow()
    
    result = await db.jobs.insert_one(job_data)
    
    # Fix: Use dictionary access for inserted_id
    job_data["_id"] = result["inserted_id"]
    
    return JobResponse(**job_data)

@router.post("/upload", response_model=JobResponse)
async def upload_job_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    company: str = Form(...),
    description: Optional[str] = Form(""),
    requirements: Optional[str] = Form(""),
    skills: Optional[str] = Form(""),
    experience_level: Optional[str] = Form(""),
    location: Optional[str] = Form(""),
    salary_range: Optional[str] = Form(""),
    current_user = Depends(get_current_user)
):
    """Upload a job description file and create job"""
    
    # Validate file type
    allowed_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF, TXT, and DOCX files are allowed."
        )
    
    # Validate file size (10MB max)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 10MB"
        )
    
    try:
        # Extract text content from file
        file_content = await file.read()
        extracted_text = ""
        
        if file.content_type == "application/pdf":
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
                
        elif file.content_type == "text/plain":
            # Extract text from TXT file
            extracted_text = file_content.decode('utf-8')
            
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Extract text from DOCX file
            doc = Document(io.BytesIO(file_content))
            for paragraph in doc.paragraphs:
                extracted_text += paragraph.text + "\n"
        
        # Clean up extracted text
        extracted_text = extracted_text.strip()
        
        # If no description provided, use extracted text
        if not description and extracted_text:
            description = extracted_text[:2000]  # Limit to 2000 characters
        
        # Parse requirements and skills from form data
        requirements_list = []
        if requirements:
            try:
                requirements_list = json.loads(requirements)
            except json.JSONDecodeError:
                # Fallback: split by newlines if JSON parsing fails
                requirements_list = [req.strip() for req in requirements.split('\n') if req.strip()]
        
        skills_list = []
        if skills:
            try:
                skills_list = json.loads(skills)
            except json.JSONDecodeError:
                # Fallback: split by commas if JSON parsing fails
                skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        
        # Create job data
        job_data = {
            "title": title,
            "company": company,
            "description": description,
            "requirements": requirements_list,
            "skills": skills_list,
            "experience_level": experience_level or None,
            "location": location or None,
            "salary_range": salary_range or None,
            "user_id": current_user["_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Save to database
        db = get_database()
        result = await db.jobs.insert_one(job_data)
        
        # Fix: Use dictionary access for inserted_id
        job_data["_id"] = result["inserted_id"]
        
        return JobResponse(**job_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )

@router.get("/", response_model=List[JobResponse])
async def get_jobs(current_user = Depends(get_current_user)):
    """Get all jobs for the current user"""
    try:
        db = get_database()
        
        # Fix: Properly await the find operation and call to_list
        jobs_cursor = await db.jobs.find({"user_id": current_user["_id"]})
        jobs = await jobs_cursor.to_list(length=100)
        
        return [JobResponse(**job) for job in jobs]
        
    except Exception as e:
        print(f"Error getting jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}"
        )

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, current_user = Depends(get_current_user)):
    """Get a specific job by ID"""
    try:
        db = get_database()
        job = await db.jobs.find_one({
            "_id": job_id,
            "user_id": current_user["_id"]
        })
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return JobResponse(**job)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job: {str(e)}"
        )

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    current_user = Depends(get_current_user)
):
    """Update a job description"""
    try:
        db = get_database()
        
        # Check if job exists and belongs to user
        existing_job = await db.jobs.find_one({
            "_id": job_id,
            "user_id": current_user["_id"]
        })
        
        if not existing_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Update job
        update_data = job_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await db.jobs.update_one(
            {"_id": job_id},
            {"$set": update_data}
        )
        
        # Get updated job
        updated_job = await db.jobs.find_one({"_id": job_id})
        return JobResponse(**updated_job)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job: {str(e)}"
        )

@router.delete("/{job_id}")
async def delete_job(job_id: str, current_user = Depends(get_current_user)):
    """Delete a job description"""
    try:
        db = get_database()
        
        # Check if job exists and belongs to user
        job = await db.jobs.find_one({
            "_id": job_id,
            "user_id": current_user["_id"]
        })
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Delete from database
        await db.jobs.delete_one({"_id": job_id})
        
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )
