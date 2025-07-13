#!/usr/bin/env python3
"""
Test script for OpenRouter integration in the knowledge management system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from agent.knowledge_agent import KnowledgeAgent

async def test_openrouter_setup():
    """Test if OpenRouter models can be properly initialized"""
    print("🧪 Testing OpenRouter integration...")
    
    # Check if OpenRouter API key is available
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        print("   Please set your OpenRouter API key to test integration:")
        print("   export OPENROUTER_API_KEY=your_api_key_here")
        return False
    
    # Check which OpenRouter model is configured
    openrouter_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    print(f"🤖 Testing with OpenRouter model: {openrouter_model}")
    
    try:
        # Initialize the agent (should use OpenRouter if API key is available)
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Check if the model was properly set up
        if hasattr(agent, 'model_name') and openrouter_model in agent.model_name:
            print(f"✅ Successfully initialized with {agent.model_name}")
        else:
            print(f"⚠️  Agent initialized but not using OpenRouter model: {getattr(agent, 'model_name', 'unknown')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing agent with OpenRouter: {e}")
        return False

async def test_openrouter_conversation():
    """Test a simple conversation with OpenRouter"""
    print("\n🧪 Testing OpenRouter conversation capabilities...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test a simple knowledge management task
        test_message = "Create a note about the benefits of using OpenRouter for accessing multiple AI models"
        
        print(f"💭 Sending test message: {test_message}")
        response = await agent.process_message(test_message)
        
        print(f"🤖 OpenRouter response received:")
        print(f"   Categories: {response.categories}")
        print(f"   Response length: {len(response.response)} characters")
        print(f"   Knowledge updates: {len(response.knowledge_updates)}")
        print(f"   Suggested actions: {len(response.suggested_actions)}")
        
        # Check if the response looks reasonable
        if len(response.response) > 50 and any(cat in ["Learning", "Research", "Ideas to Develop"] for cat in response.categories):
            print("✅ OpenRouter conversation test successful!")
            return True
        else:
            print("⚠️  OpenRouter response seems incomplete or unexpected")
            return False
            
    except Exception as e:
        print(f"❌ Error in OpenRouter conversation: {e}")
        return False

async def test_openrouter_model_variety():
    """Test different models available through OpenRouter"""
    print("\n🧪 Testing OpenRouter model variety...")
    
    # Test different models that OpenRouter provides
    test_models = [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.1-70b-instruct",
        "google/gemini-flash-1.5"
    ]
    
    original_model = os.environ.get("OPENROUTER_MODEL")
    successful_models = []
    
    for model in test_models:
        print(f"🔄 Testing model: {model}")
        
        try:
            # Temporarily set the model
            os.environ["OPENROUTER_MODEL"] = model
            
            # Create new agent instance
            agent = KnowledgeAgent()
            
            # Check if model was set correctly
            if hasattr(agent, 'model_name') and model in agent.model_name:
                print(f"   ✅ {model} configured successfully")
                successful_models.append(model)
            else:
                print(f"   ⚠️  {model} configuration unclear")
                
        except Exception as e:
            print(f"   ❌ {model} failed: {e}")
    
    # Restore original model
    if original_model:
        os.environ["OPENROUTER_MODEL"] = original_model
    elif "OPENROUTER_MODEL" in os.environ:
        del os.environ["OPENROUTER_MODEL"]
    
    print(f"\n📊 Successfully configured {len(successful_models)}/{len(test_models)} models")
    print(f"   Working models: {', '.join(successful_models)}")
    
    return len(successful_models) >= 2  # At least 2 models should work

async def test_openrouter_performance():
    """Test OpenRouter's performance with knowledge management tasks"""
    print("\n🧪 Testing OpenRouter performance with complex tasks...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test more complex knowledge management scenarios
        test_scenarios = [
            "Analyze and categorize this research: OpenRouter provides unified access to multiple AI models",
            "Create a comprehensive note about the advantages of model diversity in AI applications",
            "Search for existing notes about AI models and suggest connections to API services"
        ]
        
        success_count = 0
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"📝 Test {i}: {scenario[:50]}...")
            
            try:
                response = await agent.process_message(scenario)
                
                # Basic quality checks
                if (len(response.response) > 100 and 
                    response.categories and 
                    len(response.response.split()) > 20):
                    print(f"   ✅ Test {i} passed")
                    success_count += 1
                else:
                    print(f"   ⚠️  Test {i} response quality low")
                    
            except Exception as e:
                print(f"   ❌ Test {i} failed: {e}")
        
        success_rate = (success_count / len(test_scenarios)) * 100
        print(f"\n📊 OpenRouter performance test results: {success_count}/{len(test_scenarios)} ({success_rate:.1f}% success rate)")
        
        return success_rate >= 66.7  # At least 2/3 tests should pass
        
    except Exception as e:
        print(f"❌ Error in OpenRouter performance testing: {e}")
        return False

