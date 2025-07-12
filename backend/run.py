#!/usr/bin/env python3
"""
Startup script for the Knowledge Management Backend
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import chromadb
        import networkx
        import sentence_transformers
        print("✓ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install dependencies with: uv sync")
        return False

def setup_environment():
    """Setup environment variables and directories"""
    # Create necessary directories
    directories = [
        "knowledge_base",
        "notes",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    # Check for .env file
    if not Path(".env").exists():
        print("⚠ .env file not found. Please create one based on .env.example")
        print("Required environment variables:")
        print("- OPENAI_API_KEY (optional, for AI-powered categorization)")
        print("- KNOWLEDGE_BASE_PATH (default: ./knowledge_base)")
        print("- NOTES_DIRECTORY (default: ./notes)")
        print("- EMBEDDING_MODEL (default: all-MiniLM-L6-v2)")
        print("ℹ️  Continuing with defaults...")
        return True
    
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Knowledge Management Backend...")
    print("📦 Using uv for package management")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("⚠ Environment setup incomplete. Continuing with defaults...")
    
    # Start the server
    print("\n🌐 Starting FastAPI server...")
    print("Access the API at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 