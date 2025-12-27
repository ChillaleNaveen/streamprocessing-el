"""Test LangChain Ollama with timeout configuration"""
import sys
import time
import traceback

print("=" * 60)
print("LangChain Ollama with Timeout Test")
print("=" * 60)

# Test: LangChain with timeout
print("\n[Test] Initializing LangChain Ollama with timeout...")
try:
    from langchain_community.llms import Ollama
    from config import config
    
    print(f"  - Base URL: {config.ollama.base_url}")
    print(f"  - Model: {config.ollama.model}")
    
    # Initialize with timeout
    llm = Ollama(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        timeout=60  # Add explicit timeout
    )
    print("✅ Ollama initialized with 60s timeout")
    
    test_prompt = "Say hello in one word."
    print(f"\n  - Prompt: {test_prompt}")
    print("  - Invoking LLM...")
    
    start = time.time()
    response = llm.invoke(test_prompt)
    elapsed = time.time() - start
    
    print(f"✅ Response received in {elapsed:.2f}s!")
    print(f"  - Type: {type(response)}")
    print(f"  - Length: {len(str(response))} chars")
    print(f"  - Content: '{response}'")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Test complete!")
print("=" * 60)
