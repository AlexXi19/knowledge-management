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

app = FastAPI(title="Knowledge Management Agent", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the knowledge agent
knowledge_agent = KnowledgeAgent()

@app.on_event("startup")
async def startup_event():
    """Initialize the knowledge agent on startup"""
    await knowledge_agent.initialize()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "knowledge-agent"}

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
        structure = await knowledge_agent.get_notes_structure()
        return {
            "notes_directory": notes_dir,
            "structure": structure,
            "total_notes": sum(cat["count"] for cat in structure.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that processes user messages and returns agent responses
    """
    try:
        # Process the message through the knowledge agent
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
        categories = await knowledge_agent.get_categories()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/search")
async def search_knowledge(query: str, limit: int = 10):
    """
    Search the knowledge base
    """
    try:
        results = await knowledge_agent.search_knowledge(query, limit)
        return {"results": results}
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
        structure = await knowledge_agent.get_notes_structure()
        return {"structure": structure}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notes/search")
async def search_notes(query: str, limit: int = 10):
    """
    Search notes by content
    """
    try:
        notes = await knowledge_agent.search_notes(query, limit)
        return {"notes": notes}
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
        category_notes = [note for note in all_notes if note["category"] == category]
        return {"category": category, "notes": category_notes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 