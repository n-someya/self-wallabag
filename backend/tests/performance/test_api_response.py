#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Performance test for Wallabag API response time
Tests API endpoints under various load conditions
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
import matplotlib.pyplot as plt
from tabulate import tabulate

# Test API endpoints
API_ENDPOINTS = [
    {"name": "Get entries", "method": "GET", "path": "/api/entries", "params": {"page": 1, "perPage": 30}},
    {"name": "Get entry by ID", "method": "GET", "path": "/api/entries/{entry_id}", "params": {}},
    {"name": "Search entries", "method": "GET", "path": "/api/search", "params": {"term": "test", "page": 1}},
    {"name": "Get tags", "method": "GET", "path": "/api/tags", "params": {}},
    {"name": "Create entry", "method": "POST", "path": "/api/entries", "data": {"url": "https://example.com"}},
]

# Test configurations
TEST_CONFIGS = [
    {"name": "Light load", "concurrent_requests": 1, "repeats": 5},
    {"name": "Medium load", "concurrent_requests": 5, "repeats": 10},
    {"name": "Heavy load", "concurrent_requests": 10, "repeats": 15},
]

# Default settings
DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_CLIENT_ID = "wallabag_client_id"
DEFAULT_CLIENT_SECRET = "wallabag_client_secret"
DEFAULT_USERNAME = "wallabag"
DEFAULT_PASSWORD = "wallabag"


