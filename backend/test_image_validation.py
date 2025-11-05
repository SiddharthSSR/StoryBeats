#!/usr/bin/env python3
"""
Test script to verify image validation security
"""
import requests
import os

API_URL = "http://localhost:5001"

def test_valid_image():
    """Test with a valid PNG image"""
    print("Test 1: Valid PNG image")
    # Create a simple valid PNG
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img.save('/tmp/test_valid.png')

    with open('/tmp/test_valid.png', 'rb') as f:
        files = {'photo': ('test.png', f, 'image/png')}
        response = requests.post(f"{API_URL}/api/analyze", files=files)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  ✓ PASS: Valid image accepted")
        else:
            print(f"  ✗ FAIL: {response.json()}")

    os.remove('/tmp/test_valid.png')
    print()

def test_non_image_file():
    """Test with a text file disguised as PNG"""
    print("Test 2: Text file disguised as PNG")
    with open('/tmp/fake_image.png', 'w') as f:
        f.write("This is not an image!")

    with open('/tmp/fake_image.png', 'rb') as f:
        files = {'photo': ('fake.png', f, 'image/png')}
        response = requests.post(f"{API_URL}/api/analyze", files=files)
        print(f"  Status: {response.status_code}")
        if response.status_code == 400:
            print(f"  ✓ PASS: Fake image rejected - {response.json().get('error')}")
        else:
            print(f"  ✗ FAIL: Fake image was accepted!")

    os.remove('/tmp/fake_image.png')
    print()

def test_tiny_image():
    """Test with image smaller than minimum dimension"""
    print("Test 3: Image too small (5x5 pixels)")
    from PIL import Image
    img = Image.new('RGB', (5, 5), color='blue')
    img.save('/tmp/tiny.png')

    with open('/tmp/tiny.png', 'rb') as f:
        files = {'photo': ('tiny.png', f, 'image/png')}
        response = requests.post(f"{API_URL}/api/analyze", files=files)
        print(f"  Status: {response.status_code}")
        if response.status_code == 400:
            print(f"  ✓ PASS: Tiny image rejected - {response.json().get('error')}")
        else:
            print(f"  ✗ FAIL: Tiny image was accepted!")

    os.remove('/tmp/tiny.png')
    print()

def test_corrupted_image():
    """Test with corrupted image data"""
    print("Test 4: Corrupted PNG file")
    # Create a file with PNG header but corrupted data
    with open('/tmp/corrupted.png', 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + b'corrupted data here' * 100)

    with open('/tmp/corrupted.png', 'rb') as f:
        files = {'photo': ('corrupted.png', f, 'image/png')}
        response = requests.post(f"{API_URL}/api/analyze", files=files)
        print(f"  Status: {response.status_code}")
        if response.status_code == 400:
            print(f"  ✓ PASS: Corrupted image rejected - {response.json().get('error')}")
        else:
            print(f"  ✗ FAIL: Corrupted image was accepted!")

    os.remove('/tmp/corrupted.png')
    print()

def test_different_formats():
    """Test with different valid image formats"""
    print("Test 5: Different valid formats")
    from PIL import Image

    formats = [
        ('JPEG', 'test.jpg'),
        ('PNG', 'test.png'),
        ('GIF', 'test.gif'),
        ('WEBP', 'test.webp')
    ]

    for fmt, filename in formats:
        img = Image.new('RGB', (200, 200), color='green')
        filepath = f'/tmp/{filename}'
        img.save(filepath, fmt)

        with open(filepath, 'rb') as f:
            files = {'photo': (filename, f, f'image/{fmt.lower()}')}
            response = requests.post(f"{API_URL}/api/analyze", files=files)
            status = "✓ PASS" if response.status_code == 200 else "✗ FAIL"
            print(f"  {fmt}: {status} (Status: {response.status_code})")

        os.remove(filepath)
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("StoryBeats Image Validation Security Tests")
    print("=" * 60)
    print()

    test_valid_image()
    test_non_image_file()
    test_tiny_image()
    test_corrupted_image()
    test_different_formats()

    print("=" * 60)
    print("Tests Complete!")
    print("=" * 60)
