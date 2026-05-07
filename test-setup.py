#!/usr/bin/env python3
"""
PCARA Setup Test Script
Tests basic functionality of the development environment
"""

import requests
import time
import json
import sys

def test_api_health():
    """Test API Gateway health endpoint"""
    try:
        response = requests.get("http://localhost:8081/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Gateway health check passed")
            return True
        else:
            print(f"❌ API Gateway health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Gateway connection failed: {e}")
        return False

def test_user_registration():
    """Test user registration endpoint"""
    try:
        user_data = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "testpassword123"
        }
        
        response = requests.post(
            "http://localhost:8081/auth/register",
            json=user_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ User registration test passed")
            return response.json()
        else:
            print(f"❌ User registration test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ User registration test failed: {e}")
        return None

def test_repository_creation(auth_token):
    """Test repository creation"""
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        repo_data = {
            "name": "test-repo",
            "url": "https://github.com/octocat/Hello-World",
            "description": "Test repository for PCARA"
        }
        
        response = requests.post(
            "http://localhost:8081/repositories",
            json=repo_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Repository creation test passed")
            return response.json()
        else:
            print(f"❌ Repository creation test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Repository creation test failed: {e}")
        return None

def test_analysis_start(auth_token, repository_id):
    """Test analysis job creation"""
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        analysis_data = {
            "repository_id": repository_id,
            "languages": ["python"],
            "analysis_types": ["syntax_analysis", "complexity_analysis"]
        }
        
        response = requests.post(
            "http://localhost:8081/analysis",
            json=analysis_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Analysis job creation test passed")
            return response.json()
        else:
            print(f"❌ Analysis job creation test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Analysis job creation test failed: {e}")
        return None

def main():
    print("🧪 PCARA Setup Test Suite")
    print("=" * 40)
    
    # Wait for services to be ready
    print("⏳ Waiting for services to start...")
    time.sleep(5)
    
    # Test API health
    if not test_api_health():
        print("\n❌ API Gateway is not responding. Please check if services are running.")
        sys.exit(1)
    
    # Test user registration
    user_response = test_user_registration()
    if not user_response:
        print("\n❌ User registration failed. Check database connection.")
        sys.exit(1)
    
    auth_token = user_response.get("access_token")
    if not auth_token:
        print("❌ No access token received from registration")
        sys.exit(1)
    
    # Test repository creation
    repo_response = test_repository_creation(auth_token)
    if not repo_response:
        print("\n❌ Repository creation failed.")
        sys.exit(1)
    
    repository_id = repo_response.get("id")
    if not repository_id:
        print("❌ No repository ID received")
        sys.exit(1)
    
    # Test analysis job creation
    analysis_response = test_analysis_start(auth_token, repository_id)
    if not analysis_response:
        print("\n❌ Analysis job creation failed.")
        sys.exit(1)
    
    print("\n🎉 All tests passed! PCARA is working correctly.")
    print("\n📋 Test Results Summary:")
    print(f"   • User ID: {user_response.get('user', {}).get('id')}")
    print(f"   • Repository ID: {repository_id}")
    print(f"   • Analysis Job ID: {analysis_response.get('job_id')}")
    
    print("\n🌐 You can now access PCARA at http://localhost:3001")

if __name__ == "__main__":
    main()