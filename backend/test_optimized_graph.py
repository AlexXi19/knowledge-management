#!/usr/bin/env python3
"""
Test script for optimized knowledge graph (without content storage)
"""

import asyncio
import json
import aiohttp
from pathlib import Path
import tempfile
import os

async def test_optimized_graph():
    """Test the optimized knowledge graph functionality"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing optimized knowledge graph (content-free)...")
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # Test 1: Get knowledge graph data (should not contain content)
            print("\n1. Testing knowledge graph data structure...")
            async with session.get(f"{base_url}/knowledge/graph") as response:
                if response.status == 200:
                    data = await response.json()
                    graph = data.get('graph', {})
                    nodes = graph.get('nodes', [])
                    
                    print(f"   ✅ Graph data retrieved successfully")
                    print(f"   📊 Nodes: {len(nodes)}")
                    print(f"   📊 Edges: {len(graph.get('edges', []))}")
                    
                    if nodes:
                        sample_node = nodes[0]
                        print(f"   📝 Sample node keys: {list(sample_node.keys())}")
                        
                        # Verify content is NOT in the node data
                        if 'content' not in sample_node:
                            print(f"   ✅ Content correctly excluded from graph data")
                        else:
                            print(f"   ❌ Content still present in graph data!")
                            
                        # Verify essential fields are present
                        required_fields = ['id', 'title', 'category', 'tags', 'file_path', 'content_hash']
                        missing_fields = [field for field in required_fields if field not in sample_node]
                        
                        if not missing_fields:
                            print(f"   ✅ All required fields present")
                        else:
                            print(f"   ⚠️  Missing fields: {missing_fields}")
                            
                else:
                    print(f"   ❌ Graph data retrieval failed with status {response.status}")
            
            # Test 2: Test content search functionality
            print("\n2. Testing content search in files...")
            test_query = "idea"  # Common word likely to be in notes
            
            async with session.get(f"{base_url}/knowledge/search/content?query={test_query}&limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    print(f"   ✅ Content search successful")
                    print(f"   📊 Files found: {len(results)}")
                    print(f"   📊 Total matches: {data.get('total_matches', 0) if len(results) > 0 else 0}")
                    
                    if results:
                        sample_result = results[0]
                        print(f"   📝 Sample result keys: {list(sample_result.keys())}")
                        
                        # Verify match structure
                        if 'matches' in sample_result and sample_result['matches']:
                            sample_match = sample_result['matches'][0]
                            print(f"   📝 Sample match keys: {list(sample_match.keys())}")
                            print(f"   📝 Line number: {sample_match.get('line_number', 'N/A')}")
                            print(f"   📝 Line content: {sample_match.get('line_content', 'N/A')[:50]}...")
                            
                else:
                    print(f"   ❌ Content search failed with status {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
            
            # Test 3: Test regular semantic search (should still work)
            print("\n3. Testing semantic search...")
            async with session.get(f"{base_url}/knowledge/search?query={test_query}&limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    print(f"   ✅ Semantic search successful")
                    print(f"   📊 Results found: {len(results)}")
                    
                    if results:
                        sample_result = results[0]
                        print(f"   📝 Sample result keys: {list(sample_result.keys())}")
                        
                        # Verify semantic search still returns content (from ChromaDB)
                        if 'content' in sample_result:
                            print(f"   ✅ Semantic search correctly returns content from embeddings")
                        else:
                            print(f"   ⚠️  Semantic search missing content")
                            
                else:
                    print(f"   ❌ Semantic search failed with status {response.status}")
            
            # Test 4: Test notes list (should not contain content)
            print("\n4. Testing notes list...")
            async with session.get(f"{base_url}/notes") as response:
                if response.status == 200:
                    data = await response.json()
                    notes = data.get('notes', [])
                    
                    print(f"   ✅ Notes list retrieved successfully")
                    print(f"   📊 Notes count: {len(notes)}")
                    
                    if notes:
                        sample_note = notes[0]
                        print(f"   📝 Sample note keys: {list(sample_note.keys())}")
                        
                        # Verify content is NOT in the notes list
                        if 'content' not in sample_note:
                            print(f"   ✅ Content correctly excluded from notes list")
                        else:
                            print(f"   ❌ Content still present in notes list!")
                            
                        # Verify content_hash is present
                        if 'content_hash' in sample_note:
                            print(f"   ✅ Content hash correctly included")
                        else:
                            print(f"   ⚠️  Content hash missing")
                            
                else:
                    print(f"   ❌ Notes list retrieval failed with status {response.status}")
            
            # Test 5: Test sync to ensure it works with optimized structure
            print("\n5. Testing sync with optimized structure...")
            async with session.post(f"{base_url}/sync") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"   ✅ Sync completed successfully")
                    print(f"   📊 Files found: {data.get('vault_files_found', 0)}")
                    print(f"   📊 Graph nodes: {data.get('graph_nodes_after', 0)}")
                    print(f"   📊 Processing time: {data.get('processing_time_seconds', 0):.2f}s")
                    
                    if data.get('errors'):
                        print(f"   ⚠️  Sync errors: {data.get('errors')}")
                    
                else:
                    print(f"   ❌ Sync failed with status {response.status}")
            
            print("\n✅ Optimized knowledge graph test completed!")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def print_memory_comparison():
    """Print memory usage comparison info"""
    print("\n📊 Memory Optimization Benefits:")
    print("=" * 50)
    print("🔸 Knowledge graph nodes: No longer store full content")
    print("🔸 API responses: Reduced payload size")
    print("🔸 Memory usage: Significantly reduced for large vaults")
    print("🔸 Content search: Available via file-based search")
    print("🔸 Semantic search: Still available via ChromaDB")
    print("🔸 Sync performance: Improved due to smaller data structures")
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 Starting optimized knowledge graph test...")
    print("⚠️  Make sure the backend server is running on localhost:8000")
    print("⚠️  Make sure you have some test notes in the vault")
    print()
    
    print_memory_comparison()
    
    asyncio.run(test_optimized_graph()) 