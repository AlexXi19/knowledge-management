from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import asyncio
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
    """
    try:
        # Process the message through the smolagents knowledge agent
        response = await knowledge_agent.process_message(
            message=request.message,
            conversation_history=request.conversation_history
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint for real-time responses
    """
    try:
        async def generate():
            async for chunk in knowledge_agent.stream_response(
                message=request.message,
                conversation_history=request.conversation_history
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        return {
            "agent_type": "smolagents_powered",
            "model": knowledge_agent.model_name,
            "initialized": knowledge_agent.initialized,
            "tools_count": len(knowledge_agent.agent.tools) if knowledge_agent.agent else 0,
            "version": "2.0.0",
            "capabilities": [
                "Content processing and categorization",
                "Note creation and management",
                "Knowledge graph integration",
                "Semantic search",
                "Related content discovery",
                "Real-time chat streaming",
                "Multi-step reasoning"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get hash cache statistics and performance metrics
    """
    try:
        # Use the agent to get cache stats
        prompt = "Get cache statistics using the get_cache_stats tool"
        result = knowledge_agent.agent.run(prompt)
        
        try:
            # Try to parse the JSON result
            import json
            stats = json.loads(result)
            return stats
        except:
            # If parsing fails, return the raw result
            return {"raw_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/clear")
async def clear_cache(confirm: bool = False):
    """
    Clear the hash cache (use with caution)
    """
    try:
        confirm_str = "yes" if confirm else "no"
        prompt = f"Clear the cache with confirm='{confirm_str}' using the clear_cache tool"
        result = knowledge_agent.agent.run(prompt)
        
        try:
            import json
            response = json.loads(result)
            return response
        except:
            return {"raw_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/rebuild")
async def rebuild_cache():
    """
    Rebuild the hash cache by reprocessing all content
    """
    try:
        prompt = "Rebuild the cache using the rebuild_cache tool"
        result = knowledge_agent.agent.run(prompt)
        
        try:
            import json
            response = json.loads(result)
            return response
        except:
            return {"raw_result": result}
    except Exception as e:
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