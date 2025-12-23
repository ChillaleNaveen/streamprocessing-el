"""Test script to diagnose Ollama integration issue"""
import sys
import traceback

print("=" * 60)
print("Ollama Integration Diagnostics")
print("=" * 60)

# Test 1: Import modules
print("\n[Test 1] Importing modules...")
try:
    from langchain_community.llms import Ollama
    from config import config
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Initialize Ollama
print(f"\n[Test 2] Initializing Ollama...")
print(f"  - Base URL: {config.ollama.base_url}")
print(f"  - Model: {config.ollama.model}")
print(f"  - Temperature: {config.ollama.temperature}")

try:
    llm = Ollama(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature
    )
    print("✅ Ollama initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Simple invocation
print(f"\n[Test 3] Testing LLM invocation...")
test_prompt = "What is 2+2? Answer with just the number."

try:
    print(f"  - Prompt: {test_prompt}")
    print("  - Invoking LLM...")
    
    response = llm.invoke(test_prompt)
    
    print(f"✅ Response received!")
    print(f"  - Type: {type(response)}")
    print(f"  - Length: {len(str(response))} chars")
    print(f"  - Content: '{response}'")
    
except Exception as e:
    print(f"❌ Invocation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: With template
print(f"\n[Test 4] Testing with prompt template...")
from langchain.prompts import PromptTemplate

template = PromptTemplate(
    input_variables=["question"],
    template="Answer the following question concisely:\\n\\nQuestion: {question}\\n\\nAnswer:"
)

formatted = template.format(question="What is Python?")
print(f"  - Formatted prompt: {formatted[:100]}...")

try:
    response = llm.invoke(formatted)
    print(f"✅ Response received!")
    print(f"  - Length: {len(str(response))} chars")
    print(f"  - Content: '{response}'")
except Exception as e:
    print(f"❌ Invocation failed: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Diagnostics complete!")
print("=" * 60)
