import pytest
import json
from datetime import datetime, timedelta
from jsonschema import validate

# Define the JSON schema for validating the API key creation response
API_KEY_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["id", "key", "name", "created_at", "is_active"],
    "properties": {
        "id": {"type": "string"},
        "key": {"type": "string"},
        "name": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "expires_at": {"type": ["string", "null"], "format": "date-time"},
        "is_active": {"type": "boolean"}
    }
}

class TestPostApiKeys:
    """Tests for the POST /api-keys endpoint"""
    
    def test_post_api_key_unauthorized_without_api_key(self, api_url):
        """Test that creating API keys without API key fails"""
        data = {"name": "Unauthorized Key"}
        response = pytest.requests.post(
            f"{api_url}/api-keys", 
            headers={"Content-Type": "application/json"},
            json=data
        )
        assert response.status_code == 401
    
    def test_post_api_key_with_name_only(self, api_client):
        """Test creating an API key with only a name"""
        data = {"name": "Test Key with Name Only"}
        
        response = api_client.post("api-keys", data)
        assert response.status_code == 201
        
        # Validate the response against schema
        try:
            validate(instance=response.json(), schema=API_KEY_RESPONSE_SCHEMA)
        except Exception as e:
            pytest.fail(f"Response does not match schema: {e}")
            
        api_key = response.json()
        assert api_key["name"] == data["name"]
        assert api_key["is_active"] is True
        assert api_key["expires_at"] is None
        
        # Verify the key is present
        assert "key" in api_key
        assert len(api_key["key"]) >= 32
        
        # Clean up
        api_client.delete(f"api-keys/{api_key['id']}")
    
    def test_post_api_key_with_expiration(self, api_client):
        """Test creating an API key with an expiration date"""
        # Set expiration 7 days in the future
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        data = {
            "name": "Test Key with Expiration",
            "expires_at": expires_at
        }
        
        response = api_client.post("api-keys", data)
        assert response.status_code == 201
        
        api_key = response.json()
        assert api_key["name"] == data["name"]
        assert api_key["expires_at"] is not None
        
        # Clean up
        api_client.delete(f"api-keys/{api_key['id']}")
    
    def test_post_api_key_without_name_fails(self, api_client):
        """Test that creating an API key without a name fails"""
        data = {}  # Missing required name
        
        response = api_client.post("api-keys", data)
        assert response.status_code == 400
    
    def test_post_api_key_then_list(self, api_client):
        """Test creating an API key and then verifying it appears in the list"""
        data = {"name": "Test Key for Listing"}
        
        # Create the key
        response = api_client.post("api-keys", data)
        assert response.status_code == 201
        
        api_key = response.json()
        key_id = api_key["id"]
        
        # List keys and verify the new one is included
        list_response = api_client.get("api-keys")
        assert list_response.status_code == 200
        
        api_keys = list_response.json()
        key_ids = [key["id"] for key in api_keys]
        
        assert key_id in key_ids
        
        # Clean up
        api_client.delete(f"api-keys/{key_id}")
    
    def test_post_duplicate_api_key_names(self, api_client):
        """Test creating API keys with duplicate names is allowed"""
        data = {"name": "Duplicate Name Key"}
        
        # Create first key
        response1 = api_client.post("api-keys", data)
        assert response1.status_code == 201
        key_id1 = response1.json()["id"]
        
        # Create second key with same name
        response2 = api_client.post("api-keys", data)
        assert response2.status_code == 201
        key_id2 = response2.json()["id"]
        
        # Verify both have the same name but different IDs
        assert key_id1 != key_id2
        assert response1.json()["name"] == response2.json()["name"]
        
        # Clean up
        api_client.delete(f"api-keys/{key_id1}")
        api_client.delete(f"api-keys/{key_id2}")
    
    def test_post_api_key_shows_key_only_once(self, api_client):
        """Test that the API key value is only shown once upon creation"""
        data = {"name": "One-time Key"}
        
        # Create the key
        response = api_client.post("api-keys", data)
        assert response.status_code == 201
        api_key = response.json()
        key_id = api_key["id"]
        key_value = api_key["key"]
        
        # The key value should be present in the creation response
        assert key_value is not None
        assert len(key_value) >= 32
        
        # Get the key by listing all keys
        list_response = api_client.get("api-keys")
        assert list_response.status_code == 200
        
        # Find the key in the list
        found_key = None
        for key in list_response.json():
            if key["id"] == key_id:
                found_key = key
                break
        
        assert found_key is not None
        assert "key" not in found_key  # Key value should not be included in GET responses
        
        # Clean up
        api_client.delete(f"api-keys/{key_id}")