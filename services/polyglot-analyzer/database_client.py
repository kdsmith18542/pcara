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

class PolyglotDependency(Base):
    __tablename__ = "polyglot_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    source_file = Column(String, nullable=False)
    source_language = Column(String, nullable=False)
    target_file = Column(String)
    target_language = Column(String)
    dependency_type = Column(String, nullable=False)  # api_call, shared_resource, config, etc.
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default="now()")

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
    
    def store_polyglot_results(self, job_id: int, analysis_results: dict):
        """Store polyglot analysis results"""
        db = self.SessionLocal()
        try:
            # Store cross-language dependencies
            cross_deps = analysis_results.get("cross_language_dependencies", {})
            
            # Store API dependencies
            for api_dep in cross_deps.get("api_dependencies", []):
                dependency = PolyglotDependency(
                    job_id=job_id,
                    source_file=api_dep["source_file"],
                    source_language=api_dep["source_language"],
                    dependency_type="api_call",
                    metadata=api_dep
                )
                db.add(dependency)
            
            # Store shared resources
            for resource in cross_deps.get("shared_resources", []):
                for language in resource["referring_languages"]:
                    dependency = PolyglotDependency(
                        job_id=job_id,
                        source_file=resource["resource_path"],
                        source_language=language,
                        dependency_type="shared_resource",
                        metadata=resource
                    )
                    db.add(dependency)
            
            # Store configuration dependencies
            for config_dep in cross_deps.get("configuration_dependencies", []):
                dependency = PolyglotDependency(
                    job_id=job_id,
                    source_file=config_dep["source_file"],
                    source_language=config_dep["source_language"],
                    dependency_type="configuration",
                    metadata=config_dep
                )
                db.add(dependency)
            
            db.commit()
        finally:
            db.close()