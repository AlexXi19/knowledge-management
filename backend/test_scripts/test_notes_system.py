#!/usr/bin/env python3
"""
Test script for the notes management system
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path

from knowledge.notes_manager import NotesManager
from agent.knowledge_agent import KnowledgeAgent

async def test_notes_system():
    """Test the notes system functionality"""
    
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    print(f"🧪 Testing notes system in: {temp_dir}")
    
    try:
        # Initialize notes manager with test directory
        notes_manager = NotesManager(temp_dir)
        await notes_manager.initialize()
        
        print(f"✅ Notes manager initialized")
        print(f"📁 Created {len(notes_manager.categories)} category folders")
        
        # Test 1: Create a new note
        print("\n🧪 Test 1: Creating a new note")
        note1 = await notes_manager.create_note(
            title="Test Idea",
            content="This is a test idea that needs development. It's about building a better knowledge management system.",
            category="Ideas to Develop",
            tags=["test", "knowledge-management", "development"]
        )
        print(f"✅ Created note: {note1.title}")
        
        # Test 2: Create another note
        print("\n🧪 Test 2: Creating another note")
        note2 = await notes_manager.create_note(
            title="Reading Note",
            content="https://example.com/interesting-article - This article discusses the future of AI.",
            category="Reading List",
            tags=["ai", "future", "article"]
        )
        print(f"✅ Created note: {note2.title}")
        
        # Test 3: Update existing note
        print("\n🧪 Test 3: Updating existing note")
        updated_note = await notes_manager.update_note(
            note1.path,
            "Additional thoughts: This system should integrate with existing note-taking tools."
        )
        print(f"✅ Updated note: {updated_note.title}")
        
        # Test 4: Search for related notes
        print("\n🧪 Test 4: Finding related notes")
        related_notes = await notes_manager.find_related_notes(
            "knowledge management system development",
            limit=3
        )
        print(f"✅ Found {len(related_notes)} related notes")
        for note in related_notes:
            print(f"   - {note.title}")
        
        # Test 5: Test the decision system
        print("\n🧪 Test 5: Testing decision system")
        action, existing_note = await notes_manager.decide_note_action(
            "More thoughts on knowledge management",
            "Ideas to Develop"
        )
        print(f"✅ Decision: {action}")
        if existing_note:
            print(f"   Would update: {existing_note.title}")
        
        # Test 6: Get notes structure
        print("\n🧪 Test 6: Getting notes structure")
        structure = notes_manager.get_notes_structure()
        print(f"✅ Notes structure:")
        for category, info in structure.items():
            print(f"   {category}: {info['count']} notes")
        
        # Test 7: Test with Knowledge Agent
        print("\n🧪 Test 7: Testing with Knowledge Agent")
        # Set environment variable for test
        os.environ["NOTES_DIRECTORY"] = temp_dir
        
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Process a message
        response = await agent.process_message("I have an idea for a new app that helps people organize their thoughts")
        print(f"✅ Agent response: {response.response}")
        
        # Check if note was created
        all_notes = await agent.get_all_notes()
        print(f"✅ Total notes after agent processing: {len(all_notes)}")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        raise
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print(f"🧹 Cleaned up test directory")

async def test_existing_notes_integration():
    """Test integration with existing notes"""
    
    # Create a temporary directory with some existing notes
    temp_dir = tempfile.mkdtemp()
    print(f"🧪 Testing existing notes integration in: {temp_dir}")
    
    try:
        # Create some existing notes manually
        ideas_dir = Path(temp_dir) / "ideas"
        ideas_dir.mkdir(parents=True)
        
        # Create a sample existing note
        sample_note = ideas_dir / "existing-idea.md"
        sample_note.write_text("""---
title: Existing Idea
category: Ideas to Develop
tags: [existing, test]
created: 2024-01-01T12:00:00
---

# Existing Idea

This is an existing idea that was already in the notes directory.

It has some content and should be processed correctly.
""")
        
        # Another note in personal
        personal_dir = Path(temp_dir) / "personal"
        personal_dir.mkdir(parents=True)
        
        personal_note = personal_dir / "my-thoughts.md"
        personal_note.write_text("""# My Personal Thoughts

These are my personal reflections on life and work.

## Work-Life Balance

Finding balance is important for productivity and happiness.
""")
        
        print("📄 Created sample existing notes")
        
        # Initialize notes manager
        notes_manager = NotesManager(temp_dir)
        await notes_manager.initialize()
        
        print(f"✅ Notes manager initialized with {len(notes_manager.notes_index)} existing notes")
        
        # Test that existing notes were parsed correctly
        for path, note in notes_manager.notes_index.items():
            print(f"   📝 {note.title} ({note.category})")
        
        # Test knowledge agent integration
        os.environ["NOTES_DIRECTORY"] = temp_dir
        agent = KnowledgeAgent()
        await agent.initialize()
        
        # Check that existing notes were processed
        structure = await agent.get_notes_structure()
        print(f"✅ Agent processed existing notes:")
        for category, info in structure.items():
            if info['count'] > 0:
                print(f"   {category}: {info['count']} notes")
        
        print("\n🎉 Existing notes integration test passed!")
        
    except Exception as e:
        print(f"❌ Error during existing notes test: {e}")
        raise
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print(f"🧹 Cleaned up test directory")

if __name__ == "__main__":
    print("🧪 Notes Management System Test Suite")
    print("=" * 50)
    
    asyncio.run(test_notes_system())
    print("\n" + "=" * 50)
    asyncio.run(test_existing_notes_integration()) 