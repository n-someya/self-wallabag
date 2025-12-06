import pytest
import os
import psycopg2
import time
import requests

class TestDatabaseConnection:
    """Integration tests for database connection"""
    
    @pytest.fixture
    def db_config(self):
        """Get database configuration from environment variables"""
        return {
            'host': os.getenv('TEST_DATABASE_HOST', 'localhost'),
            'port': os.getenv('TEST_DATABASE_PORT', '5432'),
            'database': os.getenv('TEST_DATABASE_NAME', 'wallabag'),
            'user': os.getenv('TEST_DATABASE_USER', 'wallabag'),
            'password': os.getenv('TEST_DATABASE_PASSWORD', 'wallabag')
        }
    
    def test_database_connection(self, db_config):
        """Test that we can connect to the database"""
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            
            # Connection successful
            assert conn is not None
            
            # Test creating a cursor
            cursor = conn.cursor()
            assert cursor is not None
            
            # Close resources
            cursor.close()
            conn.close()
            
        except Exception as e:
            pytest.fail(f"Failed to connect to database: {e}")
    
    def test_database_tables_exist(self, db_config):
        """Test that essential database tables exist"""
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            
            cursor = conn.cursor()
            
            # Query to check if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema='public'
                ORDER BY table_name;
            """)
            
            tables = [table[0] for table in cursor.fetchall()]
            
            # Check for essential Wallabag tables (the exact names might vary based on actual schema)
            essential_table_patterns = ['entry', 'tag', 'user', 'config']
            for pattern in essential_table_patterns:
                found = False
                for table in tables:
                    if pattern in table:
                        found = True
                        break
                
                if not found:
                    pytest.fail(f"No table matching pattern '{pattern}' found in database")
            
            # Close resources
            cursor.close()
            conn.close()
            
        except Exception as e:
            pytest.fail(f"Failed to check database tables: {e}")
    
    def test_database_connection_from_application(self, api_client, wait_for_service):
        """Test that the application can connect to the database by making API requests"""
        # Try to fetch entries - this will implicitly test database connection
        response = api_client.get("entries")
        
        # Should get a successful response, not a database error
        assert response.status_code == 200
        
        # Should have the expected structure
        data = response.json()
        assert "page" in data
        assert "_embedded" in data
        assert "items" in data["_embedded"]
    
    def test_database_write_operation(self, api_client, db_config):
        """Test that we can write to the database by creating and then retrieving an article"""
        # Create a test article
        data = {
            "url": "https://example.com/database-test-article",
            "title": "Database Test Article"
        }
        
        create_response = api_client.post("entries", data)
        assert create_response.status_code == 201
        
        article_id = create_response.json()["id"]
        
        # Wait briefly to ensure database write is complete
        time.sleep(1)
        
        # Now connect directly to the database and check if the article exists
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            
            cursor = conn.cursor()
            
            # Query to check if article exists (table and column names might need adjustment)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM entry 
                WHERE id = %s OR title = %s
            """, (article_id, data['title']))
            
            count = cursor.fetchone()[0]
            
            # Should find at least one matching article
            assert count >= 1
            
            # Clean up
            cursor.close()
            conn.close()
            api_client.delete(f"entries/{article_id}")
            
        except Exception as e:
            # Clean up anyway
            api_client.delete(f"entries/{article_id}")
            pytest.fail(f"Failed to verify database write: {e}")
    
    def test_database_persistence(self, api_client):
        """Test that data persists in the database between requests"""
        # Create a test article with a unique identifier
        unique_title = f"Persistence Test Article {time.time()}"
        data = {
            "url": "https://example.com/persistence-test",
            "title": unique_title
        }
        
        create_response = api_client.post("entries", data)
        assert create_response.status_code == 201
        article_id = create_response.json()["id"]
        
        # Create a second test article
        data2 = {
            "url": "https://example.com/persistence-test-2",
            "title": f"Second {unique_title}"
        }
        
        create_response2 = api_client.post("entries", data2)
        assert create_response2.status_code == 201
        article_id2 = create_response2.json()["id"]
        
        # Get all entries and check both articles are there
        get_response = api_client.get("entries")
        assert get_response.status_code == 200
        
        articles = get_response.json()["_embedded"]["items"]
        found_first = False
        found_second = False
        
        for article in articles:
            if article["id"] == article_id:
                found_first = True
            if article["id"] == article_id2:
                found_second = True
        
        assert found_first, "First created article not found in database"
        assert found_second, "Second created article not found in database"
        
        # Clean up
        api_client.delete(f"entries/{article_id}")
        api_client.delete(f"entries/{article_id2}")