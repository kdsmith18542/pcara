from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
import logging

from database import get_db, SessionLocal
from models import User, Repository, AnalysisJob
from auth import create_access_token, verify_token
from analysis import AnalysisService
from rag import RAGService
from init_db import init_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database on startup
init_database()

app = FastAPI(
    title="PCARA API Gateway",
    description="Polyglot Codebase Analyzer & Refactor Assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class RepositoryCreate(BaseModel):
    name: str
    url: str
    description: Optional[str] = None

class AnalysisRequest(BaseModel):
    repository_id: int
    languages: List[str]
    analysis_types: List[str]

class RAGQuery(BaseModel):
    query: str
    repository_id: Optional[int] = None

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user_id

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication endpoints
@app.post("/auth/register")
async def register(user_data: UserCreate, db: SessionLocal = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user (password hashing handled in User model)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }

@app.post("/auth/login")
async def login(user_data: UserLogin, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }

# Repository management
@app.post("/repositories")
async def create_repository(
    repo_data: RepositoryCreate,
    user_id: int = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    repository = Repository(
        name=repo_data.name,
        url=repo_data.url,
        description=repo_data.description,
        user_id=user_id
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)
    
    return repository

@app.get("/repositories")
async def list_repositories(
    user_id: int = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    repositories = db.query(Repository).filter(Repository.user_id == user_id).all()
    return repositories

@app.get("/repositories/{repository_id}")
async def get_repository(
    repository_id: int,
    user_id: int = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    repository = db.query(Repository).filter(
        Repository.id == repository_id,
        Repository.user_id == user_id
    ).first()
    
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return repository

# Analysis endpoints
@app.post("/analysis")
async def start_analysis(
    analysis_request: AnalysisRequest,
    user_id: int = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    # Verify repository ownership
    repository = db.query(Repository).filter(
        Repository.id == analysis_request.repository_id,
        Repository.user_id == user_id
    ).first()
    
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Create analysis job
    analysis_service = AnalysisService()
    job = analysis_service.start_analysis(
        repository=repository,
        languages=analysis_request.languages,
        analysis_types=analysis_request.analysis_types,
        db=db
    )
    
    return {"job_id": job.id, "status": job.status}

@app.get("/analysis/{job_id}")
async def get_analysis_status(
    job_id: int,
    user_id: int = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    # Verify ownership through repository
    if job.repository.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "results": job.results
    }

# RAG endpoints
@app.post("/rag/query")
async def rag_query(
    query_data: RAGQuery,
    user_id: int = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    rag_service = RAGService()
    
    # If repository_id is provided, verify ownership
    repository = None
    if query_data.repository_id:
        repository = db.query(Repository).filter(
            Repository.id == query_data.repository_id,
            Repository.user_id == user_id
        ).first()
        
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")
    
    response = await rag_service.query(
        query=query_data.query,
        repository=repository,
        user_id=user_id
    )
    
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)