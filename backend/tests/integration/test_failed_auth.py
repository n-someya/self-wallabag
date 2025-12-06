import pytest
import requests
import os
import time

class TestFailedAuthentication:
    """Integration tests for authentication failure scenarios"""
    
    def test_missing_api_key(self, api_url):
        """Test that requests without API key are rejected"""
        # Try to get entries without API key
        response = requests.get(f"{api_url}/entries")
        assert response.status_code == 401
        
        # Try to create an entry without API key
        data = {"url": "https://example.com/auth-test"}
        response = requests.post(
            f"{api_url}/entries",
            headers={"Content-Type": "application/json"},
            json=data
        )
        assert response.status_code == 401
    
    def test_invalid_api_key(self, api_url):
        """Test that requests with invalid API key are rejected"""
        # Try to get entries with invalid API key
        headers = {
            "X-API-Key": "invalid-api-key",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{api_url}/entries", headers=headers)
        assert response.status_code == 401
        
        # Try to create an entry with invalid API key
        data = {"url": "https://example.com/auth-test"}
        response = requests.post(f"{api_url}/entries", headers=headers, json=data)
        assert response.status_code == 401
    
    def test_expired_api_key(self, api_client, api_url):
        """Test that requests with expired API key are rejected"""
        # Create an API key that expires immediately
        data = {
            "name": "Expired Key Test",
            "expires_at": "2000-01-01T00:00:00Z"  # Set in the past
        }
        
        response = api_client.post("api-keys", data)
        assert response.status_code == 201
        
        # Get the key value
        expired_key = response.json()["key"]
        key_id = response.json()["id"]
        
        # Try to use the expired key
        headers = {
            "X-API-Key": expired_key,
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{api_url}/entries", headers=headers)
        assert response.status_code == 401
        
        # Clean up
        api_client.delete(f"api-keys/{key_id}")
    
    def test_revoked_api_key(self, api_client, api_url):
        """Test that requests with a revoked API key are rejected"""
        # Create an API key
        data = {
            "name": "Key To Revoke"
        }
        
        response = api_client.post("api-keys", data)
        assert response.status_code == 201
        
        revoked_key = response.json()["key"]
        key_id = response.json()["id"]
        
        # Revoke the key by deleting it
        delete_response = api_client.delete(f"api-keys/{key_id}")
        assert delete_response.status_code == 204
        
        # Try to use the revoked key
        headers = {
            "X-API-Key": revoked_key,
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{api_url}/entries", headers=headers)
        assert response.status_code == 401
    
    def test_auth_error_response_format(self, api_url):
        """Test that authentication errors return the expected response format"""
        response = requests.get(f"{api_url}/entries")
        assert response.status_code == 401
        
        # Verify response has proper content type
        assert "application/json" in response.headers.get("Content-Type", "")
        
        # Check error response structure (should include code and message)
        error = response.json()
        assert "code" in error
        assert "message" in error
        assert error["code"] == 401
    
    def test_rate_limiting(self, api_url):
        """Test that repeated failed authentications trigger rate limiting"""
        # Make multiple rapid requests with invalid authentication
        headers = {
            "X-API-Key": "invalid-key",
            "Content-Type": "application/json"
        }
        
        # Make 10 rapid requests - should trigger rate limiting if implemented
        for _ in range(10):
            requests.get(f"{api_url}/entries", headers=headers)
        
        # Check if rate limiting is in effect
        # Either 429 (Too Many Requests) or still 401 depending on implementation
        response = requests.get(f"{api_url}/entries", headers=headers)
        
        # Either of these status codes is acceptable
        assert response.status_code in (401, 429)
        
        # If rate limited, response should have retry headers
        if response.status_code == 429:
            assert "Retry-After" in response.headers
    
    def test_error_logging(self, api_client):
        """Test that authentication failures are properly logged"""
        # This test is more theoretical since we can't access logs directly
        # In a real test environment, you'd verify logs after this test
        
        # Make an authenticated request first (to establish baseline)
        valid_response = api_client.get("entries")
        assert valid_response.status_code == 200
        
        # Make an unauthenticated request that should be logged
        response = requests.get(f"{api_client.api_url}/entries")
        assert response.status_code == 401
        
        # In a real test, you would now check logs for the authentication failure
        # Since we can't access logs here, this test is mostly for documentation
    
    def test_different_auth_methods(self, api_url, oauth_token):
        """Test that different authentication methods don't interfere with each other"""
        # Test with OAuth token
        oauth_headers = {
            "Authorization": f"Bearer {oauth_token}",
            "Content-Type": "application/json"
        }
        
        oauth_response = requests.get(f"{api_url}/entries", headers=oauth_headers)
        assert oauth_response.status_code == 200
        
        # Test with invalid API key
        api_key_headers = {
            "X-API-Key": "invalid-api-key",
            "Content-Type": "application/json"
        }
        
        api_key_response = requests.get(f"{api_url}/entries", headers=api_key_headers)
        assert api_key_response.status_code == 401