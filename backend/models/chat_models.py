from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    content: str
    sender: str  # 'user' or 'agent'
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []

class KnowledgeUpdate(BaseModel):
    action: str  # 'added', 'updated', 'linked'
    category: str
    content: str
    node_id: Optional[str] = None

class AgentResponse(BaseModel):
    content: str
    categories: List[str] = []
    knowledge_updates: List[KnowledgeUpdate] = []
    suggested_actions: List[str] = []

class ChatResponse(BaseModel):
    response: str
    categories: List[str] = []
    knowledge_updates: List[KnowledgeUpdate] = []
    suggested_actions: List[str] = []

class SearchResult(BaseModel):
    content: str
    category: str
    similarity: float
    node_id: str
    metadata: Dict[str, Any] = {} 