#!/usr/bin/env python3
"""Test multi-provider system with live API keys."""

import asyncio
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lollmsbot.providers import MultiProviderRouter


async def test_openrouter_free():
    """Test OpenRouter free tier with all 3 keys."""
    print("\n" + "="*60)
    print("TEST 1: OpenRouter Free Tier (3 keys cycling)")
    print("="*60)
    
    router = MultiProviderRouter()
    
    # Test with simple message
    messages = [{"role": "user", "content": "Say hello in exactly 5 words"}]
    
    try:
        response = await router.chat(messages, prefer_provider="openrouter")
        print(f"✅ OpenRouter Success!")
        print(f"   Provider: {response.provider}")
        print(f"   Model used: {response.model}")
        print(f"   Key: {response.key_id}")
        print(f"   Response: {response.content}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Latency: {response.latency_ms:.0f}ms")
        print(f"   Cost: ${response.cost:.4f}")
        return True
    except Exception as e:
        print(f"❌ OpenRouter Failed: {e}")
        return False


async def test_ollama():
    """Test Ollama Cloud with load balancing."""
    print("\n" + "="*60)
    print("TEST 2: Ollama Cloud (2 keys load balancing)")
    print("="*60)
    
    router = MultiProviderRouter()
    
    # Test with a simple model (if available)
    messages = [{"role": "user", "content": "Say hello in exactly 5 words"}]
    
    try:
        # Try with a common Ollama model
        response = await router.chat(
            messages,
            model="llama3.2:3b",
            prefer_provider="ollama"
        )
        print(f"✅ Ollama Success!")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Key: {response.key_id}")
        print(f"   Response: {response.content}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Latency: {response.latency_ms:.0f}ms")
        print(f"   Cost: ${response.cost:.4f}")
        return True
    except Exception as e:
        print(f"❌ Ollama Failed: {e}")
        print("   (This may be normal if model not available)")
        return False


async def test_automatic_routing():
    """Test automatic provider selection."""
    print("\n" + "="*60)
    print("TEST 3: Automatic Routing (OpenRouter → Ollama fallback)")
    print("="*60)
    
    router = MultiProviderRouter()
    
    messages = [{"role": "user", "content": "What is 2+2? Answer in one word."}]
    
    try:
        response = await router.chat(messages)  # No provider specified
        print(f"✅ Auto-routing Success!")
        print(f"   Selected provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Key: {response.key_id}")
        print(f"   Response: {response.content}")
        print(f"   Latency: {response.latency_ms:.0f}ms")
        return True
    except Exception as e:
        print(f"❌ Auto-routing Failed: {e}")
        return False


async def test_quota_cycling():
    """Test key cycling through multiple requests."""
    print("\n" + "="*60)
    print("TEST 4: Key Cycling (Multiple Requests)")
    print("="*60)
    
    router = MultiProviderRouter()
    
    messages = [{"role": "user", "content": "Say 'test' once"}]
    
    keys_used = set()
    for i in range(5):
        try:
            response = await router.chat(messages, prefer_provider="openrouter")
            keys_used.add(response.key_id)
            print(f"   Request {i+1}: Key {response.key_id} - {response.content[:30]}...")
        except Exception as e:
            print(f"   Request {i+1}: Failed - {e}")
    
    print(f"\n✅ Used {len(keys_used)} different keys across 5 requests")
    return len(keys_used) > 1


async def test_model_listing():
    """Test model listing from both providers."""
    print("\n" + "="*60)
    print("TEST 5: Model Listing")
    print("="*60)
    
    router = MultiProviderRouter()
    
    try:
        models = await router.list_models()
        for provider, model_list in models.items():
            print(f"\n{provider}:")
            print(f"   Found {len(model_list)} models")
            if model_list:
                print(f"   First 5: {model_list[:5]}")
        return True
    except Exception as e:
        print(f"❌ Model listing failed: {e}")
        return False


async def test_status():
    """Test router status."""
    print("\n" + "="*60)
    print("TEST 6: Router Status")
    print("="*60)
    
    router = MultiProviderRouter()
    status = router.get_status()
    
    print(f"\nProviders configured: {len(status['providers'])}")
    for provider in status['providers']:
        print(f"\n{provider['name']}:")
        print(f"   Enabled: {provider['enabled']}")
        print(f"   Keys: {provider['num_keys']}")
        print(f"   Endpoint: {provider['endpoint']}")
    
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🚀 MULTI-PROVIDER API SYSTEM - LIVE TESTS")
    print("="*70)
    
    # Check environment
    print("\nEnvironment Check:")
    openrouter_keys = sum(1 for i in [1,2,3] if os.getenv(f"OPENROUTER_API_KEY_{i}"))
    ollama_keys = sum(1 for k in ["OLLAMA_API_KEY", "OLLAMA_API_KEY_2"] if os.getenv(k))
    print(f"   OpenRouter keys: {openrouter_keys}/3")
    print(f"   Ollama keys: {ollama_keys}/2")
    
    if openrouter_keys == 0 and ollama_keys == 0:
        print("\n❌ No API keys found in environment!")
        print("   Set OPENROUTER_API_KEY_1/2/3 and/or OLLAMA_API_KEY/OLLAMA_API_KEY_2")
        return
    
    # Run tests
    results = []
    
    results.append(("OpenRouter Free", await test_openrouter_free()))
    results.append(("Ollama Cloud", await test_ollama()))
    results.append(("Auto Routing", await test_automatic_routing()))
    results.append(("Key Cycling", await test_quota_cycling()))
    results.append(("Model Listing", await test_model_listing()))
    results.append(("Router Status", await test_status()))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Multi-provider system is working!")
    elif passed > 0:
        print(f"\n⚠️  {total-passed} test(s) failed, but some providers working")
    else:
        print("\n❌ All tests failed - check API keys and connectivity")


if __name__ == "__main__":
    asyncio.run(main())
