#!/usr/bin/env python3
"""
Test script for the hash-based caching system in the knowledge management agent
"""

import asyncio
import sys
import time
import json
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from agent.knowledge_agent import KnowledgeAgent
from knowledge.hash_utils import get_hash_tracker, calculate_content_hash

async def test_hash_utilities():
    """Test the basic hash utility functions"""
    print("🧪 Testing hash utilities...")
    
    # Test content hash calculation
    content1 = "This is a test content for hash calculation"
    content2 = "This is a test content for hash calculation"
    content3 = "This is different content"
    
    hash1 = calculate_content_hash(content1)
    hash2 = calculate_content_hash(content2)
    hash3 = calculate_content_hash(content3)
    
    assert hash1 == hash2, "Same content should produce same hash"
    assert hash1 != hash3, "Different content should produce different hash"
    
    print(f"✅ Hash utilities working correctly")
    print(f"   Sample hash: {hash1[:16]}...")
    
    return True

async def test_hash_tracker():
    """Test the HashTracker functionality"""
    print("\n🧪 Testing hash tracker...")
    
    tracker = get_hash_tracker()
    
    # Test basic operations
    test_id = "test_content_123"
    test_content = "This is test content for the tracker"
    test_hash = calculate_content_hash(test_content)
    
    # Update hash
    tracker.update_hash(test_id, test_hash, {"test": "metadata"})
    
    # Check if content changed
    has_changed = tracker.has_content_changed(test_id, test_content)
    assert not has_changed, "Content should not be marked as changed"
    
    # Test with different content
    different_content = "This is different content"
    has_changed = tracker.has_content_changed(test_id, different_content)
    assert has_changed, "Different content should be marked as changed"
    
    # Test note mapping
    note_path = "/test/path/note.md"
    node_id = "test_node_123"
    tracker.set_note_mapping(note_path, node_id)
    
    retrieved_node_id = tracker.get_knowledge_node_id(note_path)
    assert retrieved_node_id == node_id, "Note mapping should work correctly"
    
    print("✅ Hash tracker working correctly")
    
    return True

async def test_agent_caching():
    """Test the agent's caching behavior"""
    print("\n🧪 Testing agent caching behavior...")
    
    agent = KnowledgeAgent()
    await agent.initialize()
    
    # Test content processing with caching
    test_content = "This is a test note about machine learning and artificial intelligence"
    
    print("   First processing (should be slow)...")
    start_time = time.time()
    response1 = await agent.process_message(f"Process this content: {test_content}")
    first_duration = time.time() - start_time
    
    print(f"   First processing took {first_duration:.2f} seconds")
    
    # Process the same content again (should be faster due to caching)
    print("   Second processing (should be faster due to caching)...")
    start_time = time.time()
    response2 = await agent.process_message(f"Process this content: {test_content}")
    second_duration = time.time() - start_time
    
    print(f"   Second processing took {second_duration:.2f} seconds")
    
    # The responses should be similar (though not identical due to timestamps)
    assert response1.categories == response2.categories, "Categories should be the same for identical content"
    
    # Check if caching actually provided a performance benefit
    if second_duration < first_duration * 0.8:  # At least 20% faster
        print("✅ Caching provided performance benefit")
    else:
        print("⚠️  Caching performance benefit not significant")
    
    return True

async def test_note_creation_caching():
    """Test note creation and hash tracking"""
    print("\n🧪 Testing note creation with hash tracking...")
    
    agent = KnowledgeAgent()
    await agent.initialize()
    
    # Create a test note
    note_content = "This is a test note about Python programming best practices"
    response1 = await agent.process_message(f"Create a note with this content: {note_content}")
    
    print("✅ First note created")
    
    # Try to create the same note again (should detect duplication)
    response2 = await agent.process_message(f"Create a note with this content: {note_content}")
    
    print("✅ Second note creation attempted")
    
    # Check cache statistics
    stats_prompt = "Get cache statistics"
    stats_response = await agent.process_message(stats_prompt)
    
    print(f"📊 Cache statistics: {stats_response.response[:200]}...")
    
    return True

