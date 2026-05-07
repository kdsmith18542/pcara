import redis
import json
import os
import shutil
import logging
from datetime import datetime
from go_analyzer import GoAnalyzer
from database_client import DatabaseClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoAnalysisWorker:
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
        self.db_client = DatabaseClient()
        self.analyzer = GoAnalyzer()
        self.temp_dir = "/tmp/repos"
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def run(self):
        """Main worker loop"""
        logger.info("Go analyzer worker starting...")
        
        while True:
            try:
                # Wait for job from Redis queue
                job_data = self.redis_client.brpop("analysis_queue", timeout=10)
                
                if job_data:
                    job_info = json.loads(job_data[1])
                    self.process_job(job_info)
                    
            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
    
    def process_job(self, job_info):
        """Process a single analysis job"""
        job_id = job_info["job_id"]
        repository_url = job_info["repository_url"]
        languages = job_info["languages"]
        analysis_types = job_info["analysis_types"]
        
        logger.info(f"Processing job {job_id} for repository {repository_url}")
        
        # Check if this worker can handle the requested languages
        if "go" not in languages:
            logger.info(f"Job {job_id} does not require Go analysis, skipping")
            return
        
        try:
            # Update job status to running
            self.db_client.update_job_status(job_id, "running", 10)
            
            # Clone repository
            repo_path = self.clone_repository(repository_url, job_id)
            self.db_client.update_job_status(job_id, "running", 30)
            
            # Analyze Go code
            analysis_results = self.analyzer.analyze_repository(
                repo_path, analysis_types
            )
            self.db_client.update_job_status(job_id, "running", 80)
            
            # Store results
            self.store_results(job_id, analysis_results)
            self.db_client.update_job_status(job_id, "completed", 100, analysis_results)
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            self.db_client.update_job_status(job_id, "failed", error_message=str(e))
        
        finally:
            # Cleanup
            self.cleanup_repository(job_id)
    
    def clone_repository(self, repository_url, job_id):
        """Clone repository to temporary directory"""
        from git import Repo
        
        repo_path = os.path.join(self.temp_dir, f"repo_{job_id}")
        
        # Remove if exists
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        
        # Clone repository
        Repo.clone_from(repository_url, repo_path)
        
        return repo_path
    
    def store_results(self, job_id, analysis_results):
        """Store analysis results in database"""
        self.db_client.store_analysis_results(job_id, analysis_results)
    
    def cleanup_repository(self, job_id):
        """Remove cloned repository"""
        repo_path = os.path.join(self.temp_dir, f"repo_{job_id}")
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            logger.info(f"Cleaned up repository for job {job_id}")

if __name__ == "__main__":
    worker = GoAnalysisWorker()
    worker.run()