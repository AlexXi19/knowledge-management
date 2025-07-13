#!/usr/bin/env python3
"""
Demo script showing how to use the Knowledge Agent with custom directories
"""
import asyncio
import os
from pathlib import Path
from agent.knowledge_agent import KnowledgeAgent


async def demo_directory_structure():
    """Demonstrate the directory structure functionality"""
    
    print("🚀 Knowledge Agent Directory Structure Demo")
    print("=" * 50)
    
    # Demo 1: Create agent with custom directory
    print("\n1. Creating Knowledge Agent with custom directory...")
    
    # Create a demo directory
    demo_dir = Path("./demo_knowledge_system")
    
    # Initialize agent with custom directory
    agent = KnowledgeAgent(dir=str(demo_dir))
    
    print(f"✅ Agent created with directory: {demo_dir}")
    print(f"📝 Notes will be stored in: {demo_dir}")
    print(f"🧠 Knowledge base will be stored in: {demo_dir / '.knowledge_base'}")
    
    # Demo 2: Initialize the agent
    print("\n2. Initializing the agent...")
    await agent.initialize()
    
    # Demo 3: Show the directory structure
    print("\n3. Directory structure created:")
    
    def show_tree(path, prefix="", is_last=True):
        """Show directory tree"""
        if not path.exists():
            return
            
        items = sorted(path.iterdir())
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            current_prefix = "└── " if is_last_item else "├── "
            print(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir() and not item.name.startswith('.'):
                extension = "    " if is_last_item else "│   "
                show_tree(item, prefix + extension, is_last_item)
    
    show_tree(demo_dir)
    
    # Demo 4: Show what's in the .knowledge_base directory
    print(f"\n4. Knowledge base directory contents:")
    kb_dir = demo_dir / '.knowledge_base'
    if kb_dir.exists():
        for item in kb_dir.iterdir():
            print(f"   📄 {item.name}")
    else:
        print("   📄 (Knowledge base files will be created as needed)")
    
    # Demo 5: Test basic functionality (without API key)
    print("\n5. Testing basic functionality...")
    test_message = "Create a note about directory structure"
    
    try:
        response = await agent.process_message(test_message)
        print(f"✅ Agent processed message successfully")
        print(f"📝 Response type: {type(response)}")
    except Exception as e:
        print(f"⚠️  Expected error (no API key): {str(e)[:50]}...")
    
    # Demo 6: Show agent properties
    print("\n6. Agent properties:")
    print(f"   🗂️  Base directory: {agent.base_dir}")
    print(f"   📝 Notes directory: {agent.notes_dir}")
    print(f"   🧠 Knowledge base directory: {agent.knowledge_base_dir}")
    print(f"   🤖 Agent initialized: {agent.initialized}")
    
    # Demo 7: Multiple agents with different directories
    print("\n7. Creating multiple agents with different directories...")
    
    # Create second agent with different directory
    demo_dir2 = Path("./demo_knowledge_system2")
    agent2 = KnowledgeAgent(dir=str(demo_dir2))
    await agent2.initialize()
    
    print(f"✅ Agent 1 - Directory: {agent.base_dir}")
    print(f"✅ Agent 2 - Directory: {agent2.base_dir}")
    print("   🔄 Each agent has its own isolated knowledge system")
    
    # Demo 8: Default directory behavior
    print("\n8. Default directory behavior...")
    agent_default = KnowledgeAgent()  # No directory specified
    print(f"✅ Default agent uses current directory: {agent_default.base_dir}")
    
    print("\n🎉 Demo completed!")
    print("\nKey Features:")
    print("• 📁 Custom directory support - specify where notes should be stored")
    print("• 🏗️  Automatic directory creation - creates if doesn't exist")
    print("• 🔄 Existing note processing - processes existing notes in the directory")
    print("• 🧠 Isolated knowledge base - each directory has its own .knowledge_base")
    print("• 🔗 Hierarchical structure - notes in main dir, metadata in .knowledge_base")
    print("• 🎯 Multiple agents - each can have its own directory")
    
    print("\nUsage Examples:")
    print("• agent = KnowledgeAgent(dir='/path/to/my/notes')")
    print("• agent = KnowledgeAgent(dir='./project_notes')")
    print("• agent = KnowledgeAgent()  # Uses current directory")
    
    # Cleanup demo directories
    print("\n🧹 Cleanup:")
    print("Demo directories created:")
    print(f"• {demo_dir}")
    print(f"• {demo_dir2}")
    print("You can delete these directories when you're done exploring!")


if __name__ == "__main__":
    asyncio.run(demo_directory_structure()) 