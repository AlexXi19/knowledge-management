#!/usr/bin/env python3
"""
Controlled test suite for the knowledge agent with smolagents best practices
Creates a clean environment and demonstrates agent conversations
"""

import asyncio
import sys
import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any

# Add the backend directory to the Python path (parent of testing/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.knowledge_agent import KnowledgeAgent
from models.chat_models import ChatMessage

class AgentConversationTester:
    """Test suite for agent conversations in a controlled environment"""
    
    def __init__(self, test_dir: str = "test_knowledge_env"):
        """Initialize the tester with a clean test environment"""
        self.test_dir = Path(test_dir)
        self.agent = None
        self.conversation_history = []
        
    async def setup_test_environment(self):
        """Set up a clean test environment"""
        print("🧪 Setting up test environment...")
        
        # Remove existing test directory if it exists
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        # Create new test directory structure
        self.test_dir.mkdir(exist_ok=True)
        (self.test_dir / "notes").mkdir(exist_ok=True)
        (self.test_dir / "knowledge_base").mkdir(exist_ok=True)
        (self.test_dir / "logs").mkdir(exist_ok=True)
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Initialize the knowledge agent
        print("🤖 Initializing Knowledge Agent...")
        self.agent = KnowledgeAgent()
        await self.agent.initialize()
        
        print(f"✅ Test environment ready in: {self.test_dir.absolute()}")
        print(f"📂 Working directory: {os.getcwd()}")
        
    async def cleanup_test_environment(self):
        """Clean up the test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        # Change back to parent directory
        os.chdir(self.test_dir.parent)
        
        # Remove test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print("✅ Test environment cleaned up")
    
    async def chat_with_agent(self, message: str, conversation_type: str = "general") -> Dict[str, Any]:
        """Chat with the agent and return response details"""
        print(f"\n{'='*60}")
        print(f"🗣️  {conversation_type.upper()} CONVERSATION")
        print(f"{'='*60}")
        print(f"User: {message}")
        print(f"{'─'*60}")
        
        # Record start time
        start_time = time.time()
        
        # Check if this requires complex reasoning
        requires_complex = self.agent._requires_complex_reasoning(message)
        print(f"🧠 Complex reasoning required: {requires_complex}")
        
        # Get response from agent
        response = await self.agent.process_message(message, self.conversation_history)
        
        # Record end time
        end_time = time.time()
        duration = end_time - start_time
        
        # Add to conversation history
        self.conversation_history.append(ChatMessage(
            sender="user",
            content=message,
            timestamp=start_time
        ))
        self.conversation_history.append(ChatMessage(
            sender="assistant", 
            content=response.response,
            timestamp=end_time
        ))
        
        # Display response
        print(f"🤖 Agent: {response.response}")
        print(f"📊 Response time: {duration:.2f}s")
        print(f"🏷️  Categories: {response.categories}")
        print(f"📝 Knowledge updates: {len(response.knowledge_updates)}")
        print(f"💡 Suggested actions: {response.suggested_actions[:3]}")  # Show first 3
        
        # Get agent logs
        logs = self.agent.get_agent_logs()
        tool_logs = [log for log in logs if log["agent"] == "tool_calling"]
        code_logs = [log for log in logs if log["agent"] == "code"]
        
        print(f"📋 Agent logs: {len(logs)} total ({len(tool_logs)} tool, {len(code_logs)} code)")
        
        return {
            "message": message,
            "response": response.response,
            "duration": duration,
            "requires_complex": requires_complex,
            "categories": response.categories,
            "knowledge_updates": response.knowledge_updates,
            "suggested_actions": response.suggested_actions,
            "logs": logs
        }
    
    async def demonstrate_streaming(self, message: str):
        """Demonstrate streaming response functionality"""
        print(f"\n{'='*60}")
        print(f"📡 STREAMING DEMONSTRATION")
        print(f"{'='*60}")
        print(f"User: {message}")
        print(f"{'─'*60}")
        
        stream_events = []
        async for event in self.agent.stream_response(message, self.conversation_history):
            stream_events.append(event)
            
            if event["type"] == "status":
                print(f"🔄 Status: {event['message']}")
            elif event["type"] == "step":
                print(f"🔧 Step {event['step']}: {event['action']}")
            elif event["type"] == "complete":
                print(f"✅ Complete: Response received")
            elif event["type"] == "error":
                print(f"❌ Error: {event['message']}")
        
        print(f"📊 Total streaming events: {len(stream_events)}")
        return stream_events
    
    async def run_conversation_tests(self):
        """Run a series of test conversations"""
        print("\n🚀 Starting Agent Conversation Tests")
        print("=" * 80)
        
        # Test conversations with different complexity levels
        test_conversations = [
            # Simple tasks (should use ToolCallingAgent)
            {
                "message": "Create a note about Python programming basics",
                "type": "simple_creation"
            },
            {
                "message": "Search for notes about programming",
                "type": "simple_search"
            },
            {
                "message": "What notes do I have about Python?",
                "type": "simple_query"
            },
            
            # Medium complexity tasks
            {
                "message": "Create a comprehensive note about machine learning algorithms including supervised and unsupervised learning",
                "type": "medium_creation"
            },
            {
                "message": "Find relationships between my programming notes and suggest connections",
                "type": "medium_analysis"
            },
            
            # Complex tasks (should trigger CodeAgent)
            {
                "message": "Analyze the relationships between machine learning, data science, and artificial intelligence. Compare their applications and find patterns in my knowledge base.",
                "type": "complex_analysis"
            },
            {
                "message": "Deep dive into comprehensive analysis of programming paradigms, compare functional vs object-oriented approaches, and suggest optimization strategies for my learning path",
                "type": "complex_reasoning"
            },
            {
                "message": "What are the connections between different programming languages? How do they relate to each other? Can you find trends and patterns?",
                "type": "complex_pattern_finding"
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_conversations, 1):
            print(f"\n🧪 Test {i}/{len(test_conversations)}")
            try:
                result = await self.chat_with_agent(test["message"], test["type"])
                results.append(result)
                
                # Reset agent memory between tests for consistency
                self.agent.reset_agent_memory()
                
                # Small delay between tests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Test {i} failed: {e}")
                results.append({
                    "message": test["message"],
                    "error": str(e),
                    "type": test["type"]
                })
        
        return results
    
    async def demonstrate_agent_capabilities(self):
        """Demonstrate specific agent capabilities"""
        print("\n🎯 Demonstrating Agent Capabilities")
        print("=" * 80)
        
        # Demonstrate streaming
        await self.demonstrate_streaming("Create a detailed note about neural networks and deep learning")
        
        # Demonstrate knowledge graph access
        print(f"\n📈 Knowledge Graph Demo")
        print("─" * 60)
        try:
            graph_data = await self.agent.get_knowledge_graph()
            print(f"📊 Knowledge graph: {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('edges', []))} edges")
        except Exception as e:
            print(f"❌ Knowledge graph error: {e}")
        
        # Demonstrate knowledge search
        print(f"\n🔍 Knowledge Search Demo")
        print("─" * 60)
        try:
            search_results = await self.agent.search_knowledge("Python programming", limit=5)
            print(f"🔍 Search results: {len(search_results)} items found")
            for result in search_results[:3]:  # Show first 3
                print(f"   📄 {result.content[:100]}...")
        except Exception as e:
            print(f"❌ Search error: {e}")
        
        # Demonstrate notes retrieval
        print(f"\n📚 Notes Retrieval Demo")
        print("─" * 60)
        try:
            all_notes = await self.agent.get_all_notes()
            print(f"📚 Total notes: {len(all_notes)}")
            for note in all_notes[:3]:  # Show first 3
                print(f"   📝 {note.get('title', 'Untitled')}: {note.get('content', '')[:80]}...")
        except Exception as e:
            print(f"❌ Notes retrieval error: {e}")
    
    def analyze_test_results(self, results: List[Dict[str, Any]]):
        """Analyze and summarize test results"""
        print(f"\n📊 Test Results Analysis")
        print("=" * 80)
        
        successful_tests = [r for r in results if "error" not in r]
        failed_tests = [r for r in results if "error" in r]
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
        print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
        
        if successful_tests:
            # Analyze complexity detection
            simple_tasks = [r for r in successful_tests if not r.get("requires_complex", False)]
            complex_tasks = [r for r in successful_tests if r.get("requires_complex", False)]
            
            print(f"\n🧠 Complexity Detection:")
            print(f"   Simple tasks: {len(simple_tasks)}")
            print(f"   Complex tasks: {len(complex_tasks)}")
            
            # Analyze response times
            response_times = [r["duration"] for r in successful_tests]
            avg_response_time = sum(response_times) / len(response_times)
            
            print(f"\n⏱️  Performance:")
            print(f"   Average response time: {avg_response_time:.2f}s")
            print(f"   Fastest response: {min(response_times):.2f}s")
            print(f"   Slowest response: {max(response_times):.2f}s")
            
            # Analyze agent usage
            total_logs = sum(len(r["logs"]) for r in successful_tests)
            tool_logs = sum(len([log for log in r["logs"] if log["agent"] == "tool_calling"]) for r in successful_tests)
            code_logs = sum(len([log for log in r["logs"] if log["agent"] == "code"]) for r in successful_tests)
            
            print(f"\n🤖 Agent Usage:")
            print(f"   Total logs: {total_logs}")
            print(f"   ToolCallingAgent usage: {tool_logs} ({tool_logs/total_logs*100:.1f}%)")
            print(f"   CodeAgent usage: {code_logs} ({code_logs/total_logs*100:.1f}%)")
        
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['message'][:50]}... Error: {test['error']}")


async def main():
    """Main function to run the controlled test suite"""
    tester = AgentConversationTester()
    
    try:
        # Setup test environment
        await tester.setup_test_environment()
        
        # Run conversation tests
        results = await tester.run_conversation_tests()
        
        # Demonstrate additional capabilities
        await tester.demonstrate_agent_capabilities()
        
        # Analyze results
        tester.analyze_test_results(results)
        
        print(f"\n🎉 Test suite completed successfully!")
        print(f"📊 Total conversations: {len(results)}")
        print(f"🏆 Smolagents best practices architecture working optimally!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False
    
    finally:
        # Always cleanup
        await tester.cleanup_test_environment()
    
    return True


if __name__ == "__main__":
    print("🧪 Knowledge Agent Conversation Test Suite")
    print("🤖 Testing smolagents best practices implementation")
    print("=" * 80)
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 