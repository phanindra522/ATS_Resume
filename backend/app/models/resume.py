from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ResumeBase(BaseModel):
    title: str
    description: Optional[str] = None

class ResumeCreate(ResumeBase):
    pass

class ResumeResponse(ResumeBase):
    id: str = Field(default="", alias="_id")
    user_id: str
    filename: str
    file_path: str
    file_size: int
    text_content: str  # Changed from 'content' to 'text_content' to match actual data
    file_hash: Optional[str] = None  # Add file hash
    text_hash: Optional[str] = None  # Add text hash
    skills: List[str] = []
    experience_years: Optional[int] = None
    education: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

class ResumeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    education: Optional[str] = None

class ResumeWithScore(ResumeResponse):
    score: float
    match_percentage: float
    skills_match: List[str]
    missing_skills: List[str]

class ResumeWithUserInfo(ResumeResponse):
    """Resume response with user information for global pool display"""
    user_name: Optional[str] = None
    user_email: Optional[str] = None