#!/usr/bin/env python3
"""
Test script for smolagents integration with the Knowledge Management System
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from agent.knowledge_agent import KnowledgeAgent
from models.chat_models import ChatMessage

async def test_agent_initialization():
    """Test that the agent initializes correctly"""
    print("🧪 Testing agent initialization...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        if agent.initialized:
            print("✅ Agent initialized successfully")
            print(f"✅ Model: {agent.model_name}")
            print(f"✅ Tools count: {len(agent.agent.tools) if agent.agent else 0}")
            return True
        else:
            print("❌ Agent initialization failed")
            return False
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return False

async def test_simple_message_processing():
    """Test processing a simple message"""
    print("\n🧪 Testing simple message processing...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        test_message = "This is a test note about machine learning algorithms"
        
        response = await agent.process_message(test_message)
        
        print(f"✅ Message processed successfully")
        print(f"✅ Response: {response.response[:100]}...")
        print(f"✅ Categories: {response.categories}")
        print(f"✅ Knowledge updates: {len(response.knowledge_updates)}")
        print(f"✅ Suggested actions: {len(response.suggested_actions)}")
        
        return True
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        return False

async def test_agent_tools():
    """Test that the agent can use its tools"""
    print("\n🧪 Testing agent tools...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Test creating a knowledge note
        test_message = "Create a note about Python programming best practices"
        
        response = await agent.process_message(test_message)
        
        print(f"✅ Tools test completed")
        print(f"✅ Response contains: {response.response[:200]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error testing tools: {e}")
        return False

async def test_streaming_response():
    """Test streaming response functionality"""
    print("\n🧪 Testing streaming response...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        test_message = "Tell me about artificial intelligence"
        
        chunks = []
        async for chunk in agent.stream_response(test_message):
            chunks.append(chunk)
            print(f"📡 Chunk: {chunk.get('type', 'unknown')}")
        
        print(f"✅ Streaming test completed with {len(chunks)} chunks")
        
        return True
    except Exception as e:
        print(f"❌ Error testing streaming: {e}")
        return False

async def test_knowledge_search():
    """Test knowledge search functionality"""
    print("\n🧪 Testing knowledge search...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # First create some content
        await agent.process_message("This is a note about machine learning")
        await agent.process_message("This is a note about data science")
        
        # Now search for it
        results = await agent.search_knowledge("machine learning")
        
        print(f"✅ Search completed with {len(results)} results")
        
        return True
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False

async def test_get_all_notes():
    """Test getting all notes"""
    print("\n🧪 Testing get all notes...")
    
    try:
        agent = KnowledgeAgent()
        await agent.initialize()
        
        notes = await agent.get_all_notes()
        
        print(f"✅ Retrieved {len(notes)} notes")
        
        return True
    except Exception as e:
        print(f"❌ Error getting notes: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting smolagents integration tests...")
    print("=" * 60)
    
    tests = [
        test_agent_initialization,
        test_simple_message_processing,
        test_agent_tools,
        test_streaming_response,
        test_knowledge_search,
        test_get_all_notes
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🧪 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! smolagents integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 