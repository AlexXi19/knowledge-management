#!/usr/bin/env python3
"""
Test script to verify smolagents setup
"""

import sys
import traceback

def test_imports():
    """Test that all required imports work"""
    try:
        print("Testing imports...")
        
        # Test core imports
        import fastapi
        print("✓ fastapi import successful")
        
        import chromadb
        print("✓ chromadb import successful")
        
        import networkx
        print("✓ networkx import successful")
        
        import sentence_transformers
        print("✓ sentence-transformers import successful")
        
        # Test our modules
        from agent.knowledge_agent import KnowledgeAgent
        print("✓ KnowledgeAgent import successful")
        
        from knowledge.enhanced_knowledge_graph import get_enhanced_knowledge_graph
        print("✓ EnhancedKnowledgeGraph import successful")
        
        print("All imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        traceback.print_exc()
        return False

def test_knowledge_graph():
    """Test that we can create a knowledge graph"""
    try:
        print("\nTesting enhanced knowledge graph...")
        
        from knowledge.enhanced_knowledge_graph import get_enhanced_knowledge_graph
        
        # Get the enhanced knowledge graph
        kg = get_enhanced_knowledge_graph()
        print("✓ Enhanced knowledge graph creation successful")
        return True
        
    except Exception as e:
        print(f"✗ Enhanced knowledge graph error: {e}")
        traceback.print_exc()
        return False

def test_agent_creation():
    """Test that we can create a knowledge agent"""
    try:
        print("\nTesting agent creation...")
        
        from agent.knowledge_agent import KnowledgeAgent
        
        # Create agent
        agent = KnowledgeAgent()
        
        print("✓ Knowledge agent creation successful")
        return True
        
    except Exception as e:
        print(f"✗ Agent creation error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Testing smolagents setup...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_knowledge_graph,
        test_agent_creation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Your knowledge management backend setup is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 