#!/usr/bin/env python3
"""
Debug script to test cache stats functionality
"""

import asyncio
import traceback
from agent.knowledge_agent import KnowledgeAgent

async def test_cache_stats():
    """Test the cache stats functionality directly"""
    print("🔍 Testing cache stats functionality...")
    
    try:
        # Initialize the knowledge agent
        print("1. Creating KnowledgeAgent...")
        agent = KnowledgeAgent()
        print(f"   ✅ Agent created: {type(agent)}")
        
        # Check agent attributes
        print("2. Checking agent attributes...")
        print(f"   - knowledge_worker: {type(agent.knowledge_worker) if agent.knowledge_worker else 'None'}")
        print(f"   - manager_agent: {type(agent.manager_agent) if agent.manager_agent else 'None'}")
        print(f"   - enhanced_graph: {type(agent.enhanced_graph) if agent.enhanced_graph else 'None'}")
        print(f"   - initialized: {agent.initialized}")
        
        # Check for problematic attributes
        print("3. Checking for problematic attributes...")
        if hasattr(agent, 'agent'):
            print(f"   ⚠️  Agent has 'agent' attribute: {agent.agent}")
        else:
            print(f"   ✅ Agent does NOT have 'agent' attribute")
        
        # Initialize the agent
        print("4. Initializing agent...")
        await agent.initialize()
        print(f"   ✅ Agent initialized: {agent.initialized}")
        
        # Check enhanced graph
        print("5. Checking enhanced graph...")
        if agent.enhanced_graph:
            print(f"   ✅ Enhanced graph exists: {type(agent.enhanced_graph)}")
            if hasattr(agent.enhanced_graph, 'hash_tracker'):
                print(f"   ✅ Hash tracker exists: {type(agent.enhanced_graph.hash_tracker)}")
                
                # Try to get cache stats
                print("6. Getting cache stats...")
                cache_stats = agent.enhanced_graph.hash_tracker.get_cache_stats()
                print(f"   ✅ Cache stats retrieved: {cache_stats}")
                
                # Calculate additional metrics
                print("7. Calculating additional metrics...")
                notes_count = len(agent.enhanced_graph.nodes_by_id)
                print(f"   ✅ Notes count: {notes_count}")
                
                total_cached = cache_stats.get('total_cached_items', 0)
                total_mapped = cache_stats.get('total_mapped_notes', 0)
                
                stats = {
                    "cache_statistics": cache_stats,
                    "notes_count": notes_count,
                    "memory_efficiency": {
                        "cached_items_vs_notes_ratio": round(total_cached / max(notes_count, 1), 2),
                        "mapping_coverage_percent": round(total_mapped / max(notes_count, 1) * 100, 2)
                    },
                    "recommendations": []
                }
                
                print(f"   ✅ Final stats: {stats}")
                print("🎉 Cache stats test completed successfully!")
                return stats
                
            else:
                print("   ❌ Enhanced graph has no hash_tracker")
        else:
            print("   ❌ No enhanced graph")
            
    except Exception as e:
        print(f"❌ Error in cache stats test: {e}")
        print("Stack trace:")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_cache_stats()) 