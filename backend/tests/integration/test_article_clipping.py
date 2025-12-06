import pytest
import time
import re
from datetime import datetime

class TestArticleClipping:
    """Integration tests for the article clipping feature"""
    
    @pytest.fixture
    def test_urls(self):
        """Provide test URLs for article clipping"""
        return [
            "https://example.com/test-article",
            "https://en.wikipedia.org/wiki/Web_archiving",
            "https://developer.mozilla.org/en-US/docs/Learn/HTML"
        ]
    
    def test_clip_article_basic_flow(self, api_client, test_urls):
        """Test the basic end-to-end flow of clipping an article"""
        # Create a new article
        data = {
            "url": test_urls[0],
            "title": "Test Article for Clipping"
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        # Get the article ID
        article_id = response.json()["id"]
        
        # Verify the article was created correctly
        assert response.json()["url"] == data["url"]
        assert response.json()["title"] == data["title"]
        
        # Get the article by ID to check it's retrievable
        get_response = api_client.get(f"entries/{article_id}")
        assert get_response.status_code == 200
        
        # Clean up
        api_client.delete(f"entries/{article_id}")
    
    def test_clip_article_with_tags(self, api_client, test_urls):
        """Test clipping an article with tags"""
        # Create a new article with tags
        data = {
            "url": test_urls[1],
            "tags": ["test", "integration", "clipping"]
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        article_id = response.json()["id"]
        
        # Verify tags were added
        tags = response.json()["tags"]
        tag_labels = [tag["label"] for tag in tags]
        
        for tag in data["tags"]:
            assert tag in tag_labels
        
        # Clean up
        api_client.delete(f"entries/{article_id}")
    
    def test_clip_article_then_star(self, api_client, test_urls):
        """Test clipping an article and then starring it"""
        # Create a new article
        data = {
            "url": test_urls[2]
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        article_id = response.json()["id"]
        
        # Star the article
        update_data = {
            "starred": True
        }
        
        update_response = api_client.patch(f"entries/{article_id}", update_data)
        assert update_response.status_code == 200
        assert update_response.json()["is_starred"] is True
        
        # Verify it's starred when retrieved
        get_response = api_client.get(f"entries/{article_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_starred"] is True
        
        # Clean up
        api_client.delete(f"entries/{article_id}")
    
    def test_clip_multiple_articles(self, api_client, test_urls):
        """Test clipping multiple articles and listing them"""
        article_ids = []
        
        # Create multiple articles
        for url in test_urls:
            data = {
                "url": url
            }
            
            response = api_client.post("entries", data)
            assert response.status_code == 201
            article_ids.append(response.json()["id"])
        
        # Get all articles
        list_response = api_client.get("entries")
        assert list_response.status_code == 200
        
        # Extract URLs from the response
        articles = list_response.json()["_embedded"]["items"]
        urls_in_response = [article["url"] for article in articles]
        
        # Verify our test URLs are in the response
        for url in test_urls:
            assert url in urls_in_response
        
        # Clean up
        for article_id in article_ids:
            api_client.delete(f"entries/{article_id}")
    
    def test_clip_article_content_extraction(self, api_client):
        """Test that article content is extracted properly"""
        # Use a real article with known content
        data = {
            "url": "https://example.com/article-content-test",
            "title": "Content Extraction Test",
            # For testing, we're providing content directly
            # In a real scenario, Wallabag would extract this from the URL
            "content": "<p>This is a test article with <strong>formatted content</strong>.</p>"
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        article_id = response.json()["id"]
        
        # Get the full article
        get_response = api_client.get(f"entries/{article_id}")
        assert get_response.status_code == 200
        
        # Verify content was preserved
        article = get_response.json()
        assert article["content"] is not None
        assert "<strong>formatted content</strong>" in article["content"]
        
        # Clean up
        api_client.delete(f"entries/{article_id}")
    
    def test_clip_article_reading_time(self, api_client):
        """Test that reading time is calculated for articles"""
        # Create an article with substantial content to test reading time calculation
        data = {
            "url": "https://example.com/reading-time-test",
            "title": "Reading Time Test",
            "content": "Lorem ipsum dolor sit amet, " * 500  # Long enough to have a measurable reading time
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        article_id = response.json()["id"]
        
        # Get the article and check the reading time
        get_response = api_client.get(f"entries/{article_id}")
        assert get_response.status_code == 200
        
        article = get_response.json()
        assert article["reading_time"] > 0  # Should have a positive reading time
        
        # Clean up
        api_client.delete(f"entries/{article_id}")
    
    def test_clip_article_domain_extraction(self, api_client):
        """Test that domain name is extracted from the URL"""
        data = {
            "url": "https://example.com/domain-test"
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        article_id = response.json()["id"]
        
        # Verify domain was extracted
        assert response.json()["domain_name"] == "example.com"
        
        # Clean up
        api_client.delete(f"entries/{article_id}")
    
    def test_clip_article_timestamps(self, api_client):
        """Test that timestamps are set correctly when clipping an article"""
        # Record the time before creating the article
        before_time = datetime.now().isoformat()
        
        # Wait a brief moment
        time.sleep(1)
        
        # Create a new article
        data = {
            "url": "https://example.com/timestamp-test"
        }
        
        response = api_client.post("entries", data)
        assert response.status_code == 201
        
        # Wait another brief moment
        time.sleep(1)
        
        # Record the time after creating the article
        after_time = datetime.now().isoformat()
        
        article_id = response.json()["id"]
        article = response.json()
        
        # Verify created_at is between before and after times
        assert article["created_at"] >= before_time
        assert article["created_at"] <= after_time
        
        # Verify updated_at is set
        assert article["updated_at"] is not None
        
        # Verify read_at is not set for new articles
        assert article["read_at"] is None
        
        # Clean up
        api_client.delete(f"entries/{article_id}")