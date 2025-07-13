#!/usr/bin/env python3
"""
Test script to verify concurrent request handling
This tests that long-running chat requests don't block other endpoints
"""

import asyncio
import httpx
import time
import json
from typing import List, Dict, Any

async def test_concurrent_requests():
    """Test that the server handles concurrent requests without blocking"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing concurrent request handling...")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Start a long-running chat request
        print("📤 Starting long-running chat request...")
        
        chat_request = {
            "message": "Please create a comprehensive note about machine learning algorithms including neural networks, decision trees, and clustering methods. Make sure to organize this information properly.",
            "conversation_history": []
        }
        
        # Start chat task in background
        chat_task = asyncio.create_task(
            client.post(f"{base_url}/chat", json=chat_request)
        )
        
        # Wait a moment to ensure chat processing starts
        await asyncio.sleep(0.5)
        
        # Test 2: While chat is processing, test other endpoints
        print("⚡ Testing other endpoints while chat is processing...")
        
        # Test health check (should be immediate)
        start_time = time.time()
        try:
            health_response = await client.get(f"{base_url}/health")
            health_time = time.time() - start_time
            
            if health_response.status_code == 200:
                print(f"✅ Health check: {health_response.status_code} ({health_time:.2f}s)")
            else:
                print(f"❌ Health check failed: {health_response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test agent info (should be immediate)
        start_time = time.time()
        try:
            info_response = await client.get(f"{base_url}/agent/info")
            info_time = time.time() - start_time
            
            if info_response.status_code == 200:
                print(f"✅ Agent info: {info_response.status_code} ({info_time:.2f}s)")
            else:
                print(f"❌ Agent info failed: {info_response.status_code}")
        except Exception as e:
            print(f"❌ Agent info error: {e}")
        
        # Test tasks endpoint (should be immediate)
        start_time = time.time()
        try:
            tasks_response = await client.get(f"{base_url}/tasks")
            tasks_time = time.time() - start_time
            
            if tasks_response.status_code == 200:
                print(f"✅ Tasks endpoint: {tasks_response.status_code} ({tasks_time:.2f}s)")
            else:
                print(f"❌ Tasks endpoint failed: {tasks_response.status_code}")
        except Exception as e:
            print(f"❌ Tasks endpoint error: {e}")
        
        # Test multiple concurrent health checks
        print("🔄 Testing multiple concurrent requests...")
        
        concurrent_tasks = []
        for i in range(5):
            task = asyncio.create_task(
                client.get(f"{base_url}/health")
            )
            concurrent_tasks.append(task)
        
        # Wait for all concurrent tasks
        start_time = time.time()
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        concurrent_time = time.time() - start_time
        
        success_count = sum(1 for result in concurrent_results if not isinstance(result, Exception) and result.status_code == 200)
        print(f"✅ Concurrent requests: {success_count}/5 succeeded ({concurrent_time:.2f}s total)")
        
        # Test 3: Test background task endpoint
        print("🔄 Testing background task processing...")
        
        try:
            async_response = await client.post(f"{base_url}/chat/async", json=chat_request)
            
            if async_response.status_code == 200:
                task_data = async_response.json()
                task_id = task_data["task_id"]
                print(f"✅ Background task started: {task_id}")
                
                # Poll task status
                for i in range(10):
                    await asyncio.sleep(2)
                    
                    status_response = await client.get(f"{base_url}/chat/task/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"   Task status: {status_data['status']}")
                        
                        if status_data['status'] in ['completed', 'failed']:
                            break
                    else:
                        print(f"   ❌ Status check failed: {status_response.status_code}")
                        break
                
            else:
                print(f"❌ Background task failed: {async_response.status_code}")
                
        except Exception as e:
            print(f"❌ Background task error: {e}")
        
        # Test 4: Test streaming endpoint
        print("📡 Testing streaming endpoint...")
        
        try:
            stream_request = {
                "message": "Create a simple note about Python programming",
                "conversation_history": []
            }
            
            stream_start_time = time.time()
            
            async with client.stream("POST", f"{base_url}/chat/stream", json=stream_request) as response:
                if response.status_code == 200:
                    chunk_count = 0
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            chunk_count += 1
                            if chunk_count <= 3:  # Show first 3 chunks
                                print(f"   📦 Stream chunk {chunk_count}: {chunk.strip()[:50]}...")
                        
                        # Test that other requests still work during streaming
                        if chunk_count == 2:
                            health_during_stream = await client.get(f"{base_url}/health")
                            if health_during_stream.status_code == 200:
                                print(f"   ✅ Health check during streaming: OK")
                            else:
                                print(f"   ❌ Health check during streaming failed")
                    
                    stream_time = time.time() - stream_start_time
                    print(f"✅ Streaming completed: {chunk_count} chunks ({stream_time:.2f}s)")
                else:
                    print(f"❌ Streaming failed: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Streaming error: {e}")
        
        # Wait for the original chat task to complete
        print("⏳ Waiting for original chat task to complete...")
        try:
            chat_response = await chat_task
            if chat_response.status_code == 200:
                print("✅ Original chat task completed successfully")
            else:
                print(f"❌ Original chat task failed: {chat_response.status_code}")
        except Exception as e:
            print(f"❌ Original chat task error: {e}")
        
        print("=" * 60)
        print("🎯 Concurrent request testing completed!")
        
        # Summary
        print("\n📊 Test Summary:")
        print("- Long-running chat requests should not block other endpoints")
        print("- Health checks should respond immediately (< 1s)")
        print("- Multiple concurrent requests should work")
        print("- Background tasks should be available")
        print("- Streaming should work without blocking other requests")

if __name__ == "__main__":
    asyncio.run(test_concurrent_requests()) 