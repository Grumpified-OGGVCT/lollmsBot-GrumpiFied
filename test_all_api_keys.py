#!/usr/bin/env python3
"""
Comprehensive API Key Testing for Multiple Providers
Tests all available API keys (Ollama + OpenRouter) and reports capabilities.
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Tuple

def test_ollama_key(key_name: str, api_key: str) -> Dict:
    """Test an Ollama API key and return results."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing {key_name}")
    print(f"{'='*60}")
    
    result = {
        "key_name": key_name,
        "provider": "Ollama",
        "status": "unknown",
        "models_available": [],
        "test_inference": None,
        "latency_ms": None,
        "error": None
    }
    
    # Official Ollama Cloud endpoint from documentation
    # https://docs.ollama.com/cloud
    endpoints = [
        "https://ollama.com/api",  # Official endpoint
    ]
    
    for endpoint in endpoints:
        print(f"  Trying endpoint: {endpoint}")
        try:
            import requests
            
            # Test list models (Ollama uses /api/tags for listing)
            start_time = time.time()
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{endpoint}/tags",  # Ollama uses /tags not /models
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                latency = (time.time() - start_time) * 1000
                result["latency_ms"] = round(latency, 2)
                result["status"] = "success"
                
                # Parse models (Ollama format: {"models": [...]})
                data = response.json()
                if isinstance(data, dict) and "models" in data:
                    models = data["models"]
                elif isinstance(data, list):
                    models = data
                else:
                    models = []
                
                result["models_available"] = [m.get("name", m.get("model", str(m))) for m in models[:10]]
                
                print(f"  ✅ Connection successful!")
                print(f"  ⚡ Latency: {latency:.2f}ms")
                print(f"  📋 Found {len(models)} models")
                
                # Test inference
                try:
                    inference_response = requests.post(
                        f"{endpoint}/chat/completions",
                        headers=headers,
                        json={
                            "model": result["models_available"][0] if result["models_available"] else "mistral",
                            "messages": [{"role": "user", "content": "Say 'OK'"}],
                            "max_tokens": 5
                        },
                        timeout=30
                    )
                    
                    if inference_response.status_code == 200:
                        result["test_inference"] = "success"
                        print(f"  ✅ Inference test passed")
                    else:
                        result["test_inference"] = f"failed: {inference_response.status_code}"
                        print(f"  ⚠️  Inference test failed: {inference_response.status_code}")
                except Exception as e:
                    result["test_inference"] = f"error: {str(e)}"
                    print(f"  ⚠️  Inference error: {e}")
                
                break  # Success, stop trying endpoints
            else:
                print(f"  ❌ Status {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            result["error"] = str(e)
    
    if result["status"] == "unknown":
        result["status"] = "failed"
        print(f"  ❌ All endpoints failed for {key_name}")
    
    return result


def test_openrouter_key(key_name: str, api_key: str) -> Dict:
    """Test an OpenRouter API key and return results."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing {key_name}")
    print(f"{'='*60}")
    
    result = {
        "key_name": key_name,
        "provider": "OpenRouter",
        "status": "unknown",
        "models_available": [],
        "test_inference": None,
        "latency_ms": None,
        "error": None
    }
    
    # Official OpenRouter endpoint from documentation
    endpoint = "https://openrouter.ai/api/v1"
    
    try:
        import requests
        
        # Test list models
        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Grumpified-OGGVCT/lollmsBot-GrumpiFied",
            "X-Title": "LollmsBot"
        }
        
        response = requests.get(
            f"{endpoint}/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            latency = (time.time() - start_time) * 1000
            result["latency_ms"] = round(latency, 2)
            result["status"] = "success"
            
            # Parse models
            data = response.json()
            models = data.get("data", [])
            
            result["models_available"] = [m.get("id", m.get("name", "")) for m in models[:15]]
            
            print(f"  ✅ Connection successful!")
            print(f"  ⚡ Latency: {latency:.2f}ms")
            print(f"  📋 Found {len(models)} models")
            print(f"  🎯 Sample models: {', '.join(result['models_available'][:5])}")
            
            # Test inference with OpenRouter's free model router
            # https://openrouter.ai/docs/guides/routing/routers/free-router
            try:
                inference_response = requests.post(
                    f"{endpoint}/chat/completions",
                    headers=headers,
                    json={
                        "model": "openrouter/free",  # Free Models Router
                        "messages": [{"role": "user", "content": "Say 'OK'"}],
                        "max_tokens": 5
                    },
                    timeout=30
                )
                
                if inference_response.status_code == 200:
                    result["test_inference"] = "success"
                    resp_data = inference_response.json()
                    # Log which free model was actually used
                    actual_model = resp_data.get("model", "unknown")
                    print(f"  ✅ Inference test passed (used: {actual_model})")
                else:
                    result["test_inference"] = f"failed: {inference_response.status_code}"
                    print(f"  ⚠️  Inference test failed: {inference_response.status_code}")
            except Exception as e:
                result["test_inference"] = f"error: {str(e)}"
                print(f"  ⚠️  Inference error: {e}")
                
        else:
            print(f"  ❌ Status {response.status_code}: {response.text[:100]}")
            result["status"] = "failed"
            result["error"] = f"HTTP {response.status_code}"
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        result["status"] = "failed"
        result["error"] = str(e)
    
    return result


def main():
    """Test all available API keys."""
    print("\n" + "="*60)
    print("🚀 Multi-Provider API Key Test Suite")
    print("="*60)
    
    # Check for API keys
    ollama_keys = {
        "OLLAMA_API_KEY": os.getenv("OLLAMA_API_KEY"),
        "OLLAMA_API_KEY_2": os.getenv("OLLAMA_API_KEY_2"),
    }
    
    openrouter_keys = {
        "OPENROUTER_API_KEY_1": os.getenv("OPENROUTER_API_KEY_1"),
        "OPENROUTER_API_KEY_2": os.getenv("OPENROUTER_API_KEY_2"),
        "OPENROUTER_API_KEY_3": os.getenv("OPENROUTER_API_KEY_3"),
    }
    
    all_results = []
    
    # Test Ollama keys
    print("\n" + "🔷 OLLAMA API KEYS".center(60, "="))
    for key_name, api_key in ollama_keys.items():
        if api_key:
            result = test_ollama_key(key_name, api_key)
            all_results.append(result)
        else:
            print(f"\n⚠️  {key_name} not found in environment")
    
    # Test OpenRouter keys
    print("\n" + "🔶 OPENROUTER API KEYS".center(60, "="))
    for key_name, api_key in openrouter_keys.items():
        if api_key:
            result = test_openrouter_key(key_name, api_key)
            all_results.append(result)
        else:
            print(f"\n⚠️  {key_name} not found in environment")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    successful_keys = [r for r in all_results if r["status"] == "success"]
    failed_keys = [r for r in all_results if r["status"] == "failed"]
    
    print(f"\n✅ Successful: {len(successful_keys)}/{len(all_results)}")
    for result in successful_keys:
        inference_status = "✅" if result["test_inference"] == "success" else "⚠️"
        print(f"  {inference_status} {result['key_name']:25} - {len(result['models_available'])} models, {result['latency_ms']}ms")
    
    if failed_keys:
        print(f"\n❌ Failed: {len(failed_keys)}/{len(all_results)}")
        for result in failed_keys:
            print(f"  ❌ {result['key_name']:25} - {result.get('error', 'Unknown error')}")
    
    # RC2 Model Check
    print("\n" + "="*60)
    print("🎯 RC2 MODEL AVAILABILITY CHECK")
    print("="*60)
    
    rc2_models = [
        "kimi-k2.5",
        "deepseek-v3.1:671b",
        "cogito-2.1:671b",
        "mistral-large-3",
        "gemini-3-flash-preview",
        "qwen3-next:80b",
        "ministral-3:8b",
        "qwen3-coder-next",
        "devstral-small-2:24b",
        "minimax-m2.1",
        "devstral-2:123b",
        "nomic-embed-text-v2-moe",
        "kimi-k2-thinking",
        "nemotron-3-nano:30b",
        "qwen3-vl:4b",
        "glm-4.7",
        "rnj-1:8b",
    ]
    
    # Check which provider has which models
    all_models = []
    for result in successful_keys:
        all_models.extend(result["models_available"])
    
    for model in rc2_models:
        found = False
        for result in successful_keys:
            if any(model.lower() in m.lower() for m in result["models_available"]):
                print(f"  ✅ {model:30} - Available on {result['key_name']}")
                found = True
                break
        if not found:
            print(f"  ❌ {model:30} - NOT FOUND")
    
    # Recommendations
    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS")
    print("="*60)
    
    if len(successful_keys) >= 2:
        print("  ✅ Multiple keys working - can implement failover")
    if any(r["provider"] == "Ollama" for r in successful_keys):
        print("  ✅ Ollama working - can use for RC2 pillars")
    if any(r["provider"] == "OpenRouter" for r in successful_keys):
        print("  ✅ OpenRouter working - good fallback option")
    
    if len(successful_keys) >= 3:
        print("  🚀 Excellent! Can implement load balancing across keys")
    
    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)
    
    # Exit code
    sys.exit(0 if len(successful_keys) > 0 else 1)


if __name__ == "__main__":
    main()
