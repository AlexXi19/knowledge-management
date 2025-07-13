#!/usr/bin/env python3
"""
Test script for the sync endpoint
"""

import asyncio
import json
import aiohttp
from pathlib import Path
import tempfile
import os
from datetime import datetime

async def test_sync_endpoint():
    """Test the sync endpoint functionality"""
    
    # Test with the default test-vault
    base_url = "http://localhost:8000"
    
    print("🧪 Testing sync endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # Test 1: Regular sync
            print("\n1. Testing regular sync...")
            async with session.post(f"{base_url}/sync") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Regular sync successful")
                    print(f"   📊 Files found: {data.get('vault_files_found', 0)}")
                    print(f"   📊 Nodes before: {data.get('graph_nodes_before', 0)}")
                    print(f"   📊 Nodes after: {data.get('graph_nodes_after', 0)}")
                    print(f"   📊 Total changes: {data.get('changes_detected', {}).get('total_changes', 0)}")
                    
                    changes = data.get('changes_detected', {})
                    if changes.get('total_changes', 0) > 0:
                        print(f"   📝 New files: {len(changes.get('new_files', []))}")
                        print(f"   📝 Modified files: {len(changes.get('modified_files', []))}")
                        print(f"   📝 Deleted files: {len(changes.get('deleted_files', []))}")
                        print(f"   📝 Unchanged files: {len(changes.get('unchanged_files', []))}")
                    
                    if data.get('actions_taken'):
                        print(f"   🔧 Actions taken: {data.get('actions_taken')}")
                    
                    if data.get('errors'):
                        print(f"   ❌ Errors: {data.get('errors')}")
                    
                    if data.get('warnings'):
                        print(f"   ⚠️  Warnings: {data.get('warnings')}")
                        
                else:
                    print(f"   ❌ Regular sync failed with status {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
            
            # Test 2: Force rebuild
            print("\n2. Testing force rebuild...")
            async with session.post(f"{base_url}/sync?force_rebuild=true") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Force rebuild successful")
                    print(f"   📊 Processing time: {data.get('processing_time_seconds', 0):.2f}s")
                    print(f"   📊 Total changes: {data.get('changes_detected', {}).get('total_changes', 0)}")
                    
                    # Force rebuild should process all files
                    changes = data.get('changes_detected', {})
                    if changes.get('force_rebuild'):
                        print(f"   🔄 Force rebuild mode: ON")
                        
                else:
                    print(f"   ❌ Force rebuild failed with status {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
            
            # Test 3: Get knowledge graph to verify sync worked
            print("\n3. Verifying knowledge graph after sync...")
            async with session.get(f"{base_url}/knowledge/graph") as response:
                if response.status == 200:
                    data = await response.json()
                    graph = data.get('graph', {})
                    nodes = graph.get('nodes', [])
                    edges = graph.get('edges', [])
                    
                    print(f"   ✅ Knowledge graph accessible")
                    print(f"   📊 Nodes: {len(nodes)}")
                    print(f"   📊 Edges: {len(edges)}")
                    
                    if nodes:
                        print(f"   📝 Sample node titles: {[node.get('title', 'Unknown') for node in nodes[:3]]}")
                    
                    if edges:
                        print(f"   🔗 Sample edge types: {list(set([edge.get('relation_type', 'Unknown') for edge in edges[:5]]))}")
                        
                else:
                    print(f"   ❌ Knowledge graph check failed with status {response.status}")
            
            # Test 4: Check cache stats
            print("\n4. Checking cache statistics...")
            async with session.get(f"{base_url}/cache/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Cache stats accessible")
                    
                    if isinstance(data, dict):
                        if 'total_cached_items' in data:
                            print(f"   📊 Cached items: {data.get('total_cached_items', 0)}")
                        if 'total_mapped_notes' in data:
                            print(f"   📊 Mapped notes: {data.get('total_mapped_notes', 0)}")
                        if 'last_updated' in data:
                            print(f"   📊 Last updated: {data.get('last_updated', 'Never')}")
                    else:
                        print(f"   📊 Cache stats: {data}")
                        
                else:
                    print(f"   ❌ Cache stats check failed with status {response.status}")
            
            print("\n✅ Sync endpoint test completed!")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting sync endpoint test...")
    print("⚠️  Make sure the backend server is running on localhost:8000")
    print("⚠️  Make sure you have some test notes in the vault")
    print()
    
    asyncio.run(test_sync_endpoint()) 