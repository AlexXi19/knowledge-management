#!/usr/bin/env python3
"""
Test script to make HTTP requests to the server and verify the 500 error is fixed
"""

import asyncio
import httpx
import json
import time

async def test_server_endpoints():
    """Test various server endpoints"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧪 Testing server endpoints...")
        
        # Test health check
        try:
            response = await client.get(f"{base_url}/health")
            print(f"✅ Health check: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
        
        # Test agent info
        try:
            response = await client.get(f"{base_url}/agent/info")
            print(f"✅ Agent info: {response.status_code}")
            if response.status_code == 200:
                info = response.json()
                print(f"   Agent type: {info.get('agent_type')}")
                print(f"   Tools count: {info.get('tools_count')}")
        except Exception as e:
            print(f"❌ Agent info failed: {e}")
        
        # Test the chat endpoint that was causing 500 errors
        try:
            chat_request = {
                "message": "Hello, can you help me create a note about JavaScript?",
                "conversation_history": []
            }
            
            print("\n📤 Testing chat endpoint...")
            response = await client.post(
                f"{base_url}/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"✅ Chat endpoint: {response.status_code}")
            
            if response.status_code == 200:
                chat_response = response.json()
                print(f"   Response: {chat_response['response'][:100]}...")
                print(f"   Categories: {chat_response.get('categories', [])}")
            else:
                print(f"   Error response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat endpoint failed: {e}")
            return False
        
        # Test with conversation history
        try:
            chat_request_with_history = {
                "message": "Can you tell me more about Python programming?",
                "conversation_history": [
                    {
                        "role": "user", 
                        "content": "Hello"
                    },
                    {
                        "role": "assistant", 
                        "content": "Hi! How can I help you with knowledge management?"
                    }
                ]
            }
            
            print("\n📤 Testing chat with conversation history...")
            response = await client.post(
                f"{base_url}/chat",
                json=chat_request_with_history,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"✅ Chat with history: {response.status_code}")
            
            if response.status_code == 200:
                chat_response = response.json()
                print(f"   Response: {chat_response['response'][:100]}...")
            else:
                print(f"   Error response: {response.text}")
                
        except Exception as e:
            print(f"❌ Chat with history failed: {e}")
        
        # Test get all notes
        try:
            response = await client.get(f"{base_url}/notes")
            print(f"✅ Get all notes: {response.status_code}")
            if response.status_code == 200:
                notes_response = response.json()
                print(f"   Notes count: {len(notes_response.get('notes', []))}")
        except Exception as e:
            print(f"❌ Get notes failed: {e}")
        
        return True

def check_server_running():
    """Check if the server is running"""
    import subprocess
    try:
        # Check if something is running on port 8000
        result = subprocess.run(
            ["lsof", "-i", ":8000"], 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0
    except:
        return False

async def main():
    """Main test function"""
    print("🚀 Testing Knowledge Management Server...")
    print("=" * 60)
    
    # Check if server is running
    if not check_server_running():
        print("❌ Server is not running on port 8000")
        print("   Please start the server with: uv run python main.py")
        return False
    
    print("✅ Server is running on port 8000")
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    await asyncio.sleep(2)
    
    # Run tests
    success = await test_server_endpoints()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All server tests passed! The 500 error is fixed.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 