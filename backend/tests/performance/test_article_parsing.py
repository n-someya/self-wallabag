#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Performance test for article parsing in Wallabag
Tests parsing performance for different types of articles
"""

import os
import sys
import time
import json
import argparse
import requests
import statistics
from urllib.parse import urljoin
import concurrent.futures

# Sample articles to test parsing performance
TEST_ARTICLES = [
    # Simple text articles
    "https://example.com/simple-text",
    "https://news.ycombinator.com/item?id=26453318",
    
    # Articles with images
    "https://www.nationalgeographic.com/animals/article/160122-animals-insects-pandas-science-world",
    
    # Long articles
    "https://en.wikipedia.org/wiki/World_War_II",
    
    # Articles with complex layouts
    "https://www.nytimes.com/",
    "https://www.theguardian.com/international",
    
    # Articles with paywalls/javascript
    "https://medium.com/",
    "https://www.bloomberg.com/",
]

# Test URLs - replace with your Wallabag instance
DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_API_ENDPOINT = "/api/entries"

# Authentication settings
DEFAULT_CLIENT_ID = "wallabag_client_id"
DEFAULT_CLIENT_SECRET = "wallabag_client_secret"
DEFAULT_USERNAME = "wallabag"
DEFAULT_PASSWORD = "wallabag"


class WallabagPerformanceTester:
    def __init__(self, base_url, api_key=None, client_id=None, client_secret=None,
                 username=None, password=None, verbose=False):
        self.base_url = base_url
        self.api_endpoint = urljoin(base_url, DEFAULT_API_ENDPOINT)
        self.verbose = verbose
        self.token = None
        self.api_key = api_key
        self.auth_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password
        }
        
        # Stats collections
        self.results = []
    
    def authenticate(self):
        """Authenticate with the Wallabag API"""
        if self.api_key:
            if self.verbose:
                print("Using API key authentication")
            return True
            
        if not all([self.auth_data["client_id"], self.auth_data["client_secret"],
                   self.auth_data["username"], self.auth_data["password"]]):
            print("Error: Missing authentication credentials")
            return False
            
        auth_url = urljoin(self.base_url, "/oauth/v2/token")
        payload = {
            "grant_type": "password",
            "client_id": self.auth_data["client_id"],
            "client_secret": self.auth_data["client_secret"],
            "username": self.auth_data["username"],
            "password": self.auth_data["password"]
        }
        
        try:
            response = requests.post(auth_url, data=payload)
            response.raise_for_status()
            self.token = response.json().get("access_token")
            
            if self.verbose:
                print(f"Authentication successful, token: {self.token[:10]}...")
                
            return True
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {e}")
            return False
    
    def get_headers(self):
        """Get headers for API requests"""
        if self.api_key:
            return {"X-API-Key": self.api_key}
        elif self.token:
            return {"Authorization": f"Bearer {self.token}"}
        else:
            return {}
    
    def add_article(self, url):
        """Add an article to Wallabag and measure parsing time"""
        start_time = time.time()
        
        payload = {
            "url": url,
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers=self.get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            result = {
                "url": url,
                "status": "success",
                "time": elapsed_time,
                "status_code": response.status_code,
                "article_id": data.get("id"),
                "word_count": len(data.get("content", "").split()),
                "image_count": data.get("content", "").count("<img"),
            }
            
            if self.verbose:
                print(f"Added article {url} in {elapsed_time:.2f} seconds")
                
            return result
            
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_message = f"{e} - {e.response.text}"
                
            result = {
                "url": url,
                "status": "error",
                "time": elapsed_time,
                "error": error_message
            }
            
            if self.verbose:
                print(f"Failed to add article {url}: {error_message}")
                
            return result
    
    def run_tests(self, urls, max_workers=4):
        """Run performance tests for all URLs"""
        if not self.authenticate():
            return False
            
        print(f"Running article parsing performance tests against {self.base_url}")
        print(f"Testing {len(urls)} articles with {max_workers} concurrent workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.add_article, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                self.results.append(result)
                
        return True
    
    def report_results(self):
        """Report test results"""
        if not self.results:
            print("No test results to report")
            return
            
        # Calculate statistics
        successful = [r for r in self.results if r["status"] == "success"]
        failed = [r for r in self.results if r["status"] == "error"]
        
        # Timing statistics (for successful requests)
        if successful:
            times = [r["time"] for r in successful]
            avg_time = sum(times) / len(times)
            median_time = statistics.median(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            
            # Word count statistics
            word_counts = [r["word_count"] for r in successful]
            avg_words = sum(word_counts) / len(word_counts)
            
            # Calculate words per second
            words_per_second = [word_counts[i] / times[i] for i in range(len(times))]
            avg_wps = sum(words_per_second) / len(words_per_second)
        
        # Print summary
        print("\n========== PERFORMANCE TEST RESULTS ==========")
        print(f"Total articles tested: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if successful:
            print("\n--- Timing Statistics ---")
            print(f"Average parsing time: {avg_time:.2f} seconds")
            print(f"Median parsing time: {median_time:.2f} seconds")
            print(f"Min parsing time: {min_time:.2f} seconds")
            print(f"Max parsing time: {max_time:.2f} seconds")
            print(f"Standard deviation: {std_dev:.2f} seconds")
            
            print("\n--- Content Statistics ---")
            print(f"Average word count: {avg_words:.0f} words")
            print(f"Average parsing speed: {avg_wps:.0f} words/second")
        
        if failed:
            print("\n--- Failed Articles ---")
            for result in failed:
                print(f"URL: {result['url']} - Error: {result['error']}")
    
    def save_results(self, filename):
        """Save test results to JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                "base_url": self.base_url,
                "timestamp": time.time(),
                "results": self.results
            }, f, indent=2)
            
        if self.verbose:
            print(f"Results saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Wallabag Article Parsing Performance Test')
    parser.add_argument('--base-url', default=os.environ.get('WALLABAG_URL', DEFAULT_BASE_URL),
                        help='Base URL of the Wallabag instance')
    parser.add_argument('--api-key', default=os.environ.get('WALLABAG_API_KEY'),
                        help='API key for authentication')
    parser.add_argument('--client-id', default=os.environ.get('WALLABAG_CLIENT_ID', DEFAULT_CLIENT_ID),
                        help='OAuth client ID')
    parser.add_argument('--client-secret', default=os.environ.get('WALLABAG_CLIENT_SECRET', DEFAULT_CLIENT_SECRET),
                        help='OAuth client secret')
    parser.add_argument('--username', default=os.environ.get('WALLABAG_USERNAME', DEFAULT_USERNAME),
                        help='Wallabag username')
    parser.add_argument('--password', default=os.environ.get('WALLABAG_PASSWORD', DEFAULT_PASSWORD),
                        help='Wallabag password')
    parser.add_argument('--urls', default=None,
                        help='JSON file containing URLs to test')
    parser.add_argument('--output', default='performance_results.json',
                        help='Output file for test results')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of concurrent workers')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output')
    args = parser.parse_args()
    
    # Load URLs from file if provided
    test_urls = TEST_ARTICLES
    if args.urls:
        try:
            with open(args.urls) as f:
                data = json.load(f)
                if isinstance(data, list):
                    test_urls = data
                elif isinstance(data, dict) and 'urls' in data:
                    test_urls = data['urls']
        except Exception as e:
            print(f"Error loading URLs from file: {e}")
    
    tester = WallabagPerformanceTester(
        base_url=args.base_url,
        api_key=args.api_key,
        client_id=args.client_id,
        client_secret=args.client_secret,
        username=args.username,
        password=args.password,
        verbose=args.verbose
    )
    
    if tester.run_tests(test_urls, args.workers):
        tester.report_results()
        tester.save_results(args.output)
    

if __name__ == "__main__":
    main()