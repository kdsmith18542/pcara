import redis
import json
from datetime import datetime
from typing import List
from models import AnalysisJob, Repository
from database import SessionLocal

class AnalysisService:
    def __init__(self):
        self.redis_client = redis.from_url("redis://redis:6379")
    
    def start_analysis(
        self,
        repository: Repository,
        languages: List[str],
        analysis_types: List[str],
        db: SessionLocal
    ) -> AnalysisJob:
        """Start a new analysis job"""
        
        # Create analysis job record
        job = AnalysisJob(
            repository_id=repository.id,
            status="pending",
            languages=languages,
            analysis_types=analysis_types,
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Queue the job for processing
        job_data = {
            "job_id": job.id,
            "repository_id": repository.id,
            "repository_url": repository.url,
            "languages": languages,
            "analysis_types": analysis_types
        }
        
        # Add to Redis queue for worker processing
        self.redis_client.lpush("analysis_queue", json.dumps(job_data))
        
        # If multiple languages are requested, also queue for polyglot analysis
        if len(languages) > 1:
            polyglot_job_data = {
                "job_id": job.id,
                "repository_id": repository.id,
                "repository_url": repository.url,
                "languages": languages
            }
            self.redis_client.lpush("polyglot_analysis_queue", json.dumps(polyglot_job_data))
        
        return job
    
    def update_job_status(self, job_id: int, status: str, progress: int = None, results: dict = None):
        """Update job status and progress"""
        db = SessionLocal()
        try:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job:
                job.status = status
                if progress is not None:
                    job.progress = progress
                if results is not None:
                    job.results = results
                if status == "completed":
                    job.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    
    def get_job_status(self, job_id: int) -> dict:
        """Get current job status"""
        db = SessionLocal()
        try:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job:
                return {
                    "job_id": job.id,
                    "status": job.status,
                    "progress": job.progress,
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                    "results": job.results
                }
            return None
        finally:
            db.close()