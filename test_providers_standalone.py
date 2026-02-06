#!/usr/bin/env python3
"""Standalone test for multi-provider system."""

import asyncio
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Import providers directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lollmsbot'))
from providers.router import MultiProviderRouter


async def main():
    """Run live tests."""
    print("\n" + "="*70)
    print("🚀 MULTI-PROVIDER API SYSTEM - LIVE TESTS")
    print("="*70)
    
    # Check environment
    print("\nEnvironment Check:")
    openrouter_keys = []
    for i in [1, 2, 3]:
        key = os.getenv(f"OPENROUTER_API_KEY_{i}")
        if key:
            openrouter_keys.append(f"KEY_{i}: {key[:8]}...")
    
    ollama_keys = []
    for name in ["OLLAMA_API_KEY", "OLLAMA_API_KEY_2"]:
        key = os.getenv(name)
        if key:
            ollama_keys.append(f"{name}: {key[:8]}...")
    
    print(f"   OpenRouter keys: {len(openrouter_keys)}/3")
    for key in openrouter_keys:
        print(f"      {key}")
    
    print(f"   Ollama keys: {len(ollama_keys)}/2")
    for key in ollama_keys:
        print(f"      {key}")
    
    if not openrouter_keys and not ollama_keys:
        print("\n❌ No API keys found!")
        return
    
    # Initialize router
    print("\nInitializing router...")
    router = MultiProviderRouter()
    
    # Test 1: OpenRouter
    if openrouter_keys:
        print("\n" + "="*60)
        print("TEST 1: OpenRouter Free Tier")
        print("="*60)
        
        messages = [{"role": "user", "content": "Say hello in exactly 5 words"}]
        
        try:
            response = await router.chat(messages, prefer_provider="openrouter")
            print(f"✅ SUCCESS!")
            print(f"   Provider: {response.provider}")
            print(f"   Model: {response.model}")
            print(f"   Key: {response.key_id}")
            print(f"   Response: {response.content}")
            print(f"   Tokens: {response.tokens_used}")
            print(f"   Latency: {response.latency_ms:.0f}ms")
        except Exception as e:
            print(f"❌ FAILED: {e}")
    
    # Test 2: Ollama
    if ollama_keys:
        print("\n" + "="*60)
        print("TEST 2: Ollama Cloud")
        print("="*60)
        
        messages = [{"role": "user", "content": "Say 'test' once"}]
        
        try:
            response = await router.chat(
                messages,
                model="llama3.2:3b",
                prefer_provider="ollama"
            )
            print(f"✅ SUCCESS!")
            print(f"   Provider: {response.provider}")
            print(f"   Model: {response.model}")
            print(f"   Key: {response.key_id}")
            print(f"   Response: {response.content}")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            print("   (May be normal if model not available)")
    
    # Test 3: Key cycling
    if openrouter_keys:
        print("\n" + "="*60)
        print("TEST 3: Key Cycling")
        print("="*60)
        
        messages = [{"role": "user", "content": "Say 'ok'"}]
        keys_used = set()
        
        for i in range(min(5, len(openrouter_keys) * 2)):
            try:
                response = await router.chat(messages, prefer_provider="openrouter")
                keys_used.add(response.key_id)
                print(f"   Request {i+1}: Key {response.key_id}")
            except Exception as e:
                print(f"   Request {i+1}: Failed")
        
        print(f"\n✅ Used {len(keys_used)} different keys")
    
    # Test 4: Router status
    print("\n" + "="*60)
    print("TEST 4: Router Status")
    print("="*60)
    
    status = router.get_status()
    print(f"\nProviders: {len(status['providers'])}")
    for provider in status['providers']:
        print(f"\n{provider['name']}:")
        print(f"   Keys: {provider['num_keys']}")
        print(f"   Endpoint: {provider['endpoint']}")
    
    print("\n" + "="*70)
    print("✅ Tests Complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
