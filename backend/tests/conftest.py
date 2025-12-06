import os
import pytest
import requests
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("TEST_WALLABAG_URL", "http://localhost:8080")
API_KEY = os.getenv("TEST_API_KEY", "testkey")
TEST_USERNAME = os.getenv("TEST_USERNAME", "wallabag")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "wallabag")
DB_HOST = os.getenv("TEST_DATABASE_HOST", "localhost")
DB_PORT = os.getenv("TEST_DATABASE_PORT", "5432")
DB_NAME = os.getenv("TEST_DATABASE_NAME", "wallabag")
DB_USER = os.getenv("TEST_DATABASE_USER", "wallabag")
DB_PASSWORD = os.getenv("TEST_DATABASE_PASSWORD", "wallabag")
API_VERSION = "api"  # Default API version

@pytest.fixture(scope="session")
def api_url():
    """Returns the base API URL"""
    return f"{BASE_URL}/{API_VERSION}"

@pytest.fixture(scope="session")
def headers():
    """Returns the common headers for API requests"""
    return {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

@pytest.fixture(scope="session")
def oauth_token():
    """Gets OAuth token for API access"""
    token_url = f"{BASE_URL}/oauth/v2/token"
    data = {
        "grant_type": "password",
        "client_id": "1_3o53gl30vhgk0c8ks4cocww08o8gw408sv8c00c0c8k8gwoo8c",  # Default client ID
        "client_secret": "636ocbqo978ckw0gsw4gcwwocg8044sco0w8w80wgscw448cgs",  # Default client secret
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        pytest.skip(f"Could not obtain OAuth token: {response.text}")

@pytest.fixture(scope="session")
def auth_headers(oauth_token):
    """Returns headers with OAuth token"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {oauth_token}"
    }

@pytest.fixture
def api_client(api_url, headers):
    """API client for making requests"""
    class ApiClient:
        def get(self, endpoint, params=None):
            url = f"{api_url}/{endpoint}"
            return requests.get(url, headers=headers, params=params)
            
        def post(self, endpoint, data):
            url = f"{api_url}/{endpoint}"
            return requests.post(url, headers=headers, json=data)
            
        def patch(self, endpoint, data):
            url = f"{api_url}/{endpoint}"
            return requests.patch(url, headers=headers, json=data)
            
        def delete(self, endpoint):
            url = f"{api_url}/{endpoint}"
            return requests.delete(url, headers=headers)
    
    return ApiClient()

@pytest.fixture
def create_test_article(api_client):
    """Creates a test article and returns its ID"""
    test_article_data = {
        "url": "https://example.com/test-article",
        "title": "Test Article",
        "tags": ["test", "pytest"],
        "starred": False,
        "archive": False
    }
    
    response = api_client.post("entries", test_article_data)
    
    if response.status_code == 201:
        article_id = response.json()["id"]
        yield article_id
        
        # Clean up after test
        api_client.delete(f"entries/{article_id}")
    else:
        pytest.skip(f"Could not create test article: {response.text}")

@pytest.fixture
def wait_for_service():
    """Wait for the service to be available"""
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            response = requests.get(BASE_URL, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
            
        time.sleep(retry_interval)
    
    pytest.skip("Service not available after waiting")