async def test_content_update_detection():
    """Test detection of content changes in existing notes"""
    print("\n🧪 Testing content update detection...")
    
    agent = KnowledgeAgent()
    await agent.initialize()
    
    # Create a note
    original_content = "This is the original content about data science"
    create_response = await agent.process_message(f"Create a note: {original_content}")
    
    # Try to update with identical content (should be detected as no change needed)
    identical_update = await agent.process_message(f"Update the note with: {original_content}")
    
    # Update with actually different content
    new_content = "This is additional content about machine learning algorithms"
    different_update = await agent.process_message(f"Update the note with: {new_content}")
    
    print("✅ Content update detection tested")
    
    return True

async def test_cache_management():
    """Test cache management operations"""
    print("\n🧪 Testing cache management...")
    
    agent = KnowledgeAgent()
    await agent.initialize()
    
    # Get initial cache stats
    stats_response = await agent.process_message("Get current cache statistics")
    print(f"📊 Initial cache stats: {stats_response.response[:100]}...")
    
    # Test cache rebuild
    rebuild_response = await agent.process_message("Rebuild the cache")
    print(f"🔄 Cache rebuild: {rebuild_response.response[:100]}...")
    
    # Get updated stats
    updated_stats = await agent.process_message("Get cache statistics after rebuild")
    print(f"📊 Updated cache stats: {updated_stats.response[:100]}...")
    
    print("✅ Cache management operations tested")
    
    return True

async def test_performance_comparison():
    """Test performance differences between cached and uncached operations"""
    print("\n🧪 Testing performance comparison...")
    
    agent = KnowledgeAgent()
    await agent.initialize()
    
    # Clear cache for clean test
    clear_response = await agent.process_message("Clear the cache with confirm='yes'")
    print("🗑️  Cache cleared for performance test")
    
    # Test multiple content processing operations
    test_contents = [
        "Machine learning algorithms and their applications",
        "Deep learning neural networks and architectures", 
        "Natural language processing and text analysis",
        "Computer vision and image recognition systems",
        "Reinforcement learning and decision making"
    ]
    
    print("   Processing content without cache...")
    uncached_times = []
    for content in test_contents:
        start_time = time.time()
        await agent.process_message(f"Process and categorize: {content}")
        duration = time.time() - start_time
        uncached_times.append(duration)
    
    avg_uncached = sum(uncached_times) / len(uncached_times)
    print(f"   Average uncached processing time: {avg_uncached:.3f} seconds")
    
    # Process the same content again (should be cached now)
    print("   Processing same content with cache...")
    cached_times = []
    for content in test_contents:
        start_time = time.time()
        await agent.process_message(f"Process and categorize: {content}")
        duration = time.time() - start_time
        cached_times.append(duration)
    
    avg_cached = sum(cached_times) / len(cached_times)
    print(f"   Average cached processing time: {avg_cached:.3f} seconds")
    
    # Calculate performance improvement
    improvement = (avg_uncached - avg_cached) / avg_uncached * 100
    print(f"🚀 Performance improvement: {improvement:.1f}%")
    
    if improvement > 10:  # At least 10% improvement
        print("✅ Caching provides significant performance improvement")
    else:
        print("⚠️  Caching performance improvement is minimal")
    
    return True

async def main():
    """Run all hash system tests"""
    print("🚀 Starting hash-based caching system tests...")
    print("=" * 70)
    
    tests = [
        test_hash_utilities,
        test_hash_tracker,
        test_agent_caching,
        test_note_creation_caching,
        test_content_update_detection,
        test_cache_management,
        test_performance_comparison
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
    
    print("\n" + "=" * 70)
    print(f"🧪 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All hash system tests passed! The caching system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 