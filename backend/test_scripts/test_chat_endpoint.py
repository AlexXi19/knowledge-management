#!/usr/bin/env python3
"""
Test script to reproduce the 500 error on the chat endpoint
"""

import asyncio
import sys
from pathlib import Path
import traceback

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from agent.knowledge_agent import KnowledgeAgent
from models.chat_models import ChatRequest, ChatMessage

async def test_chat_endpoint_directly():
    """Test the agent directly without FastAPI to see the error"""
    print("🧪 Testing chat functionality directly...")
    
    try:
        # Initialize the agent
        agent = KnowledgeAgent()
        await agent.initialize()
        
        print("✅ Agent initialized successfully")
        
        # Create a test request
        test_message = "Hello, can you help me create a note about Python?"
        
        print(f"📤 Sending message: {test_message}")
        
        # Process the message
        response = await agent.process_message(test_message)
        
        print("✅ Message processed successfully")
        print(f"📥 Response: {response.response}")
        print(f"📁 Categories: {response.categories}")
        print(f"🔄 Knowledge updates: {len(response.knowledge_updates)}")
        print(f"💡 Suggested actions: {response.suggested_actions}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return False

async def test_chat_request_model():
    """Test the ChatRequest model parsing"""
    print("\n🧪 Testing ChatRequest model...")
    
    try:
        # Create a test request with OpenAI-style format
        request_data = {
            "message": "Hello world",
            "conversation_history": [
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"}
            ]
        }
        
        request = ChatRequest(**request_data)
        print("✅ ChatRequest model works correctly")
        print(f"📤 Message: {request.message}")
        print(f"📝 History length: {len(request.conversation_history)}")
        
        # Test with standard format too
        request_data2 = {
            "message": "Test message",
            "conversation_history": [
                {"sender": "user", "content": "Test user message", "timestamp": "2023-01-01T00:00:00"},
                {"sender": "agent", "content": "Test agent response", "timestamp": "2023-01-01T00:01:00"}
            ]
        }
        
        request2 = ChatRequest(**request_data2)
        print("✅ ChatRequest model works with standard format too")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in ChatRequest model: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing chat endpoint functionality...")
    print("=" * 60)
    
    # Test ChatRequest model
    model_test = await test_chat_request_model()
    
    # Test agent directly
    agent_test = await test_chat_endpoint_directly()
    
    print("\n" + "=" * 60)
    if model_test and agent_test:
        print("🎉 All tests passed! The issue might be elsewhere.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return model_test and agent_test

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 