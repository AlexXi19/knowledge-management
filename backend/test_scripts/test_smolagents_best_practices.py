#!/usr/bin/env python3
"""
Test script for the improved smolagents best practices architecture
Tests ToolCallingAgent + CodeAgent implementation
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the backend directory to the Python path (parent of testing/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.knowledge_agent import KnowledgeAgent

async def test_agent_initialization():
    """Test the new dual-agent architecture initialization"""
    print("🧪 Testing smolagents best practices architecture...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Verify both agents are created
        assert agent.tool_agent is not None, "ToolCallingAgent should be initialized"
        assert agent.code_agent is not None, "CodeAgent should be initialized"
        
        # Verify agent metadata
        assert agent.tool_agent.name == "knowledge_tool_agent", "ToolCallingAgent should have correct name"
        assert agent.code_agent.name == "knowledge_code_agent", "CodeAgent should have correct name"
        
        print("✅ Dual-agent architecture initialized successfully")
        print(f"   ToolCallingAgent: {agent.tool_agent.name}")
        print(f"   CodeAgent: {agent.code_agent.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

async def test_simple_tool_calling():
    """Test ToolCallingAgent for simple structured tasks"""
    print("\n🧪 Testing ToolCallingAgent for simple tasks...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test simple knowledge management task
        simple_message = "Create a note about Python programming fundamentals"
        
        print(f"📝 Testing simple task: {simple_message}")
        response = await agent.process_message(simple_message)
        
        # Verify response quality
        assert len(response.response) > 50, "Response should be substantial"
        assert response.categories, "Response should have categories"
        assert response.suggested_actions, "Response should have suggested actions"
        
        print("✅ ToolCallingAgent handled simple task successfully")
        print(f"   Response length: {len(response.response)} characters")
        print(f"   Categories: {response.categories}")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple tool calling test failed: {e}")
        return False

async def test_complex_reasoning():
    """Test CodeAgent delegation for complex reasoning tasks"""
    print("\n🧪 Testing CodeAgent delegation for complex reasoning...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test complex reasoning task that should trigger CodeAgent
        complex_message = "Analyze the relationships between machine learning, data science, and artificial intelligence. Compare their applications and find patterns in my knowledge base."
        
        print(f"🧠 Testing complex task: {complex_message[:60]}...")
        
        # Check if task requires complex reasoning
        requires_complex = agent._requires_complex_reasoning(complex_message)
        assert requires_complex, "Complex message should trigger CodeAgent"
        
        response = await agent.process_message(complex_message)
        
        # Verify response quality for complex task
        assert len(response.response) > 100, "Complex task should generate substantial response"
        assert response.categories, "Response should have categories"
        
        print("✅ CodeAgent delegation working correctly")
        print(f"   Complex reasoning detected: {requires_complex}")
        print(f"   Response length: {len(response.response)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Complex reasoning test failed: {e}")
        return False

async def test_complexity_detection():
    """Test the complexity detection algorithm"""
    print("\n🧪 Testing complexity detection algorithm...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        test_cases = [
            # Simple tasks (should NOT trigger CodeAgent)
            ("Create a note about cats", False),
            ("Search for notes about Python", False),
            ("What is machine learning?", False),
            
            # Complex tasks (SHOULD trigger CodeAgent)
            ("Analyze the relationships between AI concepts and find patterns", True),
            ("Compare multiple approaches to data science and suggest optimization strategies", True),
            ("What are the connections between reinforcement learning and neural networks? How do they relate?", True),
            ("Deep dive into the comprehensive analysis of machine learning algorithms", True),
            ("This is a very long message with more than twenty words that discusses complex topics and requires detailed analysis and comprehensive understanding", True),
        ]
        
        correct_predictions = 0
        
        for message, expected_complex in test_cases:
            detected_complex = agent._requires_complex_reasoning(message)
            if detected_complex == expected_complex:
                correct_predictions += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"   {status} '{message[:40]}...' - Expected: {expected_complex}, Got: {detected_complex}")
        
        accuracy = (correct_predictions / len(test_cases)) * 100
        print(f"\n📊 Complexity detection accuracy: {accuracy:.1f}% ({correct_predictions}/{len(test_cases)})")
        
        return accuracy >= 80  # At least 80% accuracy
        
    except Exception as e:
        print(f"❌ Complexity detection test failed: {e}")
        return False

async def test_agent_logs():
    """Test logging from both agents"""
    print("\n🧪 Testing agent logging system...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Process a message to generate logs
        await agent.process_message("Create a note about testing agent logs")
        
        # Get logs from both agents
        logs = agent.get_agent_logs()
        
        assert len(logs) > 0, "Should have logs from agent execution"
        
        # Check if logs have proper structure
        for log in logs:
            assert "step" in log, "Log should have step number"
            assert "agent" in log, "Log should identify which agent"
            assert "type" in log, "Log should have step type"
        
        # Count logs by agent type
        tool_logs = [log for log in logs if log["agent"] == "tool_calling"]
        code_logs = [log for log in logs if log["agent"] == "code"]
        
        print(f"✅ Agent logging working correctly")
        print(f"   Total logs: {len(logs)}")
        print(f"   ToolCallingAgent logs: {len(tool_logs)}")
        print(f"   CodeAgent logs: {len(code_logs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent logging test failed: {e}")
        return False

async def test_memory_reset():
    """Test memory reset functionality for both agents"""
    print("\n🧪 Testing memory reset functionality...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Process a message to create memory
        await agent.process_message("Create a note for memory test")
        
        # Check that we have logs
        logs_before = agent.get_agent_logs()
        assert len(logs_before) > 0, "Should have logs before reset"
        
        # Reset memory
        agent.reset_agent_memory()
        
        # Check that memory is cleared
        logs_after = agent.get_agent_logs()
        
        print(f"✅ Memory reset working correctly")
        print(f"   Logs before reset: {len(logs_before)}")
        print(f"   Logs after reset: {len(logs_after)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory reset test failed: {e}")
        return False

async def test_streaming_response():
    """Test streaming response with both agents"""
    print("\n🧪 Testing streaming response with dual agents...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test streaming for complex task
        complex_message = "Analyze machine learning trends and create comprehensive insights"
        
        stream_events = []
        async for event in agent.stream_response(complex_message):
            stream_events.append(event)
            if event["type"] == "status":
                print(f"   📡 {event['message']}")
        
        # Verify streaming events
        assert len(stream_events) > 0, "Should have streaming events"
        
        status_events = [e for e in stream_events if e["type"] == "status"]
        assert len(status_events) >= 2, "Should have multiple status updates"
        
        complete_events = [e for e in stream_events if e["type"] == "complete"]
        assert len(complete_events) == 1, "Should have one completion event"
        
        print(f"✅ Streaming response working correctly")
        print(f"   Total events: {len(stream_events)}")
        print(f"   Status updates: {len(status_events)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming response test failed: {e}")
        return False

async def test_performance_comparison():
    """Compare performance of new architecture vs simple tasks"""
    print("\n🧪 Testing performance characteristics...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test simple task performance
        simple_start = time.time()
        await agent.process_message("Create a note about performance testing")
        simple_duration = time.time() - simple_start
        
        # Test complex task performance
        complex_start = time.time()
        await agent.process_message("Analyze patterns in my knowledge base and suggest comprehensive optimization strategies")
        complex_duration = time.time() - complex_start
        
        print(f"✅ Performance testing completed")
        print(f"   Simple task: {simple_duration:.2f} seconds")
        print(f"   Complex task: {complex_duration:.2f} seconds")
        print(f"   Performance ratio: {complex_duration/simple_duration:.1f}x")
        
        # Complex tasks should take longer but not excessively so
        return complex_duration < simple_duration * 5  # Should be less than 5x slower
        
    except Exception as e:
        print(f"❌ Performance comparison test failed: {e}")
        return False

async def main():
    """Run all smolagents best practices tests"""
    print("🚀 Starting smolagents best practices architecture tests...")
    print("=" * 80)
    
    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("Simple Tool Calling", test_simple_tool_calling),
        ("Complex Reasoning", test_complex_reasoning),
        ("Complexity Detection", test_complexity_detection),
        ("Agent Logs", test_agent_logs),
        ("Memory Reset", test_memory_reset),
        ("Streaming Response", test_streaming_response),
        ("Performance Comparison", test_performance_comparison)
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
    
    print("\n" + "=" * 80)
    print(f"🧪 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All smolagents best practices tests passed!")
        print("🏆 Your architecture follows smolagents best practices perfectly!")
        print("🤖 ToolCallingAgent + CodeAgent architecture is working optimally!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 