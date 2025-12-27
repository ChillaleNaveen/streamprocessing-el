"""Simple test to check Ollama API directly"""
import requests
import json
import time

print("Testing Ollama API directly...")
print("=" * 60)

# Test 1: Check server health
print("\n[Test 1] Checking Ollama server...")
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    print(f"✅ Server is responding: {response.status_code}")
    data = response.json()
    print(f"Available models: {[m['name'] for m in data.get('models', [])]}")
except Exception as e:
    print(f"❌ Server check failed: {e}")
    exit(1)

# Test 2: Simple generation
print("\n[Test 2] Testing model generation...")
try:
    payload = {
        "model": "tinyllama",
        "prompt": "Say hello in one word:",
        "stream": False
    }
    
    print(f"Sending request to Ollama...")
    start = time.time()
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=30
    )
    
    elapsed = time.time() - start
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Got response in {elapsed:.2f}s")
        print(f"Response: {result.get('response', 'No response')}")
        print(f"Done: {result.get('done', False)}")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"❌ Generation failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ Test complete!")
