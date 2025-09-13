from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_database
from app.models.user import UserCreate, UserLogin, UserResponse, Token
from app.core.security import verify_password, get_password_hash, create_access_token
from bson import ObjectId
import re
from datetime import datetime

router = APIRouter()
security = HTTPBearer()

@router.post(
    "/signup", 
    response_model=UserResponse,
    summary="Register a new user",
    description="""
    Register a new user account in the ATS system.
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter  
    - At least one number
    - At least one special character (@$!%*?&)
    
    **Email Validation:**
    - Must be a valid email format
    - Must be unique (not already registered)
    
    **Response:**
    Returns user information without the password hash.
    """,
    responses={
        200: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "id": "507f1f77bcf86cd799439011",
                        "email": "john.doe@example.com",
                        "full_name": "John Doe",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Bad request - Invalid input or email already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already registered"
                    }
                }
            }
        },
        422: {
            "description": "Validation error - Invalid email format or password requirements not met"
        }
    }
)
async def signup(user: UserCreate):
    try:
        db = get_database()
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least 8 characters, one uppercase, one lowercase, one number and one special character"
            )
        
        # Create user
        user_dict = user.dict()
        user_dict["hashed_password"] = get_password_hash(user.password)
        del user_dict["password"]
        
        # Add timestamps
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        
        result = await db.users.insert_one(user_dict)
        user_dict["_id"] = result["inserted_id"]
        
        # Return user without password
        return UserResponse(**user_dict)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post(
    "/login", 
    response_model=Token,
    summary="Authenticate user and get access token",
    description="""
    Authenticate a user with email and password to receive a JWT access token.
    
    **Authentication Process:**
    1. Validates email and password against stored user credentials
    2. Returns JWT token for authenticated requests
    3. Token expires after 30 minutes (configurable)
    
    **Usage:**
    Include the returned token in the Authorization header for protected endpoints:
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Security:**
    - Passwords are hashed using bcrypt
    - Tokens are signed with HS256 algorithm
    - Invalid credentials return 401 Unauthorized
    """,
    responses={
        200: {
            "description": "Authentication successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Authentication failed - Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect email or password"
                    }
                }
            }
        },
        422: {
            "description": "Validation error - Invalid email format"
        }
    }
)
async def login(user_credentials: UserLogin):
    try:
        db = get_database()
        
        # Find user
        user = await db.users.find_one({"email": user_credentials.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(user_credentials.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user["email"]})
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from app.core.security import verify_token
    
    try:
        token = credentials.credentials
        email = verify_token(token)
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        db = get_database()
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.get(
    "/me", 
    response_model=UserResponse,
    summary="Get current user information",
    description="""
    Retrieve information about the currently authenticated user.
    
    **Authentication Required:**
    This endpoint requires a valid JWT token in the Authorization header.
    
    **Response:**
    Returns the user's profile information including:
    - User ID
    - Email address
    - Full name
    - Account creation and update timestamps
    
    **Security:**
    - Password hash is never returned
    - Only returns data for the authenticated user
    """,
    responses={
        200: {
            "description": "User information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "507f1f77bcf86cd799439011",
                        "email": "john.doe@example.com",
                        "full_name": "John Doe",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid token"
                    }
                }
            }
        }
    }
)
async def get_current_user_info(current_user = Depends(get_current_user)):
    try:
        return UserResponse(**current_user)
    except Exception as e:
        print(f"Get user info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
