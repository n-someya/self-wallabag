import pytest
import json
import re
from jsonschema import validate

# Define the JSON schema for validating the entries response
ENTRIES_SCHEMA = {
    "type": "object",
    "required": ["page", "limit", "pages", "total", "_embedded"],
    "properties": {
        "page": {"type": "integer"},
        "limit": {"type": "integer"},
        "pages": {"type": "integer"},
        "total": {"type": "integer"},
        "_embedded": {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "url"],
                        "properties": {
                            "id": {"type": "string"},
                            "url": {"type": "string"},
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
                }
            }
        }
    }
}

@pytest.fixture
def setup_test_articles(api_client):
    """Create test articles for testing GET requests"""
    # Create a few articles for testing
    test_articles = [
        {"url": "https://example.com/test1", "title": "Test Article 1", "tags": ["test1"]},
        {"url": "https://example.com/test2", "title": "Test Article 2", "tags": ["test2"]},
        {"url": "https://example.com/test3", "title": "Test Article 3", "starred": True}
    ]
    
    article_ids = []
    for article in test_articles:
        response = api_client.post("entries", article)
        if response.status_code == 201:
            article_ids.append(response.json()["id"])
    
    yield article_ids
    
    # Clean up created articles
    for article_id in article_ids:
        api_client.delete(f"entries/{article_id}")

class TestGetEntries:
    """Tests for the GET /api/entries endpoint"""
    
    @pytest.mark.dependency()
    def test_get_entries_unauthorized_without_api_key(self, api_url):
        """Test that accessing entries without API key fails"""
        response = pytest.requests.get(f"{api_url}/entries")
        assert response.status_code == 401
    
    def test_get_entries_schema_validation(self, api_client, setup_test_articles):
        """Test that the response schema matches the API contract"""
        response = api_client.get("entries")
        assert response.status_code == 200
        
        # Validate response against schema
        try:
            validate(instance=response.json(), schema=ENTRIES_SCHEMA)
        except Exception as e:
            pytest.fail(f"Response does not match schema: {e}")
    
    def test_get_entries_pagination(self, api_client, setup_test_articles):
        """Test pagination parameters"""
        # Test with page=1, perPage=2
        response = api_client.get("entries", params={"page": 1, "perPage": 2})
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["limit"] == 2
        assert len(data["_embedded"]["items"]) <= 2
        
        # Test with page=2, perPage=1
        response = api_client.get("entries", params={"page": 2, "perPage": 1})
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert data["limit"] == 1
        assert len(data["_embedded"]["items"]) <= 1
    
    def test_get_entries_filtering_by_archived(self, api_client, setup_test_articles):
        """Test filtering by archived status"""
        # Archive one article
        if setup_test_articles:
            api_client.patch(f"entries/{setup_test_articles[0]}", {"archive": True})
        
        # Get only archived articles
        response = api_client.get("entries", params={"archive": 1})
        assert response.status_code == 200
        data = response.json()
        
        for item in data["_embedded"]["items"]:
            assert item["is_archived"] is True
    
    def test_get_entries_filtering_by_starred(self, api_client, setup_test_articles):
        """Test filtering by starred status"""
        # Get only starred articles
        response = api_client.get("entries", params={"starred": 1})
        assert response.status_code == 200
        data = response.json()
        
        for item in data["_embedded"]["items"]:
            assert item["is_starred"] is True
    
    def test_get_entries_filtering_by_tags(self, api_client, setup_test_articles):
        """Test filtering by tags"""
        response = api_client.get("entries", params={"tags": "test1"})
        assert response.status_code == 200
        data = response.json()
        
        for item in data["_embedded"]["items"]:
            has_tag = False
            for tag in item["tags"]:
                if tag["label"] == "test1":
                    has_tag = True
                    break
            assert has_tag
    
    def test_get_entries_sorting(self, api_client, setup_test_articles):
        """Test sorting parameters"""
        sort_fields = ["created", "updated", "archived"]
        sort_orders = ["asc", "desc"]
        
        for field in sort_fields:
            for order in sort_orders:
                response = api_client.get("entries", params={"sort": field, "order": order})
                assert response.status_code == 200