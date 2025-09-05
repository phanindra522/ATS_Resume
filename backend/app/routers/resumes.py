from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
import os
import PyPDF2  # Alternative PDF processing
from docx import Document
import numpy as np
import hashlib
from app.models.resume import ResumeCreate, ResumeResponse, ResumeUpdate, ResumeWithUserInfo
from app.database import get_database, get_chroma_collection
from app.routers.auth import get_current_user
from app.core.config import settings
import uuid

router = APIRouter()

def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding using configured LLM provider"""
    try:
        if settings.LLM_PROVIDER.lower() == "openai":
            return generate_openai_embedding(text)
        elif settings.LLM_PROVIDER.lower() == "gemini":
            return generate_gemini_embedding(text)
        else:
            # Fallback to placeholder for other providers
            return generate_placeholder_embedding(text, settings.EMBEDDING_DIMENSION)
    except Exception as e:
        print(f"Embedding generation failed: {e}, using placeholder")
        return generate_placeholder_embedding(text, settings.EMBEDDING_DIMENSION)

def generate_openai_embedding(text: str) -> np.ndarray:
    """Generate embedding using OpenAI"""
    try:
        import openai
        client = openai.OpenAI(api_key=settings.LLM_PROVIDER_API_KEY)  # Use sync client
        response = client.embeddings.create(
            model=settings.LLM_EMBEDDING_MODEL,
            input=text
        )
        return np.array(response.data[0].embedding)
    except Exception as e:
        raise Exception(f"OpenAI embedding error: {str(e)}")

def generate_gemini_embedding(text: str) -> np.ndarray:
    """Generate embedding using Google Gemini"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.LLM_PROVIDER_API_KEY)
        result = genai.embed_content(
            model=settings.LLM_EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )
        return np.array(result['embedding'])
    except Exception as e:
        raise Exception(f"Gemini embedding error: {str(e)}")

def generate_placeholder_embedding(text: str, dimension: int = None) -> np.ndarray:
    """Generate a placeholder embedding for fallback"""
    if dimension is None:
        dimension = settings.EMBEDDING_DIMENSION
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
        
        # Generate embeddings using configured LLM provider
        embeddings = generate_embedding(text_content)
        
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
            "text_content": text_content,  # Fixed: use text_content instead of content
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

@router.get("/", response_model=List[ResumeWithUserInfo])
async def get_resumes(current_user = Depends(get_current_user)):
    """Get all resumes from the global pool (all recruiters can see all resumes)"""
    try:
        db = get_database()
        
        # Global pool: Get all resumes from all users
        resumes_cursor = await db.resumes.find({})
        resumes = await resumes_cursor.to_list(length=1000)  # Increased limit for global pool
        
        # Get user information for each resume
        resumes_with_user_info = []
        for resume in resumes:
            # Get user information
            user = await db.users.find_one({"_id": resume["user_id"]})
            user_name = user["full_name"] if user else "Unknown User"
            user_email = user["email"] if user else "unknown@example.com"
            
            # Create resume with user info
            resume_data = resume.copy()
            resume_data["user_name"] = user_name
            resume_data["user_email"] = user_email
            
            resumes_with_user_info.append(ResumeWithUserInfo(**resume_data))
        
        return resumes_with_user_info
        
    except Exception as e:
        print(f"Error getting resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resumes: {str(e)}"
        )

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str, current_user = Depends(get_current_user)):
    """Get a specific resume by ID from the global pool"""
    db = get_database()
    resume = await db.resumes.find_one({
        "_id": resume_id
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

@router.delete("/{resume_id}")
async def delete_resume(resume_id: str, current_user = Depends(get_current_user)):
    """Delete a resume by ID"""
    try:
        db = get_database()
        
        # Check if resume exists and belongs to the user
        resume = await db.resumes.find_one({
            "_id": resume_id,
            "user_id": current_user["_id"]
        })
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or you don't have permission to delete it"
            )
        
        # Delete the resume
        result = await db.resumes.delete_one({"_id": resume_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Also remove from ChromaDB if it exists
        try:
            chroma_collection = get_chroma_collection()
            if chroma_collection:
                # Remove document from ChromaDB
                chroma_collection.delete(ids=[resume_id])
        except Exception as e:
            print(f"Warning: Could not remove resume from ChromaDB: {e}")
        
        # Delete the physical file if it exists
        try:
            if 'file_path' in resume and resume['file_path']:
                file_path = os.path.join(settings.UPLOAD_DIR, resume['file_path'])
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Warning: Could not delete physical file: {e}")
        
        return {
            "message": "Resume deleted successfully",
            "deleted_resume_id": resume_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resume: {str(e)}"
        )