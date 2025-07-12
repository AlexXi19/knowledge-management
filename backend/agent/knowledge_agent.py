# Simple knowledge agent without smolagents dependency
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import os
import asyncio
from datetime import datetime
import json

from models.chat_models import ChatMessage, AgentResponse, KnowledgeUpdate, SearchResult
from knowledge.knowledge_graph import KnowledgeGraph
from knowledge.categorizer import ContentCategorizer
from knowledge.content_processor import ContentProcessor
from knowledge.notes_manager import NotesManager
from models.chat_models import ChatMessage, ChatResponse, KnowledgeUpdate, SearchResult

class KnowledgeAgent:
    """
    Main agent that orchestrates knowledge management operations
    """
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self.categorizer = ContentCategorizer()
        self.content_processor = ContentProcessor()
        self.notes_manager = NotesManager()
        self.initialized = False
    
    async def initialize(self):
        """Initialize all components"""
        if self.initialized:
            return
        
        print("🚀 Initializing Knowledge Agent...")
        
        # Initialize all components
        await self.knowledge_graph.initialize()
        print("✅ Knowledge Graph initialized")
        
        await self.notes_manager.initialize()
        print("✅ Notes Manager initialized")
        
        # Process existing notes into knowledge graph
        await self._process_existing_notes()
        
        self.initialized = True
        print("🤖 Knowledge Agent is ready!")

    async def _process_existing_notes(self):
        """Process existing notes and add them to the knowledge graph"""
        notes = await self.notes_manager.get_all_notes()
        
        if not notes:
            print("📄 No existing notes found")
            return
        
        print(f"📚 Processing {len(notes)} existing notes...")
        
        for note in notes:
            try:
                # Add note to knowledge graph
                await self.knowledge_graph.add_node(
                    content=note.content,
                    category=note.category,
                    metadata={
                        "title": note.title,
                        "source": "existing_note",
                        "content_type": "note",
                        "tags": note.tags,
                        "timestamp": note.updated_at.isoformat(),
                        "note_path": note.path,
                        "created_at": note.created_at.isoformat()
                    }
                )
            except Exception as e:
                print(f"Error processing note {note.title}: {e}")
        
        print(f"✅ Processed {len(notes)} existing notes into knowledge graph")

    async def process_message(self, message: str, conversation_history: List[ChatMessage] = None) -> ChatResponse:
        """Process a user message and return a response"""
        if not self.initialized:
            await self.initialize()
        
        # Process the content
        processed_content = await self.content_processor.extract_content(message)
        
        # Categorize the content
        categories = await self.categorizer.categorize(processed_content.get("text", message))
        best_category = categories[0] if categories else "Quick Notes"
        
        # Decide whether to create new note or update existing
        action, existing_note = await self.notes_manager.decide_note_action(
            processed_content.get("text", message), best_category
        )
        
        note_action_taken = ""
        if action == "create":
            # Create new note
            note = await self.notes_manager.create_note(
                title=processed_content.get("title") or f"Note from {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=processed_content.get("text", message),
                category=best_category,
                tags=processed_content.get("tags", [])
            )
            note_action_taken = f"Created new note: '{note.title}'"
        else:
            # Update existing note
            note = await self.notes_manager.update_note(
                existing_note.path,
                processed_content.get("text", message)
            )
            note_action_taken = f"Updated existing note: '{note.title}'"
        
        # Add to knowledge graph
        await self.knowledge_graph.add_node(
            content=processed_content.get("text", message),
            category=best_category,
            metadata={
                "title": processed_content.get("title", ""),
                "source": processed_content.get("source", "user_input"),
                "content_type": processed_content.get("content_type", "text"),
                "tags": processed_content.get("tags", []),
                "timestamp": datetime.now().isoformat(),
                "original_message": message,
                "note_path": note.path,
                "note_action": action
            }
        )
        
        # Find related notes to suggest
        related_notes = await self.notes_manager.find_related_notes(
            processed_content.get("text", message), limit=3
        )
        
        # Generate response
        response_parts = [
            f"📝 {note_action_taken}",
            f"📁 Categorized as \"{best_category}\"",
        ]
        
        if processed_content.get("tags"):
            response_parts.append(f"🏷️  Tagged with: {', '.join(processed_content['tags'])}")
        
        if processed_content.get("source") and processed_content["source"] != "user_input":
            response_parts.append(f"🔗 Source: {processed_content['source']}")
        
        if related_notes:
            related_titles = [note.title for note in related_notes[:2]]
            response_parts.append(f"🔗 Related notes: {', '.join(related_titles)}")
        
        response_text = "\n\n".join(response_parts)
        
        # Create knowledge update
        knowledge_update = KnowledgeUpdate(
            action="added",
            category=best_category,
            content=processed_content.get("text", message),
            node_id=str(hash(processed_content.get("text", message)))  # Simple ID generation
        )
        
        # Generate suggestions
        suggestions = []
        if action == "create":
            suggestions.extend([
                "Add more details to this note",
                "Create connections to related topics",
                "Add relevant tags"
            ])
        else:
            suggestions.extend([
                "Review the updated note",
                "Add more context",
                "Link to other related notes"
            ])
        
        if related_notes:
            suggestions.append(f"Review related note: {related_notes[0].title}")
        
        return ChatResponse(
            response=response_text,
            categories=categories,
            knowledge_updates=[knowledge_update],
            suggested_actions=suggestions
        )
    
    async def stream_response(self, message: str, conversation_history: List[ChatMessage] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream processing updates"""
        if not self.initialized:
            await self.initialize()
        
        yield {"type": "status", "message": "Processing your message..."}
        
        # Process content
        processed_content = await self.content_processor.extract_content(message)
        yield {"type": "content", "data": processed_content}
        
        # Categorize
        categories = await self.categorizer.categorize(processed_content.get("text", message))
        best_category = categories[0] if categories else "Quick Notes"
        yield {"type": "category", "category": best_category}
        
        # Decide note action
        action, existing_note = await self.notes_manager.decide_note_action(
            processed_content.get("text", message), best_category
        )
        yield {"type": "decision", "action": action, "existing_note": existing_note.title if existing_note else None}
        
        # Execute note action
        if action == "create":
            note = await self.notes_manager.create_note(
                title=processed_content.get("title") or f"Note from {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=processed_content.get("text", message),
                category=best_category,
                tags=processed_content.get("tags", [])
            )
            yield {"type": "note_created", "note": note.to_dict()}
        else:
            note = await self.notes_manager.update_note(
                existing_note.path,
                processed_content.get("text", message)
            )
            yield {"type": "note_updated", "note": note.to_dict()}
        
        # Add to knowledge graph
        await self.knowledge_graph.add_node(
            content=processed_content.get("text", message),
            category=best_category,
            metadata={
                "title": processed_content.get("title", ""),
                "source": processed_content.get("source", "user_input"),
                "content_type": processed_content.get("content_type", "text"),
                "tags": processed_content.get("tags", []),
                "timestamp": datetime.now().isoformat(),
                "original_message": message,
                "note_path": note.path,
                "note_action": action
            }
        )
        
        # Find related notes
        related_notes = await self.notes_manager.find_related_notes(
            processed_content.get("text", message), limit=3
        )
        
        if related_notes:
            yield {"type": "related_notes", "notes": [note.to_dict() for note in related_notes]}
        
        yield {"type": "complete", "message": "Processing complete!"}
    
    async def get_knowledge_graph(self) -> Dict[str, Any]:
        """Get the knowledge graph data"""
        return await self.knowledge_graph.get_graph_data()
    
    async def get_categories(self) -> List[str]:
        """Get available categories"""
        return list(self.categorizer.categories.keys())
    
    async def search_knowledge(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search the knowledge base"""
        return await self.knowledge_graph.search(query, limit)
    
    async def get_notes_structure(self) -> Dict[str, Any]:
        """Get the notes directory structure"""
        return self.notes_manager.get_notes_structure()
    
    async def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all notes"""
        notes = await self.notes_manager.get_all_notes()
        return [note.to_dict() for note in notes]
    
    async def search_notes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search notes"""
        notes = await self.notes_manager.search_notes(query, limit)
        return [note.to_dict() for note in notes]
    
    async def get_note_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get a specific note by path"""
        if path in self.notes_manager.notes_index:
            return self.notes_manager.notes_index[path].to_dict()
        return None 