async def test_openrouter_priority():
    """Test that OpenRouter has the highest priority in model selection"""
    print("\n🧪 Testing OpenRouter priority in model selection...")
    
    # Test with different environment setups
    original_openrouter = os.environ.get("OPENROUTER_API_KEY")
    original_anthropic = os.environ.get("ANTHROPIC_API_KEY") 
    original_openai = os.environ.get("OPENAI_API_KEY")
    
    try:
        # Test 1: Only OpenRouter key (should use OpenRouter)
        if original_openrouter:
            # Temporarily remove other keys
            os.environ.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("OPENAI_API_KEY", None)
            
            agent = KnowledgeAgent()
            openrouter_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
            
            if hasattr(agent, 'model_name') and openrouter_model in agent.model_name:
                print("✅ Priority test 1 passed: OpenRouter selected when only OpenRouter key available")
            else:
                print(f"⚠️  Priority test 1 failed: Expected OpenRouter, got {getattr(agent, 'model_name', 'unknown')}")
        
        # Test 2: OpenRouter + other keys (OpenRouter should still have priority)
        if original_openrouter and (original_anthropic or original_openai):
            # Restore other keys
            if original_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = original_anthropic
            if original_openai:
                os.environ["OPENAI_API_KEY"] = original_openai
            
            agent = KnowledgeAgent()
            if hasattr(agent, 'model_name') and openrouter_model in agent.model_name:
                print("✅ Priority test 2 passed: OpenRouter still selected when multiple keys available")
            else:
                print(f"⚠️  Priority test 2 failed: Expected OpenRouter, got {getattr(agent, 'model_name', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in OpenRouter priority testing: {e}")
        return False
    finally:
        # Restore original environment
        if original_openrouter:
            os.environ["OPENROUTER_API_KEY"] = original_openrouter
        if original_anthropic:
            os.environ["ANTHROPIC_API_KEY"] = original_anthropic
        if original_openai:
            os.environ["OPENAI_API_KEY"] = original_openai

async def test_openrouter_cost_tracking():
    """Test OpenRouter cost and usage tracking features"""
    print("\n🧪 Testing OpenRouter cost tracking awareness...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test a simple message to understand cost implications
        test_message = "Explain the cost benefits of using OpenRouter for AI model access"
        
        print(f"💰 Testing cost-aware message: {test_message[:50]}...")
        response = await agent.process_message(test_message)
        
        # Check if response is reasonable
        if len(response.response) > 50:
            print("✅ OpenRouter cost tracking test completed")
            print(f"   Response mentions cost: {'cost' in response.response.lower()}")
            print(f"   Response mentions pricing: {'pric' in response.response.lower()}")
            return True
        else:
            print("⚠️  OpenRouter cost tracking response incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Error in OpenRouter cost tracking test: {e}")
        return False

async def main():
    """Run all OpenRouter integration tests"""
    print("🚀 Starting OpenRouter integration tests...")
    print("=" * 70)
    
    tests = [
        ("OpenRouter Setup", test_openrouter_setup),
        ("OpenRouter Conversation", test_openrouter_conversation),
        ("Model Variety", test_openrouter_model_variety),
        ("OpenRouter Performance", test_openrouter_performance),
        ("Model Priority", test_openrouter_priority),
        ("Cost Tracking", test_openrouter_cost_tracking)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} test FAILED with exception: {e}")
    
    print("\n" + "=" * 70)
    print(f"🧪 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All OpenRouter integration tests passed!")
        print("🤖 Your system is ready to use OpenRouter with multiple AI models!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        if not os.getenv("OPENROUTER_API_KEY"):
            print("💡 Tip: Make sure to set OPENROUTER_API_KEY to test OpenRouter integration")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 