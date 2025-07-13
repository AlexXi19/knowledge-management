#!/usr/bin/env python3
"""
Run script for the smolagents-powered knowledge management system
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import smolagents
        print(f"✅ smolagents version: {smolagents.__version__}")
    except ImportError:
        print("❌ smolagents not found. Please install with: uv add smolagents[toolkit,litellm]")
        return False
    
    try:
        import chromadb
        print(f"✅ chromadb available")
    except ImportError:
        print("❌ chromadb not found. Please install with: uv add chromadb")
        return False
    
    return True

def check_api_keys():
    """Check for available API keys and recommend setup"""
    api_keys = {}
    
    # Check OpenRouter API key (highest priority - access to all models)
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        api_keys["OpenRouter"] = "✅ Found"
        openrouter_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        print(f"✅ OpenRouter API key found - will use {openrouter_model}")
    else:
        api_keys["OpenRouter"] = "❌ Missing"
    
    # Check Anthropic API key (second priority for Claude Sonnet)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        api_keys["Anthropic"] = "✅ Found"
        claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        print(f"✅ Anthropic API key found - will use {claude_model}")
    else:
        api_keys["Anthropic"] = "❌ Missing"
    
    # Check HuggingFace token
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        api_keys["HuggingFace"] = "✅ Found"
        print("✅ HuggingFace token found")
    else:
        api_keys["HuggingFace"] = "❌ Missing"
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        api_keys["OpenAI"] = "✅ Found"
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        print(f"✅ OpenAI API key found - will use {openai_model}")
    else:
        api_keys["OpenAI"] = "❌ Missing"
    
    # Check embedding provider
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "sentence_transformer")
    print(f"📊 Embedding provider: {embedding_provider}")
    
    if not any("✅" in status for status in api_keys.values()):
        print("\n⚠️  No API keys found. The system will use free HuggingFace models (rate limited).")
        print("\nTo use premium models, set one of these environment variables (in priority order):")
        print("  1. OPENROUTER_API_KEY=your_openrouter_key (access to all models)")
        print("  2. ANTHROPIC_API_KEY=your_anthropic_key (for Claude Sonnet models)")
        print("  3. OPENAI_API_KEY=your_openai_key (for GPT models)")
        print("  4. HF_TOKEN=your_huggingface_token (for HuggingFace models)")
        print("\nOptional model selection:")
        print("  • OPENROUTER_MODEL=anthropic/claude-3.5-sonnet (default)")
        print("  • CLAUDE_MODEL=claude-3-5-sonnet-20241022 (default)")
        print("  • OPENAI_MODEL=gpt-4o-mini (default)")
        print("  • EMBEDDING_PROVIDER=openai|sentence_transformer")
    
    return api_keys

def main():
    """Main entry point"""
    print("🚀 Starting smolagents-powered knowledge management system...")
    print("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check API keys and configuration
    api_keys = check_api_keys()
    
    print("\n" + "=" * 70)
    print("🤖 Initializing knowledge management agent...")
    
    # Detect development mode
    is_dev = (
        os.getenv("ENVIRONMENT") == "development" or
        os.getenv("DEV") == "true" or
        "--dev" in sys.argv or
        "--reload" in sys.argv
    )
    
    # Import and run the main application
    try:
        from main import app
        import uvicorn
        
        print("✅ All systems ready!")
        print("🌐 Starting server on http://localhost:8000")
        print("📚 API documentation available at http://localhost:8000/docs")
        print("💾 Cache management at http://localhost:8000/cache/stats")
        
        if is_dev:
            print("🔄 Hot reload enabled for development")
        else:
            print("🏭 Production mode - use --dev flag for hot reload")
            
        print("\nPress Ctrl+C to stop the server")
        print("=" * 70)
        
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=is_dev)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 