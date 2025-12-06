import pytest
import json

@pytest.fixture
def create_article(api_client):
    """Create a test article and return its ID"""
    data = {
        "url": "https://example.com/test-article-for-delete",
        "title": "Article to Delete"
    }
    
    response = api_client.post("entries", data)
    assert response.status_code == 201
    article_id = response.json()["id"]
    
    yield article_id
    
    # Verify the article was deleted or clean up if needed
    check_response = api_client.get(f"entries/{article_id}")
    if check_response.status_code != 404:
        api_client.delete(f"entries/{article_id}")

class TestDeleteEntries:
    """Tests for the DELETE /api/entries/{id} endpoint"""
    
    def test_delete_entry_unauthorized_without_api_key(self, api_url, create_article):
        """Test that deleting entries without API key fails"""
        response = pytest.requests.delete(f"{api_url}/entries/{create_article}")
        assert response.status_code == 401
    
    def test_delete_entry_success(self, api_client, create_article):
        """Test successfully deleting an entry"""
        # First, verify the article exists
        get_response = api_client.get(f"entries/{create_article}")
        assert get_response.status_code == 200
        
        # Delete the article
        delete_response = api_client.delete(f"entries/{create_article}")
        assert delete_response.status_code == 204
        
        # Verify the article was deleted
        get_after_delete = api_client.get(f"entries/{create_article}")
        assert get_after_delete.status_code == 404
    
    def test_delete_entry_twice(self, api_client, create_article):
        """Test deleting the same entry twice"""
        # First deletion should succeed
        delete_response = api_client.delete(f"entries/{create_article}")
        assert delete_response.status_code == 204
        
        # Second deletion should return 404
        delete_again = api_client.delete(f"entries/{create_article}")
        assert delete_again.status_code == 404
    
    def test_delete_nonexistent_entry(self, api_client):
        """Test deleting a nonexistent entry"""
        response = api_client.delete("entries/nonexistent-id")
        assert response.status_code == 404
    
    def test_delete_then_get(self, api_client, create_article):
        """Test getting an article after deleting it"""
        # Delete the article
        delete_response = api_client.delete(f"entries/{create_article}")
        assert delete_response.status_code == 204
        
        # Try to get the article
        get_response = api_client.get(f"entries/{create_article}")
        assert get_response.status_code == 404
    
    def test_delete_then_update(self, api_client, create_article):
        """Test updating an article after deleting it"""
        # Delete the article
        delete_response = api_client.delete(f"entries/{create_article}")
        assert delete_response.status_code == 204
        
        # Try to update the article
        data = {"title": "This Should Fail"}
        update_response = api_client.patch(f"entries/{create_article}", data)
        assert update_response.status_code == 404