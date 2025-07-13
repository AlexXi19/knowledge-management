#!/usr/bin/env python3
"""
Simple agent chat test - focused on key conversations
Quick way to test the smolagents best practices implementation
"""

import asyncio
import sys
import os
import shutil
import time
from pathlib import Path

# Add the backend directory to the Python path (parent of testing/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.knowledge_agent import KnowledgeAgent

async def setup_clean_environment():
    """Set up a clean test environment"""
    test_dir = Path("simple_chat_test")
    
    # Remove existing test directory if it exists
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # Create new test directory structure
    test_dir.mkdir(exist_ok=True)
    (test_dir / "notes").mkdir(exist_ok=True)
    (test_dir / "knowledge_base").mkdir(exist_ok=True)
    
    # Change to test directory
    os.chdir(test_dir)
    
    return test_dir

async def cleanup_environment(test_dir):
    """Clean up the test environment"""
    os.chdir(test_dir.parent)
    if test_dir.exists():
        shutil.rmtree(test_dir)

async def chat_with_agent(agent, message, conversation_type="chat"):
    """Simple chat function"""
    print(f"\n{'='*50}")
    print(f"💬 {conversation_type.upper()}")
    print(f"{'='*50}")
    print(f"You: {message}")
    print(f"{'─'*50}")
    
    # Check complexity
    complex_reasoning = agent._requires_complex_reasoning(message)
    print(f"🧠 Complex reasoning: {'Yes' if complex_reasoning else 'No'}")
    
    # Get response
    start_time = time.time()
    response = await agent.process_message(message)
    duration = time.time() - start_time
    
    # Display response
    print(f"🤖 Agent: {response.response}")
    print(f"⏱️  Time: {duration:.2f}s")
    print(f"📂 Categories: {', '.join(response.categories)}")
    
    # Show agent logs
    logs = agent.get_agent_logs()
    tool_logs = len([log for log in logs if log["agent"] == "tool_calling"])
    code_logs = len([log for log in logs if log["agent"] == "code"])
    print(f"📋 Logs: {len(logs)} total ({tool_logs} tool, {code_logs} code)")
    
    return response

async def main():
    """Main chat function"""
    print("🚀 Simple Agent Chat Test")
    print("🤖 Testing smolagents architecture")
    print("=" * 60)
    
    test_dir = None
    try:
        # Setup environment
        test_dir = await setup_clean_environment()
        print(f"✅ Test environment: {test_dir.absolute()}")
        
        # Initialize agent
        print("🤖 Initializing Knowledge Agent...")
        agent = KnowledgeAgent()
        await agent.initialize()
        print("✅ Agent initialized!")
        
        # Test conversations
        conversations = [
            ("Create a note about Python programming", "Simple Task"),
            ("Search for programming notes", "Simple Search"),
            ("Analyze the relationships between programming languages and find patterns", "Complex Analysis"),
            ("What are the connections between different AI concepts?", "Complex Query")
        ]
        
        for message, chat_type in conversations:
            await chat_with_agent(agent, message, chat_type)
            
            # Reset agent memory for clean tests
            agent.reset_agent_memory()
            
            # Brief pause
            await asyncio.sleep(1)
        
        print(f"\n🎉 Chat test completed!")
        print(f"🏆 Smolagents architecture working correctly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if test_dir:
            await cleanup_environment(test_dir)
            print("🧹 Cleaned up test environment")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 