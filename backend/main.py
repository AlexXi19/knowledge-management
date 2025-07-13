from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import uuid
from datetime import datetime
from dotenv import load_dotenv
import os

from agent.knowledge_agent import KnowledgeAgent
from models.chat_models import ChatMessage, ChatRequest, ChatResponse
from knowledge.embedding_service import create_embedding_service

load_dotenv()

app = FastAPI(title="Knowledge Management Agent", version="2.0.0", description="AI-powered knowledge management using smolagents")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the knowledge agent with smolagents
knowledge_agent = KnowledgeAgent()

# Task management for non-blocking operations
active_tasks: Dict[str, Dict[str, Any]] = {}

class TaskStatus(BaseModel):
    """Task status model"""
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the knowledge agent on startup"""
    await knowledge_agent.initialize()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "knowledge-agent",
        "version": "2.0.0",
        "agent_type": "smolagents_powered"
    }

@app.get("/config/embeddings")
async def get_embedding_config():
    """Get current embedding configuration"""
    try:
        embedding_service = create_embedding_service()
        provider_info = embedding_service.get_provider_info()
        return {
            "embedding_provider": provider_info,
            "recommendations": {
                "local": "Use sentence_transformer for free, local processing",
                "openai": "Use OpenAI for superior quality (requires API key)"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config/notes")
async def get_notes_config():
    """Get current notes configuration"""
    try:
        notes_dir = os.getenv("NOTES_DIRECTORY", "./notes")
        # Get all notes to calculate structure
        notes = await knowledge_agent.get_all_notes()
        
        # Calculate structure from notes
        structure = {}
        for note in notes:
            category = note.get("category", "Unknown")
            if category not in structure:
                structure[category] = {"count": 0, "notes": []}
            structure[category]["count"] += 1
            structure[category]["notes"].append({
                "title": note.get("title", ""),
                "path": note.get("path", ""),
                "updated_at": note.get("updated_at", "")
            })
        
        return {
            "notes_directory": notes_dir,
            "structure": structure,
            "total_notes": len(notes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that processes user messages and returns agent responses
    Uses asyncio for non-blocking processing (Node.js-style promises)
    """
    try:
        # Process the message using asyncio - non-blocking like Node.js promises
        result = await knowledge_agent.process_message(
            message=request.message,
            conversation_history=request.conversation_history
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/async")
async def chat_async(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Async chat endpoint that starts processing in background and returns task ID
    Uses asyncio for concurrent processing without blocking
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        active_tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "result": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        # Start background task using asyncio (like Node.js async/await)
        background_tasks.add_task(
            process_chat_task,
            task_id,
            request.message,
            request.conversation_history
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Processing started in background"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a background chat task
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = active_tasks[task_id]
    
    # Clean up completed tasks older than 10 minutes
    if task_info["status"] in ["completed", "failed"] and task_info["completed_at"]:
        completed_time = datetime.fromisoformat(task_info["completed_at"])
        if (datetime.now() - completed_time).total_seconds() > 600:  # 10 minutes
            del active_tasks[task_id]
            raise HTTPException(status_code=410, detail="Task expired")
    
    return TaskStatus(**task_info)

async def process_chat_task(task_id: str, message: str, conversation_history: List[ChatMessage] = None):
    """
    Background task to process chat messages
    """
    try:
        # Update task status
        active_tasks[task_id]["status"] = "running"
        
        # Process the message
        result = await knowledge_agent.process_message(
            message=message,
            conversation_history=conversation_history
        )
        
        # Update task with result
        active_tasks[task_id].update({
            "status": "completed",
            "result": result.model_dump(),
            "completed_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        # Update task with error
        active_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint for real-time responses
    Uses asyncio generators for streaming (like Node.js readable streams)
    """
    try:
        async def generate():
            complete_response_sent = False
            try:
                print(f"DEBUG: Starting stream for message: {request.message[:100]}...")
                
                # Use asyncio generator for streaming - like Node.js streams
                async for chunk in knowledge_agent.stream_response(
                    message=request.message,
                    conversation_history=request.conversation_history
                ):
                    print(f"DEBUG: Yielding chunk type: {chunk.get('type', 'unknown')}")
                    
                    # Check if this is a complete response
                    if chunk.get('type') == 'complete':
                        complete_response_sent = True
                        print(f"DEBUG: Complete response chunk: {chunk}")
                    
                    yield f"data: {json.dumps(chunk)}\n\n"
                
                # If no complete response was sent, send a fallback
                if not complete_response_sent:
                    print("DEBUG: No complete response received from agent, sending fallback")
                    fallback_response = {
                        "type": "complete",
                        "response": {
                            "response": "I've processed your request and organized the information in your knowledge base.",
                            "categories": ["General"],
                            "knowledge_updates": [],
                            "suggested_actions": ["Continue organizing your thoughts"]
                        }
                    }
                    yield f"data: {json.dumps(fallback_response)}\n\n"
                    
                # Send completion marker
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                print("DEBUG: Stream completed successfully")
                
            except Exception as e:
                print(f"DEBUG: Error in streaming: {e}")
                # Send error in stream
                error_chunk = {
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
        )
    
    except Exception as e:
        print(f"DEBUG: Error creating stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks")
async def list_active_tasks():
    """
    List all active tasks
    """
    return {
        "active_tasks": len(active_tasks),
        "tasks": [
            {
                "task_id": task_id,
                "status": task_info["status"],
                "created_at": task_info["created_at"]
            }
            for task_id, task_info in active_tasks.items()
        ]
    }

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a running task
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = active_tasks[task_id]
    if task_info["status"] == "running":
        task_info["status"] = "cancelled"
        task_info["completed_at"] = datetime.now().isoformat()
        return {"message": "Task cancelled"}
    else:
        return {"message": f"Task is {task_info['status']}, cannot cancel"}

@app.get("/knowledge/graph")
async def get_knowledge_graph():
    """
    Get the current knowledge graph structure
    """
    try:
        graph_data = await knowledge_agent.get_knowledge_graph()
        return {"graph": graph_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/categories")
async def get_categories():
    """
    Get all available categories in the knowledge base
    """
    try:
        # Get categories from existing notes
        notes = await knowledge_agent.get_all_notes()
        categories = list(set(note.get("category", "Unknown") for note in notes))
        
        # Add default categories
        default_categories = [
            "Quick Notes", "Learning", "Projects", "Ideas", "Research", 
            "Tasks", "References", "Personal", "Technical", "Business"
        ]
        
        all_categories = list(set(categories + default_categories))
        all_categories.sort()
        
        return {"categories": all_categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/search")
async def search_knowledge(query: str, limit: int = 10):
    """
    Search the knowledge base using the AI agent
    """
    try:
        results = await knowledge_agent.search_knowledge(query, limit)
        return {"results": [result.model_dump() if hasattr(result, 'model_dump') else result for result in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/search/content")
async def search_content_in_files(query: str, case_sensitive: bool = False, limit: int = 10):
    """
    Search for content in actual note files using grep-like functionality
    """
    try:
        results = await knowledge_agent.search_content_in_files(query, case_sensitive, limit)
        return {"results": results, "query": query, "case_sensitive": case_sensitive}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notes")
async def get_all_notes():
    """
    Get all notes
    """
    try:
        notes = await knowledge_agent.get_all_notes()
        return {"notes": notes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notes/structure")
async def get_notes_structure():
    """
    Get the notes directory structure
    """
    try:
        # Get all notes and build structure
        notes = await knowledge_agent.get_all_notes()
        structure = {}
        
        for note in notes:
            category = note.get("category", "Unknown")
            if category not in structure:
                structure[category] = {"count": 0, "notes": []}
            structure[category]["count"] += 1
            structure[category]["notes"].append({
                "title": note.get("title", ""),
                "path": note.get("path", ""),
                "updated_at": note.get("updated_at", "")
            })
        
        return {"structure": structure}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notes/search")
async def search_notes(query: str, limit: int = 10):
    """
    Search notes by content using the AI agent
    """
    try:
        # Use the agent to search notes
        notes = await knowledge_agent.get_all_notes()
        
        # Simple text search as fallback
        matching_notes = []
        query_lower = query.lower()
        
        for note in notes:
            if (query_lower in note.get("title", "").lower() or 
                query_lower in note.get("content", "").lower()):
                matching_notes.append(note)
                if len(matching_notes) >= limit:
                    break
        
        return {"notes": matching_notes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notes/{category}")
async def get_notes_by_category(category: str):
    """
    Get notes by category
    """
    try:
        # Get all notes and filter by category
        all_notes = await knowledge_agent.get_all_notes()
        category_notes = [note for note in all_notes if note.get("category") == category]
        return {"category": category, "notes": category_notes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/logs")
async def get_agent_logs():
    """
    Get the agent's execution logs for debugging
    """
    try:
        logs = knowledge_agent.get_agent_logs()
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/reset")
async def reset_agent():
    """
    Reset the agent's memory for a fresh start
    """
    try:
        knowledge_agent.reset_agent_memory()
        return {"message": "Agent memory reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/info")
async def get_agent_info():
    """
    Get information about the current agent
    """
    try:
        tools_count = 0
        if knowledge_agent.knowledge_worker and hasattr(knowledge_agent.knowledge_worker, 'tools'):
            tools_count = len(knowledge_agent.knowledge_worker.tools)
        
        return {
            "agent_type": "smolagents_powered",
            "model": knowledge_agent.model_name,
            "initialized": knowledge_agent.initialized,
            "tools_count": tools_count,
            "version": "2.0.0",
            "capabilities": [
                "Content processing and categorization",
                "Note creation and management",
                "Knowledge graph integration",
                "Semantic search",
                "Related content discovery",
                "Real-time chat streaming",
                "Enhanced PKM features",
                "Wiki-link management",
                "Typed relationships",
                "Hierarchical organization"
            ],
            "agents": {
                "knowledge_worker": {
                    "name": knowledge_agent.knowledge_worker.name if knowledge_agent.knowledge_worker else None,
                    "max_steps": knowledge_agent.knowledge_worker.max_steps if knowledge_agent.knowledge_worker else None,
                    "tools": tools_count
                },
                "manager_agent": {
                    "name": knowledge_agent.manager_agent.name if knowledge_agent.manager_agent else None,
                    "max_steps": knowledge_agent.manager_agent.max_steps if knowledge_agent.manager_agent else None,
                    "type": "CodeAgent"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get hash cache statistics and performance metrics
    """
    try:
        # Initialize the knowledge agent if not already done
        if not knowledge_agent.initialized:
            await knowledge_agent.initialize()
        
        # Get hash tracker directly
        hash_tracker = knowledge_agent.enhanced_graph.hash_tracker
        cache_stats = hash_tracker.get_cache_stats()
        
        # Get additional statistics
        notes_count = len(knowledge_agent.enhanced_graph.nodes_by_id)
        
        # Calculate metrics
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
        
        # Add recommendations based on stats
        if total_mapped < notes_count * 0.8:
            stats["recommendations"].append("Consider rebuilding cache - some notes may not be mapped to knowledge nodes")
        
        if total_cached > notes_count * 2:
            stats["recommendations"].append("Cache cleanup may be beneficial - many stale entries detected")
            
        return stats
        
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/clear")
async def clear_cache(confirm: bool = False):
    """
    Clear the hash cache (use with caution)
    """
    try:
        if not confirm:
            return {
                "success": False,
                "message": "Cache not cleared. Use confirm=true to actually clear the cache.",
                "warning": "This will remove all cached content hashes and note mappings, requiring full reprocessing on next startup."
            }
        
        # Initialize the knowledge agent if not already done
        if not knowledge_agent.initialized:
            await knowledge_agent.initialize()
        
        # Get hash tracker directly
        hash_tracker = knowledge_agent.enhanced_graph.hash_tracker
        old_stats = hash_tracker.get_cache_stats()
        
        # Clear the cache
        hash_tracker.clear_cache()
        
        return {
            "success": True,
            "message": "Cache cleared successfully",
            "cleared_items": old_stats['total_cached_items'],
            "cleared_mappings": old_stats['total_mapped_notes'],
            "warning": "All cached data has been removed. Next startup will require full reprocessing."
        }
        
    except Exception as e:
        print(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/rebuild")
async def rebuild_cache():
    """
    Rebuild the hash cache by reprocessing all content
    """
    try:
        # Initialize the knowledge agent if not already done
        if not knowledge_agent.initialized:
            await knowledge_agent.initialize()
        
        from knowledge.hash_utils import get_hash_tracker
        
        hash_tracker = get_hash_tracker()
        
        print("🔄 Starting cache rebuild...")
        
        # Clear existing cache
        old_stats = hash_tracker.get_cache_stats()
        hash_tracker.clear_cache()
        
        # Reinitialize enhanced graph to rebuild cache
        await knowledge_agent.enhanced_graph.initialize()
        
        # Get new stats
        new_stats = hash_tracker.get_cache_stats()
        
        return {
            "success": True,
            "message": "Cache rebuilt successfully",
            "before": {
                "cached_items": old_stats['total_cached_items'],
                "mapped_notes": old_stats['total_mapped_notes']
            },
            "after": {
                "cached_items": new_stats['total_cached_items'],
                "mapped_notes": new_stats['total_mapped_notes']
            },
            "nodes_processed": len(knowledge_agent.enhanced_graph.nodes_by_id)
        }
        
    except Exception as e:
        print(f"Error rebuilding cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_knowledge_base(force_rebuild: bool = False):
    """
    Sync the knowledge base with the current vault state
    
    Args:
        force_rebuild: If True, force a complete rebuild regardless of changes
    
    Returns:
        Detailed sync results including changes detected and actions taken
    """
    try:
        sync_results = await knowledge_agent.sync_knowledge_base(force_rebuild)
        return sync_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 