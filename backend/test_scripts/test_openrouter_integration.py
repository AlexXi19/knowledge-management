#!/usr/bin/env python3
"""
Test script for OpenRouter integration with LiteLLM
Tests the knowledge agent's OpenRouter model setup and basic functionality
"""

import os
import sys
import asyncio
import json
from typing import Dict, Any

# Add the parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.knowledge_agent import KnowledgeAgent
from litellm import completion
import litellm


def test_direct_openrouter_litellm():
    """Test direct OpenRouter integration with LiteLLM"""
    print("🧪 Testing direct OpenRouter integration with LiteLLM...")
    
    # Check if API key is set
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY environment variable not set")
        return False
    
    # Set up environment variables
    os.environ["OPENROUTER_API_KEY"] = api_key
    
    # Optional: Set site URL and app name
    site_url = os.getenv("OR_SITE_URL", "")
    app_name = os.getenv("OR_APP_NAME", "Knowledge-Management-Test")
    
    if site_url:
        os.environ["OR_SITE_URL"] = site_url
    if app_name:
        os.environ["OR_APP_NAME"] = app_name
    
    try:
        # Test with the corrected OpenRouter model format
        model_name = "openrouter/anthropic/claude-3.5-sonnet"
        
        print(f"📡 Testing model: {model_name}")
        
        # Make a simple test completion
        response = completion(
            model=model_name,
            messages=[
                {"role": "user", "content": "Hello! Please respond with just 'OpenRouter working' to confirm the connection."}
            ],
            max_tokens=50
        )
        
        print("✅ Direct OpenRouter test successful!")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Direct OpenRouter test failed: {e}")
        return False


def test_knowledge_agent_openrouter():
    """Test the knowledge agent with OpenRouter model"""
    print("\n🧪 Testing KnowledgeAgent with OpenRouter...")
    
    # Check if API key is set
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY environment variable not set")
        return False
    
    try:
        # Set the model preference to ensure OpenRouter is used
        os.environ["OPENROUTER_MODEL"] = "anthropic/claude-3.5-sonnet"
        
        # Create knowledge agent in test directory
        test_dir = os.path.join(os.path.dirname(__file__), "test_openrouter_notes")
        os.makedirs(test_dir, exist_ok=True)
        
        agent = KnowledgeAgent(dir=test_dir)
        
        # Check if OpenRouter model was selected
        if not agent.model:
            print("❌ No model was initialized")
            return False
            
        print(f"✅ Knowledge agent initialized with model")
        
        # Test a simple message processing
        async def test_message():
            test_message = "This is a test note for OpenRouter integration. Please create a simple note."
            
            try:
                response = await agent.process_message(test_message)
                print(f"✅ Message processing successful!")
                print(f"   Response: {response.response[:100]}...")
                return True
            except Exception as e:
                print(f"❌ Message processing failed: {e}")
                return False
        
        # Run the async test
        result = asyncio.run(test_message())
        
        # Clean up test directory
        import shutil
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        
        return result
        
    except Exception as e:
        print(f"❌ KnowledgeAgent OpenRouter test failed: {e}")
        return False


def test_openrouter_models_list():
    """Test different OpenRouter models"""
    print("\n🧪 Testing different OpenRouter models...")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY environment variable not set")
        return False
    
    # List of models to test
    test_models = [
        "openrouter/anthropic/claude-3.5-sonnet",
        "openrouter/openai/gpt-4o-mini",
        "openrouter/meta-llama/llama-3.1-8b-instruct:free",
        "openrouter/google/gemini-flash-1.5"
    ]
    
    successful_models = []
    
    for model in test_models:
        try:
            print(f"📡 Testing model: {model}")
            
            response = completion(
                model=model,
                messages=[
                    {"role": "user", "content": "Respond with just 'OK' to confirm this model works."}
                ],
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip()
            print(f"   ✅ {model}: {result}")
            successful_models.append(model)
            
        except Exception as e:
            print(f"   ❌ {model}: {str(e)[:100]}...")
    
    if successful_models:
        print(f"\n✅ {len(successful_models)} out of {len(test_models)} models working")
        return True
    else:
        print("\n❌ No models working")
        return False


def display_openrouter_config():
    """Display current OpenRouter configuration"""
    print("\n📋 Current OpenRouter Configuration:")
    print("=" * 50)
    
    # Check environment variables
    config = {
        "OPENROUTER_API_KEY": "Set" if os.getenv("OPENROUTER_API_KEY") else "Not set",
        "OPENROUTER_MODEL": os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet (default)"),
        "OR_SITE_URL": os.getenv("OR_SITE_URL", "Not set"),
        "OR_APP_NAME": os.getenv("OR_APP_NAME", "Not set"),
        "DEBUG": os.getenv("DEBUG", "false")
    }
    
    for key, value in config.items():
        print(f"   {key}: {value}")
    
    print("=" * 50)


def main():
    """Main test function"""
    print("🚀 OpenRouter Integration Test Suite")
    print("=" * 60)
    
    # Display configuration
    display_openrouter_config()
    
    # Enable debug mode for detailed error information
    if os.getenv("DEBUG") == "true":
        litellm.set_verbose = True
    
    # Run tests
    tests = [
        ("Direct OpenRouter LiteLLM", test_direct_openrouter_litellm),
        ("KnowledgeAgent OpenRouter", test_knowledge_agent_openrouter),
        ("OpenRouter Models List", test_openrouter_models_list)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' encountered an error: {e}")
            results[test_name] = False
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary")
    print(f"{'='*60}")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    print(f"\n📈 Overall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All tests passed! OpenRouter integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 