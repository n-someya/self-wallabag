import pytest
import json
from jsonschema import validate

# Define the JSON schema for validating the API keys response
API_KEYS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "name", "created_at", "is_active"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time"},
            "expires_at": {"type": ["string", "null"], "format": "date-time"},
            "last_used_at": {"type": ["string", "null"], "format": "date-time"},
            "is_active": {"type": "boolean"}
        }
    }
}

@pytest.fixture
def create_api_key(api_client):
    """Create a test API key and return its ID"""
    data = {
        "name": "Test API Key for GET Tests"
    }
    
    response = api_client.post("api-keys", data)
    assert response.status_code == 201
    key_id = response.json()["id"]
    
    yield key_id
    
    # Clean up
    api_client.delete(f"api-keys/{key_id}")

class TestGetApiKeys:
    """Tests for the GET /api-keys endpoint"""
    
    def test_get_api_keys_unauthorized_without_api_key(self, api_url):
        """Test that accessing API keys without API key fails"""
        response = pytest.requests.get(f"{api_url}/api-keys")
        assert response.status_code == 401
    
    def test_get_api_keys_schema_validation(self, api_client, create_api_key):
        """Test that the response schema matches the API contract"""
        response = api_client.get("api-keys")
        assert response.status_code == 200
        
        # Validate response against schema
        try:
            validate(instance=response.json(), schema=API_KEYS_SCHEMA)
        except Exception as e:
            pytest.fail(f"Response does not match schema: {e}")
    
    def test_get_api_keys_includes_created_key(self, api_client, create_api_key):
        """Test that the created API key is included in the list"""
        response = api_client.get("api-keys")
        assert response.status_code == 200
        
        api_keys = response.json()
        key_ids = [key["id"] for key in api_keys]
        
        assert create_api_key in key_ids
    
    def test_get_api_keys_sensitive_data_excluded(self, api_client, create_api_key):
        """Test that sensitive data like the key value is not included"""
        response = api_client.get("api-keys")
        assert response.status_code == 200
        
        api_keys = response.json()
        for key in api_keys:
            assert "key" not in key  # The actual API key value should not be included
    
    def test_get_api_keys_required_fields(self, api_client, create_api_key):
        """Test that each API key has all required fields"""
        response = api_client.get("api-keys")
        assert response.status_code == 200
        
        api_keys = response.json()
        
        required_fields = ["id", "name", "created_at", "is_active"]
        for key in api_keys:
            for field in required_fields:
                assert field in key
                assert key[field] is not None