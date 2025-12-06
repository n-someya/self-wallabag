import pytest
import time

class TestArticleManagement:
    """Integration tests for article management features"""
    
    @pytest.fixture
    def test_articles(self, api_client):
        """Create test articles for management tests"""
        articles = [
            {
                "url": "https://example.com/article-management-1",
                "title": "Article Management Test 1",
                "tags": ["test", "management"]
            },
            {
                "url": "https://example.com/article-management-2",
                "title": "Article Management Test 2",
                "tags": ["test", "management"]
            },
            {
                "url": "https://example.com/article-management-3",
                "title": "Article Management Test 3",
                "tags": ["test"]
            }
        ]
        
        article_ids = []
        
        # Create the test articles
        for article in articles:
            response = api_client.post("entries", article)
            assert response.status_code == 201
            article_ids.append(response.json()["id"])
        
        yield article_ids
        
        # Clean up
        for article_id in article_ids:
            api_client.delete(f"entries/{article_id}")
    
    def test_archive_article(self, api_client, test_articles):
        """Test archiving and unarchiving an article"""
        article_id = test_articles[0]
        
        # Archive the article
        data = {"archive": True}
        response = api_client.patch(f"entries/{article_id}", data)
        assert response.status_code == 200
        assert response.json()["is_archived"] is True
        
        # Get article to verify it's archived
        get_response = api_client.get(f"entries/{article_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_archived"] is True
        
        # List only archived articles
        list_response = api_client.get("entries", params={"archive": 1})
        assert list_response.status_code == 200
        
        # Verify our article is in the archived list
        articles = list_response.json()["_embedded"]["items"]
        found = False
        for article in articles:
            if article["id"] == article_id:
                found = True
                break
        
        assert found, "Article not found in archived list"
        
        # Unarchive the article
        data = {"archive": False}
        response = api_client.patch(f"entries/{article_id}", data)
        assert response.status_code == 200
        assert response.json()["is_archived"] is False
    
    def test_star_article(self, api_client, test_articles):
        """Test starring and unstarring an article"""
        article_id = test_articles[1]
        
        # Star the article
        data = {"starred": True}
        response = api_client.patch(f"entries/{article_id}", data)
        assert response.status_code == 200
        assert response.json()["is_starred"] is True
        
        # Get article to verify it's starred
        get_response = api_client.get(f"entries/{article_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_starred"] is True
        
        # List only starred articles
        list_response = api_client.get("entries", params={"starred": 1})
        assert list_response.status_code == 200
        
        # Verify our article is in the starred list
        articles = list_response.json()["_embedded"]["items"]
        found = False
        for article in articles:
            if article["id"] == article_id:
                found = True
                break
        
        assert found, "Article not found in starred list"
        
        # Unstar the article
        data = {"starred": False}
        response = api_client.patch(f"entries/{article_id}", data)
        assert response.status_code == 200
        assert response.json()["is_starred"] is False
    
    def test_update_article_tags(self, api_client, test_articles):
        """Test adding and removing tags from an article"""
        article_id = test_articles[2]
        
        # Get initial tags
        get_response = api_client.get(f"entries/{article_id}")
        assert get_response.status_code == 200
        initial_tags = [tag["label"] for tag in get_response.json()["tags"]]
        
        # Add new tags
        new_tags = ["updated", "management", "integration"]
        data = {"tags": new_tags}
        response = api_client.patch(f"entries/{article_id}", data)
        assert response.status_code == 200
        
        # Verify tags were updated
        updated_tags = [tag["label"] for tag in response.json()["tags"]]
        for tag in new_tags:
            assert tag in updated_tags
    
    def test_mark_article_as_read(self, api_client, test_articles):
        """Test marking an article as read"""
        article_id = test_articles[0]
        
        # Initially, the article should not be read
        get_response = api_client.get(f"entries/{article_id}")
        assert get_response.status_code == 200
        assert get_response.json()["read_at"] is None
        
        # Mark as read (in Wallabag API, this might be done differently depending on implementation)
        # This is a simplified approach - in a real test, you'd use the actual API for marking as read
        data = {"read_at": "2023-01-01T12:00:00+00:00"}
        response = api_client.patch(f"entries/{article_id}", data)
        assert response.status_code == 200
        assert response.json()["read_at"] is not None
    
    def test_filter_articles_by_tag(self, api_client, test_articles):
        """Test filtering articles by tag"""
        # All test articles have the 'test' tag
        response = api_client.get("entries", params={"tags": "test"})
        assert response.status_code == 200
        
        articles = response.json()["_embedded"]["items"]
        for article_id in test_articles:
            found = False
            for article in articles:
                if article["id"] == article_id:
                    found = True
                    break
            assert found, f"Article {article_id} not found when filtering by 'test' tag"
        
        # Only two articles have the 'management' tag
        response = api_client.get("entries", params={"tags": "management"})
        assert response.status_code == 200
        
        articles = response.json()["_embedded"]["items"]
        management_articles = [test_articles[0], test_articles[1]]
        
        for article_id in management_articles:
            found = False
            for article in articles:
                if article["id"] == article_id:
                    found = True
                    break
            assert found, f"Article {article_id} not found when filtering by 'management' tag"
    
    def test_sort_articles(self, api_client, test_articles):
        """Test sorting articles"""
        # Sort by created date, ascending
        response = api_client.get("entries", params={"sort": "created", "order": "asc"})
        assert response.status_code == 200
        
        # The articles should be in the order they were created
        articles = response.json()["_embedded"]["items"]
        article_ids = [article["id"] for article in articles if article["id"] in test_articles]
        
        # The test articles were created in order, so they should appear in that order
        for i in range(len(test_articles)):
            if i < len(article_ids):
                assert test_articles[i] == article_ids[i]
        
        # Sort by created date, descending
        response = api_client.get("entries", params={"sort": "created", "order": "desc"})
        assert response.status_code == 200
        
        # The articles should be in reverse order
        articles = response.json()["_embedded"]["items"]
        article_ids = [article["id"] for article in articles if article["id"] in test_articles]
        
        # The test articles were created in order, so they should appear in reverse order
        for i in range(len(test_articles)):
            if i < len(article_ids):
                assert test_articles[len(test_articles) - 1 - i] == article_ids[i]
    
    def test_bulk_actions(self, api_client, test_articles):
        """Test bulk actions on articles by using filters"""
        # First, archive all articles with the 'management' tag
        # This is a simulation of bulk action since our API doesn't have explicit bulk endpoints
        
        # Get all articles with the 'management' tag
        response = api_client.get("entries", params={"tags": "management"})
        assert response.status_code == 200
        
        management_articles = [article["id"] for article in response.json()["_embedded"]["items"]]
        
        # Archive each one
        for article_id in management_articles:
            data = {"archive": True}
            response = api_client.patch(f"entries/{article_id}", data)
            assert response.status_code == 200
        
        # Now verify all management-tagged articles are archived
        response = api_client.get("entries", params={"tags": "management", "archive": 1})
        assert response.status_code == 200
        
        archived_management = [article["id"] for article in response.json()["_embedded"]["items"]]
        assert len(archived_management) == len(management_articles)