class WallabagApiTester:
    def __init__(self, base_url, api_key=None, client_id=None, client_secret=None,
                 username=None, password=None, verbose=False):
        self.base_url = base_url
        self.verbose = verbose
        self.token = None
        self.api_key = api_key
        self.auth_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password
        }
        
        # Internal storage
        self.entry_id = None
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
            return {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        elif self.token:
            return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        else:
            return {"Content-Type": "application/json"}
    
    def prepare_test_data(self):
        """Create test data to use in performance tests"""
        if self.verbose:
            print("Preparing test data...")
            
        # Create a test entry to use for get/update operations
        try:
            url = urljoin(self.base_url, "/api/entries")
            payload = {"url": "https://example.com/performance-test"}
            
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            self.entry_id = response.json().get("id")
            
            if self.verbose:
                print(f"Created test entry with ID: {self.entry_id}")
            
            # Add some tags to the entry
            if self.entry_id:
                tags_url = urljoin(self.base_url, f"/api/entries/{self.entry_id}/tags")
                tags_payload = {"tags": "performance,test,api"}
                
                requests.post(tags_url, headers=self.get_headers(), json=tags_payload)
            
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to prepare test data: {e}")
            return False
    
    def make_request(self, endpoint):
        """Make a request to the specified API endpoint"""
        method = endpoint["method"]
        path = endpoint["path"]
        
        # Replace path parameters
        if "{entry_id}" in path and self.entry_id:
            path = path.replace("{entry_id}", str(self.entry_id))
        
        url = urljoin(self.base_url, path)
        start_time = time.time()
        
        try:
            if method == "GET":
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    params=endpoint.get("params", {})
                )
            elif method == "POST":
                response = requests.post(
                    url,
                    headers=self.get_headers(),
                    json=endpoint.get("data", {})
                )
            elif method == "PUT" or method == "PATCH":
                response = requests.patch(
                    url,
                    headers=self.get_headers(),
                    json=endpoint.get("data", {})
                )
            elif method == "DELETE":
                response = requests.delete(
                    url,
                    headers=self.get_headers()
                )
            else:
                return {
                    "endpoint": endpoint["name"],
                    "status": "error",
                    "time": 0,
                    "error": f"Unsupported HTTP method: {method}"
                }
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            result = {
                "endpoint": endpoint["name"],
                "status": "success" if response.status_code < 400 else "error",
                "time": elapsed_time,
                "status_code": response.status_code,
            }
            
            # Add response size if successful
            if result["status"] == "success":
                result["response_size"] = len(response.content)
            else:
                result["error"] = response.text
            
            return result
            
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            return {
                "endpoint": endpoint["name"],
                "status": "error",
                "time": elapsed_time,
                "error": str(e)
            }
    
    def run_test(self, endpoint, concurrent_requests, repeats):
        """Run performance test for a specific endpoint"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(self.make_request, endpoint) for _ in range(repeats)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        return results
    
    def run_all_tests(self):
        """Run all performance tests"""
        if not self.authenticate():
            return False
        
        if not self.prepare_test_data():
            return False
        
        print(f"Running API performance tests against {self.base_url}")
        
        for config in TEST_CONFIGS:
            print(f"\n=== Running tests with {config['name']} ===")
            print(f"Concurrent requests: {config['concurrent_requests']}")
            print(f"Repeats per endpoint: {config['repeats']}")
            
            config_results = {
                "config": config,
                "results": []
            }
            
            for endpoint in API_ENDPOINTS:
                if self.verbose:
                    print(f"Testing endpoint: {endpoint['name']}")
                
                endpoint_results = self.run_test(
                    endpoint,
                    config['concurrent_requests'],
                    config['repeats']
                )
                
                config_results["results"].extend(endpoint_results)
            
            self.results.append(config_results)
        
        return True
    
    def report_results(self):
        """Generate a report of performance test results"""
        if not self.results:
            print("No test results to report")
            return
        
        print("\n========== API PERFORMANCE TEST RESULTS ==========")
        
        for config_result in self.results:
            config = config_result["config"]
            results = config_result["results"]
            
            print(f"\n=== {config['name']} ===")
            
            # Group results by endpoint
            endpoint_results = {}
            for result in results:
                endpoint = result["endpoint"]
                if endpoint not in endpoint_results:
                    endpoint_results[endpoint] = []
                
                endpoint_results[endpoint].append(result)
            
            # Calculate statistics for each endpoint
            table_data = []
            for endpoint, endpoint_results_list in endpoint_results.items():
                successful = [r for r in endpoint_results_list if r["status"] == "success"]
                failed = len(endpoint_results_list) - len(successful)
                
                if successful:
                    times = [r["time"] for r in successful]
                    avg_time = sum(times) / len(times)
                    median_time = statistics.median(times)
                    min_time = min(times)
                    max_time = max(times)
                    std_dev = statistics.stdev(times) if len(times) > 1 else 0
                    
                    table_data.append([
                        endpoint,
                        len(successful),
                        failed,
                        f"{avg_time:.3f}s",
                        f"{median_time:.3f}s",
                        f"{min_time:.3f}s",
                        f"{max_time:.3f}s",
                        f"{std_dev:.3f}s"
                    ])
                else:
                    table_data.append([
                        endpoint,
                        0,
                        failed,
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A"
                    ])
            
            # Print table
            headers = ["Endpoint", "Success", "Failed", "Avg Time", "Median", "Min", "Max", "Std Dev"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    def generate_charts(self, output_dir):
        """Generate performance charts from test results"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Prepare data for charts
        configs = [cr["config"]["name"] for cr in self.results]
        endpoints = set()
        
        # Find all unique endpoints
        for config_result in self.results:
            for result in config_result["results"]:
                endpoints.add(result["endpoint"])
        
        endpoints = sorted(list(endpoints))
        
        # Create a chart for each endpoint
        for endpoint in endpoints:
            avg_times = []
            
            for config_result in self.results:
                config_name = config_result["config"]["name"]
                endpoint_results = [r for r in config_result["results"] if r["endpoint"] == endpoint and r["status"] == "success"]
                
                if endpoint_results:
                    times = [r["time"] for r in endpoint_results]
                    avg_time = sum(times) / len(times)
                    avg_times.append(avg_time)
                else:
                    avg_times.append(0)
            
            # Create the chart
            plt.figure(figsize=(10, 6))
            plt.bar(configs, avg_times)
            plt.title(f"Average Response Time: {endpoint}")
            plt.xlabel("Test Configuration")
            plt.ylabel("Time (seconds)")
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            
            # Save the chart
            safe_name = endpoint.replace(" ", "_").replace("/", "_").lower()
            chart_path = os.path.join(output_dir, f"{safe_name}.png")
            plt.savefig(chart_path)
            plt.close()
    
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
    parser = argparse.ArgumentParser(description='Wallabag API Performance Test')
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
    parser.add_argument('--output', default='api_performance_results.json',
                        help='Output file for test results')
    parser.add_argument('--charts', default='performance_charts',
                        help='Directory to output performance charts')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output')
    args = parser.parse_args()
    
    tester = WallabagApiTester(
        base_url=args.base_url,
        api_key=args.api_key,
        client_id=args.client_id,
        client_secret=args.client_secret,
        username=args.username,
        password=args.password,
        verbose=args.verbose
    )
    
    if tester.run_all_tests():
        tester.report_results()
        tester.save_results(args.output)
        
        try:
            tester.generate_charts(args.charts)
            print(f"Performance charts generated in directory: {args.charts}")
        except ImportError:
            print("Warning: matplotlib not installed. Charts not generated.")
        except Exception as e:
            print(f"Error generating charts: {e}")
    

if __name__ == "__main__":
    main()