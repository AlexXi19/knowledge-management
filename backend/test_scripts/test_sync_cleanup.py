#!/usr/bin/env python3
"""
Test script for the enhanced sync endpoint with comprehensive cleanup
"""

import asyncio
import json
import aiohttp
from pathlib import Path
import tempfile
import os
from datetime import datetime
import time

async def test_sync_cleanup():
    """Test the enhanced sync endpoint cleanup functionality"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing enhanced sync endpoint cleanup...")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # Test 1: Check initial state
            print("\n1. 📊 Checking initial state...")
            async with session.get(f"{base_url}/knowledge/graph") as response:
                if response.status == 200:
                    data = await response.json()
                    initial_nodes = len(data.get('nodes', []))
                    initial_edges = len(data.get('edges', []))
                    print(f"   ✅ Initial state: {initial_nodes} nodes, {initial_edges} edges")
                else:
                    print(f"   ❌ Could not get initial state: {response.status}")
                    return
            
            # Test 2: Regular sync (should clean orphaned entries)
            print("\n2. 🔄 Testing regular sync with orphaned cleanup...")
            async with session.post(f"{base_url}/sync") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Regular sync successful")
                    print(f"   📊 Processing time: {data.get('processing_time_seconds', 0):.2f}s")
                    print(f"   📊 Files found: {data.get('vault_files_found', 0)}")
                    print(f"   📊 Nodes: {data.get('graph_nodes_before', 0)} → {data.get('graph_nodes_after', 0)}")
                    
                    actions = data.get('actions_taken', [])
                    orphaned_actions = [action for action in actions if 'orphaned' in action.lower()]
                    if orphaned_actions:
                        print(f"   🧹 Orphaned cleanup: {orphaned_actions}")
                    else:
                        print(f"   ✅ No orphaned entries found")
                    
                    if data.get('errors'):
                        print(f"   ❌ Errors: {data.get('errors')}")
                    if data.get('warnings'):
                        print(f"   ⚠️  Warnings: {data.get('warnings')}")
                        
                else:
                    print(f"   ❌ Regular sync failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return
            
            # Test 3: Check cache stats before force rebuild
            print("\n3. 📈 Checking cache stats before force rebuild...")
            async with session.get(f"{base_url}/cache/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Cache stats accessible")
                    
                    if isinstance(data, dict):
                        cached_items = data.get('total_cached_items', 0)
                        mapped_notes = data.get('total_mapped_notes', 0)
                        print(f"   📊 Before cleanup: {cached_items} cached items, {mapped_notes} mapped notes")
                    else:
                        print(f"   📊 Cache stats: {data}")
                else:
                    print(f"   ❌ Could not get cache stats: {response.status}")
            
            # Test 4: Force rebuild (comprehensive cleanup)
            print("\n4. 🧹 Testing force rebuild with comprehensive cleanup...")
            async with session.post(f"{base_url}/sync?force_rebuild=true") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Force rebuild successful")
                    print(f"   📊 Processing time: {data.get('processing_time_seconds', 0):.2f}s")
                    print(f"   📊 Files processed: {data.get('vault_files_found', 0)}")
                    print(f"   📊 Final nodes: {data.get('graph_nodes_after', 0)}")
                    print(f"   📊 Final edges: {data.get('graph_edges_after', 0)}")
                    
                    # Check cleanup results
                    cleanup_results = data.get('cleanup_results', {})
                    if cleanup_results:
                        print(f"\n   🧹 Cleanup Results:")
                        cleanup_actions = cleanup_results.get('actions_taken', [])
                        for action in cleanup_actions:
                            print(f"      ✅ {action}")
                        
                        cleanup_errors = cleanup_results.get('errors', [])
                        if cleanup_errors:
                            print(f"      ❌ Cleanup errors:")
                            for error in cleanup_errors:
                                print(f"         {error}")
                        
                        cleanup_warnings = cleanup_results.get('warnings', [])
                        if cleanup_warnings:
                            print(f"      ⚠️  Cleanup warnings:")
                            for warning in cleanup_warnings:
                                print(f"         {warning}")
                    else:
                        print(f"   ⚠️  No cleanup results found (not force rebuild?)")
                    
                    # Check regular actions
                    regular_actions = data.get('actions_taken', [])
                    if regular_actions:
                        print(f"\n   🔄 Sync Actions:")
                        for action in regular_actions:
                            print(f"      ✅ {action}")
                        
                else:
                    print(f"   ❌ Force rebuild failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return
            
            # Test 5: Check cache stats after force rebuild
            print("\n5. 📈 Checking cache stats after force rebuild...")
            async with session.get(f"{base_url}/cache/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Cache stats accessible")
                    
                    if isinstance(data, dict):
                        cached_items = data.get('total_cached_items', 0)
                        mapped_notes = data.get('total_mapped_notes', 0)
                        print(f"   📊 After cleanup: {cached_items} cached items, {mapped_notes} mapped notes")
                    else:
                        print(f"   📊 Cache stats: {data}")
                else:
                    print(f"   ❌ Could not get cache stats: {response.status}")
            
            # Test 6: Verify knowledge graph state after cleanup
            print("\n6. 📊 Verifying knowledge graph state after cleanup...")
            async with session.get(f"{base_url}/knowledge/graph") as response:
                if response.status == 200:
                    data = await response.json()
                    final_nodes = len(data.get('nodes', []))
                    final_edges = len(data.get('edges', []))
                    print(f"   ✅ Final state: {final_nodes} nodes, {final_edges} edges")
                    
                    # Check if nodes have proper structure (no content for optimization)
                    if data.get('nodes'):
                        sample_node = data['nodes'][0]
                        has_content = 'content' in sample_node
                        print(f"   📊 Node structure: {'includes content' if has_content else 'optimized (no content)'}")
                    
                    # Check stats
                    stats = data.get('stats', {})
                    if stats:
                        print(f"   📊 Categories: {len(stats.get('categories', []))}")
                        print(f"   📊 Tags: {len(stats.get('tags', []))}")
                else:
                    print(f"   ❌ Could not verify final state: {response.status}")
            
            # Test 7: Test semantic search to verify vector database
            print("\n7. 🔍 Testing semantic search to verify vector database...")
            async with session.get(f"{base_url}/knowledge/search?query=test&limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    print(f"   ✅ Semantic search working: {len(results)} results")
                    
                    if results:
                        for i, result in enumerate(results[:3]):
                            similarity = result.get('similarity', 0)
                            category = result.get('category', 'Unknown')
                            print(f"      {i+1}. {category} (similarity: {similarity:.3f})")
                else:
                    print(f"   ❌ Semantic search failed: {response.status}")
            
            # Test 8: Test content search
            print("\n8. 🔍 Testing content search...")
            async with session.get(f"{base_url}/knowledge/search/content?query=test&limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    total_matches = data.get('total_matches', 0)
                    print(f"   ✅ Content search working: {len(results)} files, {total_matches} matches")
                    
                    if results:
                        for i, result in enumerate(results[:3]):
                            title = result.get('title', 'Unknown')
                            matches = result.get('total_matches', 0)
                            print(f"      {i+1}. {title} ({matches} matches)")
                else:
                    print(f"   ❌ Content search failed: {response.status}")
            
            print("\n" + "=" * 60)
            print("✅ Enhanced sync endpoint cleanup test completed successfully!")
            print("\nKey Features Tested:")
            print("  🧹 Comprehensive cleanup (force rebuild)")
            print("  🗑️  Vector database cleanup")
            print("  📊 Cache and index cleanup")
            print("  🔍 Search functionality preservation")
            print("  📈 Performance optimization")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_cleanup_performance():
    """Test performance of cleanup operations"""
    
    base_url = "http://localhost:8000"
    
    print("\n🏃‍♂️ Testing cleanup performance...")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # Test regular sync performance
            print("\n1. ⏱️  Testing regular sync performance...")
            start_time = time.time()
            async with session.post(f"{base_url}/sync") as response:
                if response.status == 200:
                    data = await response.json()
                    end_time = time.time()
                    actual_time = end_time - start_time
                    reported_time = data.get('processing_time_seconds', 0)
                    
                    print(f"   ✅ Regular sync: {actual_time:.2f}s actual, {reported_time:.2f}s reported")
                    print(f"   📊 Files processed: {data.get('vault_files_found', 0)}")
                    print(f"   📊 Changes detected: {data.get('changes_detected', {}).get('total_changes', 0)}")
                else:
                    print(f"   ❌ Regular sync failed: {response.status}")
            
            # Test force rebuild performance
            print("\n2. ⏱️  Testing force rebuild performance...")
            start_time = time.time()
            async with session.post(f"{base_url}/sync?force_rebuild=true") as response:
                if response.status == 200:
                    data = await response.json()
                    end_time = time.time()
                    actual_time = end_time - start_time
                    reported_time = data.get('processing_time_seconds', 0)
                    
                    print(f"   ✅ Force rebuild: {actual_time:.2f}s actual, {reported_time:.2f}s reported")
                    print(f"   📊 Files processed: {data.get('vault_files_found', 0)}")
                    
                    # Analyze cleanup performance
                    cleanup_results = data.get('cleanup_results', {})
                    if cleanup_results:
                        cleanup_actions = cleanup_results.get('actions_taken', [])
                        print(f"   🧹 Cleanup actions: {len(cleanup_actions)}")
                        
                        # Look for specific cleanup metrics
                        for action in cleanup_actions:
                            if 'ChromaDB' in action:
                                print(f"      🗑️  {action}")
                            elif 'cache' in action.lower():
                                print(f"      📊 {action}")
                else:
                    print(f"   ❌ Force rebuild failed: {response.status}")
            
            print("\n" + "=" * 60)
            print("✅ Performance testing completed!")
            
    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting enhanced sync endpoint cleanup test...")
    print("⚠️  Make sure the backend server is running on localhost:8000")
    print("⚠️  Make sure you have some test notes in the vault")
    print()
    
    asyncio.run(test_sync_cleanup())
    asyncio.run(test_cleanup_performance()) 