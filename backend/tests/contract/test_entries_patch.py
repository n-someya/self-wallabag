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

@pytest.fixture
def test_article(api_client):
    """Create a test article for update tests and return its ID"""
    data = {
        "url": "https://example.com/test-article-for-patch",
        "title": "Original Title",
        "tags": ["original-tag"],
        "starred": False,
        "archive": False
    }
    
    response = api_client.post("entries", data)
    article_id = response.json()["id"]
    
    yield article_id
    
    # Clean up
    api_client.delete(f"entries/{article_id}")

class TestPatchEntries:
    """Tests for the PATCH /api/entries/{id} endpoint"""
    
    def test_patch_entry_unauthorized_without_api_key(self, api_url, test_article):
        """Test that patching entries without API key fails"""
        data = {"title": "Updated Title"}
        response = pytest.requests.patch(
            f"{api_url}/entries/{test_article}", 
            headers={"Content-Type": "application/json"},
            json=data
        )
        assert response.status_code == 401
    
    def test_patch_entry_title(self, api_client, test_article):
        """Test updating an entry's title"""
        data = {"title": "Updated Title via PATCH"}
        
        response = api_client.patch(f"entries/{test_article}", data)
        assert response.status_code == 200
        
        # Validate the response against schema
        try:
            validate(instance=response.json(), schema=ARTICLE_SCHEMA)
        except Exception as e:
            pytest.fail(f"Response does not match schema: {e}")
            
        article = response.json()
        assert article["title"] == data["title"]
        
        # Verify the change persisted by getting the article
        get_response = api_client.get(f"entries/{test_article}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == data["title"]
    
    def test_patch_entry_tags(self, api_client, test_article):
        """Test updating an entry's tags"""
        data = {"tags": ["updated-tag1", "updated-tag2"]}
        
        response = api_client.patch(f"entries/{test_article}", data)
        assert response.status_code == 200
        
        article = response.json()
        
        # Verify tags were updated
        tag_labels = [tag["label"] for tag in article["tags"]]
        for tag in data["tags"]:
            assert tag in tag_labels
            
        # Verify the original tag is no longer present
        assert "original-tag" not in tag_labels
    
    def test_patch_entry_starred_status(self, api_client, test_article):
        """Test updating an entry's starred status"""
        # First, verify it's not starred
        get_response = api_client.get(f"entries/{test_article}")
        assert get_response.json()["is_starred"] is False
        
        # Update to starred
        data = {"starred": True}
        response = api_client.patch(f"entries/{test_article}", data)
        assert response.status_code == 200
        
        article = response.json()
        assert article["is_starred"] is True
        
        # Update back to not starred
        data = {"starred": False}
        response = api_client.patch(f"entries/{test_article}", data)
        assert response.status_code == 200
        
        article = response.json()
        assert article["is_starred"] is False
    
    def test_patch_entry_archive_status(self, api_client, test_article):
        """Test updating an entry's archive status"""
        # First, verify it's not archived
        get_response = api_client.get(f"entries/{test_article}")
        assert get_response.json()["is_archived"] is False
        
        # Update to archived
        data = {"archive": True}
        response = api_client.patch(f"entries/{test_article}", data)
        assert response.status_code == 200
        
        article = response.json()
        assert article["is_archived"] is True
        
        # Update back to not archived
        data = {"archive": False}
        response = api_client.patch(f"entries/{test_article}", data)
        assert response.status_code == 200
        
        article = response.json()
        assert article["is_archived"] is False
    
    def test_patch_entry_multiple_properties(self, api_client, test_article):
        """Test updating multiple properties at once"""
        data = {
            "title": "Multiple Updates Title",
            "tags": ["multi-update-tag"],
            "starred": True,
            "archive": True
        }
        
        response = api_client.patch(f"entries/{test_article}", data)
        assert response.status_code == 200
        
        article = response.json()
        assert article["title"] == data["title"]
        assert article["is_starred"] is True
        assert article["is_archived"] is True
        
        tag_labels = [tag["label"] for tag in article["tags"]]
        assert "multi-update-tag" in tag_labels
    
    def test_patch_nonexistent_entry(self, api_client):
        """Test patching a nonexistent entry"""
        data = {"title": "This Should Fail"}
        response = api_client.patch("entries/nonexistent-id", data)
        assert response.status_code == 404