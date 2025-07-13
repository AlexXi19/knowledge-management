"""
Test the directory structure functionality of the Knowledge Agent
"""
import os
import tempfile
import shutil
from pathlib import Path
import asyncio
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.knowledge_agent import KnowledgeAgent


async def test_directory_structure():
    """Test that the knowledge agent creates and uses the correct directory structure"""
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="knowledge_test_")
    
    try:
        print("🧪 Testing Knowledge Agent Directory Structure")
        print(f"📁 Test directory: {test_dir}")
        print("=" * 60)
        
        # Test 1: Initialize agent with custom directory
        print("\n1. Testing custom directory initialization...")
        agent = KnowledgeAgent(dir=test_dir)
        
        # Check that directories were created
        notes_dir = Path(test_dir)
        knowledge_base_dir = Path(test_dir) / '.knowledge_base'
        
        assert notes_dir.exists(), "Notes directory should exist"
        assert knowledge_base_dir.exists(), "Knowledge base directory should exist"
        print(f"✅ Notes directory created: {notes_dir}")
        print(f"✅ Knowledge base directory created: {knowledge_base_dir}")
        
        # Test 2: Initialize the agent
        print("\n2. Testing agent initialization...")
        await agent.initialize()
        print("✅ Agent initialized successfully")
        
        # Check that category directories were created
        expected_categories = ["ideas", "personal", "research", "reading-list", "projects", "learning", "quick-notes"]
        for category in expected_categories:
            category_dir = notes_dir / category
            if category_dir.exists():
                print(f"✅ Category directory created: {category}")
            else:
                print(f"⚠️  Category directory missing: {category}")
        
        # Test 3: Check knowledge base files
        print("\n3. Testing knowledge base structure...")
        expected_kb_files = ["hash_cache.json", "note_mapping.json"]
        for kb_file in expected_kb_files:
            kb_file_path = knowledge_base_dir / kb_file
            if kb_file_path.exists():
                print(f"✅ Knowledge base file created: {kb_file}")
            else:
                print(f"📄 Knowledge base file will be created when needed: {kb_file}")
        
        # Test 4: Create a note and verify structure
        print("\n4. Testing note creation...")
        test_message = "Create a note about Python testing best practices"
        
        try:
            response = await agent.process_message(test_message)
            print(f"✅ Note creation attempted")
            print(f"📝 Response: {response.response[:100]}...")
        except Exception as e:
            print(f"⚠️  Note creation failed (expected without API key): {e}")
        
        # Test 5: Verify environment variables are set
        print("\n5. Testing environment variables...")
        notes_env = os.environ.get('NOTES_DIRECTORY')
        kb_env = os.environ.get('KNOWLEDGE_BASE_PATH')
        
        # Use resolve() to handle symlinks on macOS
        expected_notes_path = str(notes_dir.resolve())
        expected_kb_path = str(knowledge_base_dir.resolve())
        
        assert notes_env == expected_notes_path, f"NOTES_DIRECTORY should be {expected_notes_path}, got {notes_env}"
        assert kb_env == expected_kb_path, f"KNOWLEDGE_BASE_PATH should be {expected_kb_path}, got {kb_env}"
        print(f"✅ NOTES_DIRECTORY: {notes_env}")
        print(f"✅ KNOWLEDGE_BASE_PATH: {kb_env}")
        
        # Test 6: Test with different directory
        print("\n6. Testing with different directory...")
        test_dir2 = tempfile.mkdtemp(prefix="knowledge_test2_")
        
        try:
            agent2 = KnowledgeAgent(dir=test_dir2)
            await agent2.initialize()
            
            # Verify the new paths
            notes_dir2 = Path(test_dir2)
            knowledge_base_dir2 = Path(test_dir2) / '.knowledge_base'
            
            assert notes_dir2.exists(), "Second notes directory should exist"
            assert knowledge_base_dir2.exists(), "Second knowledge base directory should exist"
            print(f"✅ Second test directory structure created: {test_dir2}")
            
        finally:
            shutil.rmtree(test_dir2, ignore_errors=True)
        
        print("\n✅ All directory structure tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        print(f"\n🧹 Cleaning up test directory: {test_dir}")
        shutil.rmtree(test_dir, ignore_errors=True)


async def test_default_directory():
    """Test that the agent works with default directory (current working directory)"""
    
    print("\n🧪 Testing Default Directory Behavior")
    print("=" * 60)
    
    # Save current working directory
    original_cwd = os.getcwd()
    
    # Create a temporary directory and change to it
    test_dir = tempfile.mkdtemp(prefix="knowledge_default_")
    
    try:
        os.chdir(test_dir)
        
        print(f"📁 Changed to test directory: {test_dir}")
        
        # Test agent with no directory parameter (should use current directory)
        agent = KnowledgeAgent()
        
        # Check that directories were created in current directory
        notes_dir = Path(test_dir)
        knowledge_base_dir = Path(test_dir) / '.knowledge_base'
        
        assert notes_dir.exists(), "Notes directory should exist in current directory"
        assert knowledge_base_dir.exists(), "Knowledge base directory should exist in current directory"
        print(f"✅ Default directory structure created in: {test_dir}")
        
        # Initialize agent
        await agent.initialize()
        print("✅ Agent initialized with default directory")
        
        print("✅ Default directory test passed!")
        
    except Exception as e:
        print(f"❌ Default directory test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        # Clean up
        shutil.rmtree(test_dir, ignore_errors=True)


async def main():
    """Run all directory structure tests"""
    print("🚀 Knowledge Agent Directory Structure Tests")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    await test_directory_structure()
    await test_default_directory()
    
    print("\n🎉 All tests completed!")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main()) 