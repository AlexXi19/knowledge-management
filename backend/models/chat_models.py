from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class ChatMessage(BaseModel):
    content: str
    sender: str = Field(alias="role", default="user")  # 'user' or 'agent'/'assistant'
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('sender', pre=True)
    def normalize_sender(cls, v):
        """Normalize different sender formats"""
        if v in ['assistant', 'ai', 'agent']:
            return 'agent'
        elif v in ['user', 'human']:
            return 'user'
        return v
    
    class Config:
        validate_by_name = True

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
    category: str = "General"
    similarity: float = Field(alias="score", default=1.0)
    node_id: str = ""
    metadata: Dict[str, Any] = {}
    
    @validator('similarity', pre=True)
    def normalize_similarity(cls, v):
        """Handle different score field names"""
        return float(v) if v is not None else 1.0
    
    class Config:
        validate_by_name = True 