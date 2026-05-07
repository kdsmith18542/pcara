from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext
from database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    repositories = relationship("Repository", back_populates="owner")
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.hashed_password = pwd_context.hash(password)
    
    def verify_password(self, password):
        return pwd_context.verify(password, self.hashed_password)

class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="repositories")
    analysis_jobs = relationship("AnalysisJob", back_populates="repository")

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    languages = Column(JSON)  # List of languages to analyze
    analysis_types = Column(JSON)  # List of analysis types requested
    results = Column(JSON)  # Analysis results
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    repository = relationship("Repository", back_populates="analysis_jobs")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    file_path = Column(String, nullable=False)
    language = Column(String, nullable=False)
    analysis_type = Column(String, nullable=False)
    results = Column(JSON)  # Detailed analysis results
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Dependency(Base):
    __tablename__ = "dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    source_file = Column(String, nullable=False)
    source_language = Column(String, nullable=False)
    target_file = Column(String, nullable=False)
    target_language = Column(String, nullable=False)
    dependency_type = Column(String, nullable=False)  # import, call, inheritance, etc.
    metadata = Column(JSON)  # Additional dependency information
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PolyglotDependency(Base):
    __tablename__ = "polyglot_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    source_file = Column(String, nullable=False)
    source_language = Column(String, nullable=False)
    target_file = Column(String)
    target_language = Column(String)
    dependency_type = Column(String, nullable=False)  # api_call, shared_resource, config, etc.
    metadata = Column(JSON)  # Cross-language dependency information
    created_at = Column(DateTime(timezone=True), server_default=func.now())