#!/usr/bin/env python3
"""
Database initialization script for PCARA
"""
import time
import os
from sqlalchemy import text
from database import engine, create_tables
from models import Base

def wait_for_db():
    """Wait for database to be ready"""
    max_retries = 30
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database is ready!")
            return True
        except Exception as e:
            print(f"Waiting for database... ({i+1}/{max_retries})")
            time.sleep(2)
    
    print("Database connection failed after maximum retries")
    return False

def init_database():
    """Initialize database tables"""
    if wait_for_db():
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database initialization complete!")
        return True
    return False

if __name__ == "__main__":
    init_database()