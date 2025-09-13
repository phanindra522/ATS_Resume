"""
Custom OpenAPI schema configuration for enhanced Swagger UI
"""

from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
from typing import Dict, Any

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced documentation
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints",
            "externalDocs": {
                "description": "JWT Authentication Guide",
                "url": "https://jwt.io/introduction",
            },
        },
        {
            "name": "Resumes",
            "description": "Resume management and processing endpoints",
            "externalDocs": {
                "description": "Document Processing Guide",
                "url": "https://docs.python.org/3/library/email.html",
            },
        },
        {
            "name": "Jobs",
            "description": "Job description management endpoints",
            "externalDocs": {
                "description": "Job Description Best Practices",
                "url": "https://www.indeed.com/hire/c/info/how-to-write-job-description",
            },
        },
        {
            "name": "Scoring",
            "description": "AI-powered resume scoring and analysis endpoints",
            "externalDocs": {
                "description": "Multi-Agent Architecture Guide",
                "url": "https://en.wikipedia.org/wiki/Multi-agent_system",
            },
        },
    ]
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token obtained from the /api/auth/login endpoint"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add custom info
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # Add contact information
    openapi_schema["info"]["contact"] = {
        "name": "ATS Resume Scoring Assistant",
        "email": "support@ats-scoring.com",
        "url": "https://github.com/your-org/ats-resume-scoring"
    }
    
    # Add license information
    openapi_schema["info"]["license"] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "Complete API Documentation",
        "url": "https://docs.ats-scoring.com"
    }
    
    # Add examples for common responses
    openapi_schema["components"]["examples"] = {
        "UserExample": {
            "summary": "User Object",
            "value": {
                "id": "507f1f77bcf86cd799439011",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        "TokenExample": {
            "summary": "JWT Token Response",
            "value": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huLmRvZUBleGFtcGxlLmNvbSIsImV4cCI6MTcwNDA2NzIwMH0.example",
                "token_type": "bearer"
            }
        },
        "ScoringResultExample": {
            "summary": "Scoring Result",
            "value": {
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
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def setup_custom_openapi(app: FastAPI):
    """
    Setup custom OpenAPI schema for the FastAPI app
    """
    app.openapi = lambda: custom_openapi(app)
