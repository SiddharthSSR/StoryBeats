#!/usr/bin/env python3
"""
Test script to verify rate limiting on StoryBeats API
"""
import requests
import time

API_URL = "http://localhost:5001"

def test_rate_limit():
    """Test rate limiting on /api/analyze endpoint (5 per minute)"""
    print("Testing rate limiting on /api/analyze endpoint...")
    print("Rate limit: 5 requests per minute\n")

    # Test file (create a dummy file for testing)
    test_file = {'photo': ('test.jpg', b'fake image data', 'image/jpeg')}

    for i in range(7):  # Try 7 requests (should fail after 5)
        print(f"Request {i+1}:")
        try:
            response = requests.post(
                f"{API_URL}/api/analyze",
                files=test_file,
                timeout=5
            )

            # Check for rate limit headers
            if 'X-RateLimit-Limit' in response.headers:
                print(f"  Rate Limit: {response.headers.get('X-RateLimit-Limit')}")
                print(f"  Remaining: {response.headers.get('X-RateLimit-Remaining')}")
                print(f"  Reset: {response.headers.get('X-RateLimit-Reset')}")

            print(f"  Status: {response.status_code}")

            if response.status_code == 429:
                print(f"  ✓ RATE LIMITED! (as expected)")
                print(f"  Response: {response.json()}")
                break
            else:
                print(f"  Response: {response.text[:100]}...")

        except requests.exceptions.RequestException as e:
            print(f"  Error: {e}")

        print()
        time.sleep(0.5)  # Small delay between requests

def test_health_endpoint():
    """Test that health endpoint has default rate limits"""
    print("\nTesting health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if 'X-RateLimit-Limit' in response.headers:
        print(f"Rate Limit: {response.headers.get('X-RateLimit-Limit')}")
        print(f"Remaining: {response.headers.get('X-RateLimit-Remaining')}")

if __name__ == "__main__":
    test_health_endpoint()
    test_rate_limit()
