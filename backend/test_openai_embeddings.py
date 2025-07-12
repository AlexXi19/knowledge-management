#!/usr/bin/env python3
"""
Test script to demonstrate OpenAI embeddings functionality
Run this with your OpenAI API key to test the embedding service
"""

import os
import asyncio
import sys
from knowledge.embedding_service import EmbeddingService

async def test_openai_embeddings():
    """Test OpenAI embeddings if API key is available"""
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("To test OpenAI embeddings:")
        print("1. Set your API key: export OPENAI_API_KEY='your-key-here'")
        print("2. Or add it to your .env file")
        print("3. Run this script again")
        return False
    
    print("🔑 OpenAI API key found, testing embeddings...")
    
    try:
        # Test different OpenAI embedding models
        models_to_test = [
            "text-embedding-3-small",  # Most cost-effective
            "text-embedding-3-large",  # Higher quality
            # "text-embedding-ada-002",  # Legacy model
        ]
        
        for model in models_to_test:
            print(f"\n🧠 Testing {model}...")
            
            # Create embedding service with OpenAI
            service = EmbeddingService(
                provider_type="openai",
                model=model,
                api_key=api_key
            )
            
            provider_info = service.get_provider_info()
            print(f"   Provider: {provider_info['type']}")
            print(f"   Model: {provider_info['model']}")
            print(f"   Dimension: {provider_info['dimension']}")
            
            # Test single embedding
            test_text = "Knowledge management with AI embeddings"
            embedding = await service.embed_text(test_text)
            print(f"   ✓ Single embedding generated: {len(embedding)} dimensions")
            
            # Test multiple embeddings
            test_texts = [
                "Artificial intelligence and machine learning",
                "Natural language processing techniques",
                "Vector embeddings for semantic search"
            ]
            embeddings = await service.embed_texts(test_texts)
            print(f"   ✓ Batch embeddings generated: {len(embeddings)} texts")
            
            # Test similarity (basic check)
            if len(embeddings) >= 2:
                import numpy as np
                emb1 = np.array(embeddings[0])
                emb2 = np.array(embeddings[1])
                similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                print(f"   ✓ Similarity between first two texts: {similarity:.3f}")
        
        print("\n🎉 All OpenAI embedding tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing OpenAI embeddings: {e}")
        return False

async def compare_embeddings():
    """Compare OpenAI vs Sentence Transformer embeddings"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Skipping comparison - OpenAI API key not available")
        return
    
    print("\n📊 Comparing embedding providers...")
    
    test_text = "Machine learning algorithms for data analysis"
    
    # Test OpenAI
    openai_service = EmbeddingService(
        provider_type="openai",
        model="text-embedding-3-small",
        api_key=api_key
    )
    
    # Test Sentence Transformer
    st_service = EmbeddingService(
        provider_type="sentence_transformer",
        model_name="all-MiniLM-L6-v2"
    )
    
    import time
    
    # Time OpenAI embedding
    start_time = time.time()
    openai_embedding = await openai_service.embed_text(test_text)
    openai_time = time.time() - start_time
    
    # Time Sentence Transformer embedding
    start_time = time.time()
    st_embedding = await st_service.embed_text(test_text)
    st_time = time.time() - start_time
    
    print(f"\n📈 Embedding Comparison:")
    print(f"   OpenAI (text-embedding-3-small):")
    print(f"     - Dimensions: {len(openai_embedding)}")
    print(f"     - Time: {openai_time:.3f}s")
    print(f"   Sentence Transformer (all-MiniLM-L6-v2):")
    print(f"     - Dimensions: {len(st_embedding)}")
    print(f"     - Time: {st_time:.3f}s")

def show_configuration_examples():
    """Show how to configure different embedding providers"""
    
    print("\n🔧 Configuration Examples:")
    print("\n1. Using Sentence Transformers (default, free, runs locally):")
    print("   EMBEDDING_PROVIDER=sentence_transformer")
    print("   EMBEDDING_MODEL=all-MiniLM-L6-v2")
    
    print("\n2. Using OpenAI embeddings (requires API key, higher quality):")
    print("   EMBEDDING_PROVIDER=openai") 
    print("   OPENAI_EMBEDDING_MODEL=text-embedding-3-small")
    print("   OPENAI_API_KEY=your_api_key_here")
    
    print("\n3. Available OpenAI models:")
    print("   - text-embedding-3-small: 1536 dimensions, cost-effective")
    print("   - text-embedding-3-large: 3072 dimensions, higher quality")
    print("   - text-embedding-ada-002: 1536 dimensions, legacy model")
    
    print("\n💡 Tips:")
    print("   - Start with sentence_transformer for testing")
    print("   - Use OpenAI for production or higher quality needs")
    print("   - text-embedding-3-small offers best balance of cost/quality")

async def main():
    """Main test function"""
    print("🧪 OpenAI Embeddings Test Suite")
    print("=" * 50)
    
    # Show configuration examples first
    show_configuration_examples()
    
    # Test OpenAI embeddings
    await test_openai_embeddings()
    
    # Compare providers
    await compare_embeddings()
    
    print("\n✅ Testing complete!")
    print("\nTo use OpenAI embeddings in your knowledge management system:")
    print("1. Update your .env file with OpenAI settings")
    print("2. Restart the backend server")
    print("3. Your knowledge graph will use OpenAI embeddings for new content")

if __name__ == "__main__":
    asyncio.run(main()) 