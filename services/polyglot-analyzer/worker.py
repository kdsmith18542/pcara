import redis
import json
import os
import shutil
import logging
from datetime import datetime
from polyglot_analyzer import PolyglotAnalyzer
from database_client import DatabaseClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolyglotAnalysisWorker:
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
        self.db_client = DatabaseClient()
        self.analyzer = PolyglotAnalyzer()
        self.temp_dir = "/tmp/repos"
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def run(self):
        """Main worker loop"""
        logger.info("Polyglot analyzer worker starting...")
        
        while True:
            try:
                # Wait for job from Redis queue - use different queue for polyglot analysis
                job_data = self.redis_client.brpop("polyglot_analysis_queue", timeout=10)
                
                if job_data:
                    job_info = json.loads(job_data[1])
                    self.process_job(job_info)
                    
            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
    
    def process_job(self, job_info):
        """Process a polyglot analysis job"""
        job_id = job_info["job_id"]
        repository_url = job_info["repository_url"]
        languages = job_info["languages"]
        
        logger.info(f"Processing polyglot analysis job {job_id} for repository {repository_url}")
        
        try:
            # Update job status to running
            self.db_client.update_job_status(job_id, "running", 10)
            
            # Clone repository
            repo_path = self.clone_repository(repository_url, job_id)
            self.db_client.update_job_status(job_id, "running", 30)
            
            # Perform polyglot analysis
            analysis_results = self.analyzer.analyze_cross_language_dependencies(
                repo_path, languages
            )
            self.db_client.update_job_status(job_id, "running", 80)
            
            # Store results
            self.store_results(job_id, analysis_results)
            self.db_client.update_job_status(job_id, "completed", 100, analysis_results)
            
            logger.info(f"Polyglot analysis job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing polyglot job {job_id}: {e}")
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
        """Store polyglot analysis results in database"""
        self.db_client.store_polyglot_results(job_id, analysis_results)
    
    def cleanup_repository(self, job_id):
        """Remove cloned repository"""
        repo_path = os.path.join(self.temp_dir, f"repo_{job_id}")
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            logger.info(f"Cleaned up repository for polyglot job {job_id}")

if __name__ == "__main__":
    worker = PolyglotAnalysisWorker()
    worker.run()