from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
import os
import PyPDF2  # Alternative PDF processing
from docx import Document
import numpy as np
import hashlib
from app.models.resume import ResumeCreate, ResumeResponse, ResumeUpdate
from app.database import get_database, get_chroma_collection
from app.routers.auth import get_current_user
from app.core.config import settings
import uuid

router = APIRouter()

# TODO: Replace with OpenAI embeddings when OpenAI integration is complete
def generate_placeholder_embedding(text: str, dimension: int = 1536) -> np.ndarray:
    """Generate a placeholder embedding for now - will be replaced with OpenAI"""
    return np.random.rand(dimension)

def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content for duplicate detection"""
    return hashlib.sha256(content).hexdigest()

def calculate_text_hash(text: str) -> str:
    """Calculate SHA-256 hash of text content for duplicate detection"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    title: str = None,
    description: str = None,
    current_user = Depends(get_current_user)
):
    """Upload a resume file"""
    
    # Validate file type
    allowed_extensions = [".pdf", ".docx"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed"
        )
    
    # Validate file size (10MB max)
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must be less than {settings.MAX_FILE_SIZE / (1024 * 1024)}MB"
        )
    
    try:
        # Read file content first for duplicate checking
        file_content = await file.read()
        
        # Calculate file hash for duplicate detection
        file_hash = calculate_file_hash(file_content)
        
        # Check for duplicate file upload (same content)
        db = get_database()
        existing_resume = await db.resumes.find_one({
            "user_id": current_user["_id"],
            "file_hash": file_hash
        })
        
        if existing_resume:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This resume file has already been uploaded. Duplicate uploads are not allowed."
            )
        
        # Create uploads directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Extract text content
        text_content = ""
        try:
            if file_extension.lower() == '.pdf':
                with open(file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()
            elif file_extension.lower() == '.docx':
                doc = Document(file_path)
                text_content = ""
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + "\n"
        except Exception as e:
            # If text extraction fails, still save the file but with empty content
            text_content = f"Text extraction failed: {str(e)}"
        
        # Calculate text hash for content-based duplicate detection
        text_hash = calculate_text_hash(text_content)
        
        # Check for duplicate content (even if file is different)
        if text_content and len(text_content) > 50:  # Only check if we have substantial text
            existing_content_resume = await db.resumes.find_one({
                "user_id": current_user["_id"],
                "text_hash": text_hash
            })
            
            if existing_content_resume:
                # Clean up the uploaded file since it's a duplicate
                os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A resume with identical content has already been uploaded. Duplicate content is not allowed."
                )
        
        # Generate placeholder embeddings (will be replaced with OpenAI)
        embeddings = generate_placeholder_embedding(text_content, settings.EMBEDDING_DIMENSION)
        
        # Store embeddings in ChromaDB
        chroma_collection = get_chroma_collection()
        if chroma_collection:
            try:
                chroma_collection.add(
                    embeddings=embeddings.tolist(),
                    documents=[text_content],
                    metadatas=[{"filename": filename, "user_id": current_user["_id"]}],
                    ids=[str(uuid.uuid4())]
                )
            except Exception as e:
                print(f"Warning: Could not store embeddings: {e}")
        
        # Create resume record with hash values
        resume_data = {
            "title": title or f"Resume - {file.filename}",
            "description": description or "Uploaded resume",
            "filename": filename,
            "file_path": file_path,
            "file_size": file.size,
            "content": text_content,
            "file_hash": file_hash,  # Store file hash
            "text_hash": text_hash,  # Store text hash
            "skills": [],  # Will be extracted later
            "experience_years": None,
            "education": None,
            "user_id": current_user["_id"]
        }
        
        # Save to database
        result = await db.resumes.insert_one(resume_data)
        
        # Fix: Use dictionary access for inserted_id
        resume_data["_id"] = result["inserted_id"]
        
        return ResumeResponse(**resume_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions (like duplicate detection)
        raise
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resume: {str(e)}"
        )

@router.get("/", response_model=List[ResumeResponse])
async def get_resumes(current_user = Depends(get_current_user)):
    """Get all resumes for the current user"""
    try:
        db = get_database()
        
        # Fix: Properly await the find operation and call to_list
        resumes_cursor = await db.resumes.find({"user_id": current_user["_id"]})
        resumes = await resumes_cursor.to_list(length=100)
        
        return [ResumeResponse(**resume) for resume in resumes]
        
    except Exception as e:
        print(f"Error getting resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resumes: {str(e)}"
        )

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str, current_user = Depends(get_current_user)):
    """Get a specific resume by ID"""
    db = get_database()
    resume = await db.resumes.find_one({
        "_id": resume_id,
        "user_id": current_user["_id"]
    })
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return ResumeResponse(**resume)

@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: str,
    resume_update: ResumeUpdate,
    current_user = Depends(get_current_user)
):
    """Update a resume"""
    db = get_database()
    
    # Check if resume exists and belongs to user
    existing_resume = await db.resumes.find_one({
        "_id": resume_id,
        "user_id": current_user["_id"]
    })
    
    if not existing_resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Update resume
    update_data = resume_update.dict(exclude_unset=True)
    
    await db.resumes.update_one(
        {"_id": resume_id},
        {"$set": update_data}
    )
    
    # Get updated resume
    updated_resume = await db.resumes.find_one({"_id": resume_id})
    return ResumeResponse(**updated_resume)

@router.delete("/{resume_id}")
async def delete_resume(resume_id: str, current_user = Depends(get_current_user)):
    """Delete a resume"""
    db = get_database()
    
    # Check if resume exists and belongs to user
    resume = await db.resumes.find_one({
        "_id": resume_id,
        "user_id": current_user["_id"]
    })
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Delete file from filesystem
    if os.path.exists(resume["file_path"]):
        os.remove(resume["file_path"])
    
    # Delete from database
    await db.resumes.delete_one({"_id": resume_id})
    
    return {"message": "Resume deleted successfully"}

@router.get("/check-duplicate/{filename}")
async def check_duplicate_resume(
    filename: str,
    current_user = Depends(get_current_user)
):
    """Check if a resume with similar content already exists"""
    db = get_database()
    
    # Check for exact filename match
    existing_resume = await db.resumes.find_one({
        "user_id": current_user["_id"],
        "filename": filename
    })
    
    if existing_resume:
        return {
            "is_duplicate": True,
            "message": "A resume with this filename already exists",
            "existing_resume": existing_resume["_id"]
        }
    
    return {
        "is_duplicate": False,
        "message": "No duplicate found"
    }