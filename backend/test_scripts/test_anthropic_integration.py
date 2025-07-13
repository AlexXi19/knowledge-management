#!/usr/bin/env python3
"""
Test script for Anthropic Claude Sonnet integration in the knowledge management system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from agent.knowledge_agent import KnowledgeAgent

async def test_anthropic_setup():
    """Test if Anthropic Claude models can be properly initialized"""
    print("🧪 Testing Anthropic Claude Sonnet integration...")
    
    # Check if Anthropic API key is available
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not found in environment variables")
        print("   Please set your Anthropic API key to test Claude integration:")
        print("   export ANTHROPIC_API_KEY=your_api_key_here")
        return False
    
    # Check which Claude model is configured
    claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    print(f"🤖 Testing with Claude model: {claude_model}")
    
    try:
        # Initialize the agent (should use Claude if API key is available)
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Check if the model was properly set up
        if hasattr(agent, 'model_name') and 'claude' in agent.model_name.lower():
            print(f"✅ Successfully initialized with {agent.model_name}")
        else:
            print(f"⚠️  Agent initialized but not using Claude model: {getattr(agent, 'model_name', 'unknown')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing agent with Claude: {e}")
        return False

async def test_claude_conversation():
    """Test a simple conversation with Claude Sonnet"""
    print("\n🧪 Testing Claude conversation capabilities...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test a simple knowledge management task
        test_message = "Create a note about the benefits of using Claude Sonnet for knowledge management"
        
        print(f"💭 Sending test message: {test_message}")
        response = await agent.process_message(test_message)
        
        print(f"🤖 Claude response received:")
        print(f"   Categories: {response.categories}")
        print(f"   Response length: {len(response.response)} characters")
        print(f"   Knowledge updates: {len(response.knowledge_updates)}")
        print(f"   Suggested actions: {len(response.suggested_actions)}")
        
        # Check if the response looks reasonable
        if len(response.response) > 50 and any(cat in ["Learning", "Research", "Ideas to Develop"] for cat in response.categories):
            print("✅ Claude conversation test successful!")
            return True
        else:
            print("⚠️  Claude response seems incomplete or unexpected")
            return False
            
    except Exception as e:
        print(f"❌ Error in Claude conversation: {e}")
        return False

async def test_claude_performance():
    """Test Claude's performance with knowledge management tasks"""
    print("\n🧪 Testing Claude performance with complex tasks...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test more complex knowledge management scenarios
        test_scenarios = [
            "Analyze and categorize this research: Machine learning transformers have revolutionized natural language processing",
            "Create a comprehensive note about the pros and cons of different LLM providers",
            "Search for existing notes about AI and suggest connections to reinforcement learning"
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
        print(f"\n📊 Claude performance test results: {success_count}/{len(test_scenarios)} ({success_rate:.1f}% success rate)")
        
        return success_rate >= 66.7  # At least 2/3 tests should pass
        
    except Exception as e:
        print(f"❌ Error in Claude performance testing: {e}")
        return False

async def test_claude_vs_other_models():
    """Compare Claude with other available models"""
    print("\n🧪 Testing model selection priority...")
    
    # Test with different environment setups
    original_anthropic = os.environ.get("ANTHROPIC_API_KEY")
    original_openai = os.environ.get("OPENAI_API_KEY")
    
    try:
        # Test 1: Only Anthropic key (should use Claude)
        if original_anthropic:
            os.environ.pop("OPENAI_API_KEY", None)
            agent = KnowledgeAgent()
            if hasattr(agent, 'model_name') and 'claude' in agent.model_name.lower():
                print("✅ Priority test 1 passed: Claude selected when Anthropic key available")
            else:
                print(f"⚠️  Priority test 1 failed: Expected Claude, got {getattr(agent, 'model_name', 'unknown')}")
        
        # Test 2: Restore OpenAI key (Claude should still have priority)
        if original_openai:
            os.environ["OPENAI_API_KEY"] = original_openai
            agent = KnowledgeAgent()
            if hasattr(agent, 'model_name') and 'claude' in agent.model_name.lower():
                print("✅ Priority test 2 passed: Claude still selected when both keys available")
            else:
                print(f"⚠️  Priority test 2 failed: Expected Claude, got {getattr(agent, 'model_name', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in model priority testing: {e}")
        return False
    finally:
        # Restore original environment
        if original_anthropic:
            os.environ["ANTHROPIC_API_KEY"] = original_anthropic
        if original_openai:
            os.environ["OPENAI_API_KEY"] = original_openai

async def main():
    """Run all Anthropic Claude integration tests"""
    print("🚀 Starting Anthropic Claude Sonnet integration tests...")
    print("=" * 70)
    
    tests = [
        ("Anthropic Setup", test_anthropic_setup),
        ("Claude Conversation", test_claude_conversation),
        ("Claude Performance", test_claude_performance),
        ("Model Priority", test_claude_vs_other_models)
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
        print("🎉 All Anthropic Claude integration tests passed!")
        print("🤖 Your system is ready to use Claude Sonnet models!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("💡 Tip: Make sure to set ANTHROPIC_API_KEY to test Claude integration")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 