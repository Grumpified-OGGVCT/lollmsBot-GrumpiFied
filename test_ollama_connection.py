#!/usr/bin/env python3
"""
Test script to verify Ollama Cloud API access.

Checks:
1. Environment variables for API key
2. Tests connection to Ollama Cloud
3. Lists available models
4. Tests basic model call
"""

import os
import sys
import requests
import json
from typing import Optional

# Possible environment variable names for Ollama API key
POSSIBLE_ENV_VARS = [
    "OLLAMA_API_KEY",
    "OLLAMA_CLOUD_API_KEY",
    "OLLAMA_KEY",
    "RC2_API_KEY",
    "RC2_OLLAMA_KEY",
]

OLLAMA_CLOUD_BASE = "https://api.ollama.cloud"  # Adjust if different


def find_api_key() -> Optional[str]:
    """Search for Ollama API key in environment variables."""
    print("🔍 Searching for Ollama API key in environment variables...")
    
    for var_name in POSSIBLE_ENV_VARS:
        value = os.getenv(var_name)
        if value:
            print(f"✅ Found API key in: {var_name}")
            # Mask the key for security
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"   Key (masked): {masked}")
            return value
    
    # Check all env vars for anything that looks like an API key
    print("\n🔎 Checking all environment variables for 'ollama' or 'api'...")
    for key, value in os.environ.items():
        if 'ollama' in key.lower() or ('api' in key.lower() and 'key' in key.lower()):
            print(f"   Found: {key} = {value[:20]}..." if len(value) > 20 else f"   Found: {key} = {value}")
    
    print("\n❌ No Ollama API key found in environment variables")
    return None


def test_ollama_connection(api_key: str) -> bool:
    """Test connection to Ollama Cloud API."""
    print("\n🌐 Testing Ollama Cloud connection...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Try to list models endpoint
        response = requests.get(
            f"{OLLAMA_CLOUD_BASE}/api/tags",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Successfully connected to Ollama Cloud!")
            return True
        elif response.status_code == 401:
            print(f"❌ Authentication failed (401) - API key may be invalid")
            return False
        else:
            print(f"⚠️  Unexpected response code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def list_available_models(api_key: str):
    """List available models on Ollama Cloud."""
    print("\n📋 Fetching available models...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{OLLAMA_CLOUD_BASE}/api/tags",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Found {len(models.get('models', []))} models:")
            
            # List RC2-relevant models
            rc2_models = [
                "kimi-k2.5", "mistral-large-3",
                "deepseek-v3.1:671b", "cogito-2.1:671b",
                "gemini-3-flash-preview", "qwen3-next:80b",
                "ministral-3:8b", "qwen3-coder-next",
                "devstral-small-2:24b", "devstral-2:123b",
                "nemotron-3-nano:30b", "qwen3-vl:4b",
                "glm-4.7", "rnj-1:8b", "gpt-oss:120b",
                "gemma3:27b", "minimax-m2.1"
            ]
            
            found_models = []
            for model in models.get('models', []):
                model_name = model.get('name', '')
                found_models.append(model_name)
                
                # Check if it's an RC2 model
                is_rc2 = any(rc2 in model_name for rc2 in rc2_models)
                marker = "⭐" if is_rc2 else "  "
                print(f"   {marker} {model_name}")
            
            # Check which RC2 models are available
            print("\n🎯 RC2 Model Availability Check:")
            for rc2_model in rc2_models:
                available = any(rc2_model in fm for fm in found_models)
                status = "✅" if available else "❌"
                print(f"   {status} {rc2_model}")
                
        else:
            print(f"❌ Failed to fetch models: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")


def test_model_call(api_key: str):
    """Test a simple model call."""
    print("\n🧪 Testing model call (using small model if available)...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gemini-3-flash-preview",  # Try a fast model
        "prompt": "Respond with exactly: 'Connection successful'",
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_CLOUD_BASE}/api/generate",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Model call successful!")
            print(f"   Response: {result.get('response', '')[:100]}")
        else:
            print(f"❌ Model call failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error testing model call: {e}")


def check_github_secrets():
    """Check if running in GitHub Actions and look for secrets."""
    print("\n🔐 Checking GitHub Actions environment...")
    
    if os.getenv("GITHUB_ACTIONS") == "true":
        print("✅ Running in GitHub Actions")
        print(f"   Repository: {os.getenv('GITHUB_REPOSITORY')}")
        print(f"   Workflow: {os.getenv('GITHUB_WORKFLOW')}")
        
        print("\n📝 Note: GitHub Secrets are not directly accessible in code.")
        print("   They must be explicitly passed as environment variables in the workflow.")
        print("   Check .github/workflows/*.yml for secret mappings.")
    else:
        print("ℹ️  Not running in GitHub Actions (running locally)")


def main():
    print("=" * 70)
    print("🧪 Ollama Cloud API Connection Test")
    print("=" * 70)
    
    # Check GitHub environment
    check_github_secrets()
    
    # Find API key
    api_key = find_api_key()
    
    if not api_key:
        print("\n" + "=" * 70)
        print("❌ CONCLUSION: No API key found")
        print("=" * 70)
        print("\n💡 To fix:")
        print("   1. Set OLLAMA_API_KEY environment variable")
        print("   2. Or configure in .github/workflows/ if using GitHub Actions")
        print("   3. Or add to repository secrets and map in workflow")
        sys.exit(1)
    
    # Test connection
    if not test_ollama_connection(api_key):
        print("\n" + "=" * 70)
        print("❌ CONCLUSION: Could not connect to Ollama Cloud")
        print("=" * 70)
        sys.exit(1)
    
    # List models
    list_available_models(api_key)
    
    # Test model call
    test_model_call(api_key)
    
    print("\n" + "=" * 70)
    print("✅ CONCLUSION: Ollama Cloud access verified!")
    print("=" * 70)
    print("\n✨ Ready to implement RC2 with Ollama Cloud models")


if __name__ == "__main__":
    main()
