import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    status = Column(String, default="pending")
    progress = Column(Integer, default=0)
    languages = Column(JSON)
    analysis_types = Column(JSON)
    results = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    file_path = Column(String, nullable=False)
    language = Column(String, nullable=False)
    analysis_type = Column(String, nullable=False)
    results = Column(JSON)

class DatabaseClient:
    def __init__(self):
        database_url = os.getenv("DATABASE_URL", "postgresql://pcara_user:pcara_dev_password@postgres:5432/pcara_dev")
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def update_job_status(self, job_id: int, status: str, progress: int = None, results: dict = None, error_message: str = None):
        """Update job status in database"""
        db = self.SessionLocal()
        try:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job:
                job.status = status
                if progress is not None:
                    job.progress = progress
                if results is not None:
                    job.results = results
                if error_message is not None:
                    job.error_message = error_message
                if status == "completed":
                    job.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    
    def store_analysis_results(self, job_id: int, analysis_results: dict):
        """Store detailed analysis results"""
        db = self.SessionLocal()
        try:
            # Store results for each file
            for analysis_type, type_results in analysis_results.get("analysis_results", {}).items():
                if "file_stats" in type_results:
                    for file_path, file_results in type_results["file_stats"].items():
                        result = AnalysisResult(
                            job_id=job_id,
                            file_path=file_path,
                            language="go",
                            analysis_type=analysis_type,
                            results=file_results
                        )
                        db.add(result)
            
            db.commit()
        finally:
            db.close()