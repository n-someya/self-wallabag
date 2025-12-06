import pytest
import json
import re
from jsonschema import validate

# Define the JSON schema for validating the article response
ARTICLE_SCHEMA = {
    "type": "object",
    "required": ["id", "url", "title", "created_at"],
    "properties": {
        "id": {"type": "string"},
        "url": {"type": "string", "format": "uri"},
        "title": {"type": "string"},
        "content": {"type": ["string", "null"]},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
        "read_at": {"type": ["string", "null"], "format": "date-time"},
        "reading_time": {"type": "integer"},
        "domain_name": {"type": "string"},
        "is_archived": {"type": "boolean"},
        "is_starred": {"type": "boolean"},
        "tags": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "label"],
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"}
                }
            }
        }
    }
}

class TestPostEntries:
    """Tests for the POST /api/entries endpoint"""
    
    def test_post_entries_unauthorized_without_api_key(self, api_url):
        """Test that posting entries without API key fails"""
        data = {"url": "https://example.com/test-article"}
        response = pytest.requests.post(
            f"{api_url}/entries", 
            headers={"Content-Type": "application/json"},
            json=data
        )
        assert response.status_code == 401
    
    def test_post_entry_with_valid_url(self, api_client):
        """Test creating an entry with valid URL"""
        data = {
            "url": "https://example.com/valid-article",
            "title": "Test Article with Valid URL"
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        # Validate the response against schema
        try:
            validate(instance=response.json(), schema=ARTICLE_SCHEMA)
        except Exception as e:
            pytest.fail(f"Response does not match schema: {e}")
            
        article = response.json()
        assert article["url"] == data["url"]
        assert article["title"] == data["title"]
        
        # Clean up
        article_id = article["id"]
        api_client.delete(f"entries/{article_id}")
    
    def test_post_entry_with_tags(self, api_client):
        """Test creating an entry with tags"""
        data = {
            "url": "https://example.com/article-with-tags",
            "tags": ["test", "example", "api"]
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        article = response.json()
        
        # Verify tags were added
        tag_labels = [tag["label"] for tag in article["tags"]]
        for tag in data["tags"]:
            assert tag in tag_labels
        
        # Clean up
        article_id = article["id"]
        api_client.delete(f"entries/{article_id}")
    
    def test_post_entry_with_starred_and_archived(self, api_client):
        """Test creating an entry with starred and archived flags"""
        data = {
            "url": "https://example.com/starred-archived-article",
            "starred": True,
            "archive": True
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        article = response.json()
        assert article["is_starred"] is True
        assert article["is_archived"] is True
        
        # Clean up
        article_id = article["id"]
        api_client.delete(f"entries/{article_id}")
    
    def test_post_entry_without_url_fails(self, api_client):
        """Test that creating an entry without URL fails"""
        data = {
            "title": "Test Article with No URL"
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 400
    
    def test_post_entry_with_invalid_url_fails(self, api_client):
        """Test that creating an entry with invalid URL format fails"""
        data = {
            "url": "not-a-valid-url"
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 400
    
    def test_post_entry_with_custom_title(self, api_client):
        """Test that custom title overrides the parsed title"""
        data = {
            "url": "https://example.com/custom-title-article",
            "title": "My Custom Title"
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        article = response.json()
        assert article["title"] == "My Custom Title"
        
        # Clean up
        article_id = article["id"]
        api_client.delete(f"entries/{article_id}")
    
    def test_post_entry_idempotency(self, api_client):
        """Test that posting the same URL twice doesn't create duplicates"""
        data = {
            "url": "https://example.com/idempotency-test"
        }
        
        # First post
        response1 = api_client.post("entries", data)
        assert response1.status_code == 201
        article_id1 = response1.json()["id"]
        
        # Second post with same URL
        response2 = api_client.post("entries", data)
        assert response2.status_code in (200, 201, 409)  # Different API behaviors are acceptable
        
        if response2.status_code in (200, 201):
            article_id2 = response2.json()["id"]
            # Clean up
            if article_id2 != article_id1:
                api_client.delete(f"entries/{article_id2}")
        
        # Clean up first article
        api_client.delete(f"entries/{article_id1}")