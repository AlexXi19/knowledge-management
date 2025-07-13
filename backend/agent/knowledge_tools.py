"""
Custom tools for knowledge management operations using smolagents
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import asyncio
from smolagents import tool

from knowledge.enhanced_knowledge_graph import get_enhanced_knowledge_graph
from knowledge.categorizer import ContentCategorizer
from knowledge.content_processor import ContentProcessor
from knowledge.notes_manager import NotesManager
from models.chat_models import SearchResult


class KnowledgeToolsManager:
    """Manages the knowledge management tools and their shared state"""
    
    def __init__(self):
        self.knowledge_graph = None
        self.categorizer = None
        self.content_processor = None
        self.notes_manager = None
        self.initialized = False
        self.notes_directory = None
        self.knowledge_base_directory = None
    
    def setup_directories(self, notes_dir: str, knowledge_base_dir: str):
        """
        Set up the directories for notes and knowledge base
        
        Args:
            notes_dir: Directory where notes will be stored
            knowledge_base_dir: Directory where knowledge base data will be stored
        """
        self.notes_directory = notes_dir
        self.knowledge_base_directory = knowledge_base_dir
        
        # Create the components with the specified directories
        self.knowledge_graph = get_enhanced_knowledge_graph()
        self.categorizer = ContentCategorizer()
        self.content_processor = ContentProcessor()
        self.notes_manager = NotesManager(notes_directory=notes_dir)
        
        # Update the hash tracker to use the knowledge base directory
        from knowledge.hash_utils import get_hash_tracker
        hash_tracker = get_hash_tracker()
        hash_tracker.cache_file = f"{knowledge_base_dir}/hash_cache.json"
        # Reload cache from new location
        hash_tracker.hash_cache = hash_tracker._load_cache()
        hash_tracker.note_to_node_mapping = hash_tracker._load_mapping()
    
    async def initialize(self):
        """Initialize all components"""
        if self.initialized:
            return
        
        # Initialize with default directories if not set up yet
        if self.knowledge_graph is None:
            self.knowledge_graph = get_enhanced_knowledge_graph()
        if self.categorizer is None:
            self.categorizer = ContentCategorizer()
        if self.content_processor is None:
            self.content_processor = ContentProcessor()
        if self.notes_manager is None:
            self.notes_manager = NotesManager()
        
        print("🚀 Initializing Knowledge Management Tools...")
        
        # Initialize all components
        await self.knowledge_graph.initialize()
        await self.notes_manager.initialize()
        
        # Process existing notes into knowledge graph
        await self._process_existing_notes()
        
        self.initialized = True
        print("✅ Knowledge Management Tools initialized!")
    
    async def _process_existing_notes(self):
        """Process existing notes and add them to the knowledge graph"""
        notes = await self.notes_manager.get_all_notes()
        
        if not notes:
            print("📄 No existing notes found")
            return
        
        print(f"📚 Processing {len(notes)} existing notes...")
        
        for note in notes:
            try:
                # Add note to enhanced knowledge graph using add_note_from_content
                await self.knowledge_graph.add_note_from_content(
                    title=note.title,
                    content=note.content,
                    category=note.category,
                    tags=note.tags,
                    file_path=note.path
                )
            except Exception as e:
                print(f"Error processing note {note.title}: {e}")
        
        print(f"✅ Processed {len(notes)} existing notes into knowledge graph")


# Global instance for shared state
_knowledge_tools_manager = KnowledgeToolsManager()


def _run_async_safely(coro):
    """Run async coroutine safely, handling existing event loops"""
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're in an event loop, we need to use a different approach
        import concurrent.futures
        import threading
        
        # Create a new event loop in a separate thread
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        # Run the coroutine in a thread pool
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop running, we can use asyncio.run()
        return asyncio.run(coro)


@tool
def process_and_categorize_content(content: str, title: Optional[str] = None) -> str:
    """
    Process content and categorize it for knowledge management with caching.
    
    Args:
        content: The content to process and categorize
        title: Optional title for the content
        
    Returns:
        JSON string containing processed content with category and metadata
    """
    async def _process():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Check if we've already processed this content recently
        from knowledge.hash_utils import calculate_content_hash, get_hash_tracker
        
        content_hash = calculate_content_hash(content)
        cache_key = f"processed_content:{content_hash}"
        hash_tracker = get_hash_tracker()
        
        # Check if we have cached results
        if not hash_tracker.has_content_changed(cache_key, content):
            cache_entry = hash_tracker.hash_cache.get(cache_key, {})
            cached_result = cache_entry.get('metadata', {}).get('result')
            if cached_result:
                print(f"⚡ Using cached content processing for hash {content_hash[:8]}...")
                return cached_result
        
        # Process the content
        processed_content = await _knowledge_tools_manager.content_processor.extract_content(content)
        
        # Categorize the content
        categories = await _knowledge_tools_manager.categorizer.categorize(
            processed_content.get("text", content)
        )
        best_category = categories[0] if categories else "Quick Notes"
        
        result = {
            "processed_content": processed_content,
            "category": best_category,
            "all_categories": categories,
            "title": title or processed_content.get("title", ""),
            "content_hash": content_hash
        }
        
        result_json = json.dumps(result, indent=2)
        
        # Cache the result
        hash_tracker.update_hash(
            cache_key,
            content_hash,
            {
                "result": result_json,
                "processed_at": datetime.now().isoformat(),
                "category": best_category
            }
        )
        
        return result_json
    
    return _run_async_safely(_process())


@tool
def create_knowledge_note(content: str, category: str, title: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
    """
    Create a new knowledge note and add it to the knowledge graph with hash tracking.
    
    Args:
        content: The content of the note
        category: The category for the note
        title: Optional title for the note
        tags: Optional list of tags for the note
        
    Returns:
        JSON string containing the created note information
    """
    async def _create():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Create the note
        note = await _knowledge_tools_manager.notes_manager.create_note(
            title=title or f"Note from {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            content=content,
            category=category,
            tags=tags or []
        )
        
        # Add to enhanced knowledge graph
        node_id = await _knowledge_tools_manager.knowledge_graph.add_note_from_content(
            title=note.title,
            content=content,
            category=category,
            tags=note.tags,
            file_path=note.path
        )
        
        return json.dumps({
            "success": True,
            "note": note.to_dict(),
            "knowledge_node_id": node_id,
            "message": f"Created note: {note.title}",
            "cached": False
        }, indent=2)
    
    return _run_async_safely(_create())


@tool
def update_knowledge_note(note_path: str, additional_content: str) -> str:
    """
    Update an existing knowledge note with additional content and sync knowledge graph.
    
    Args:
        note_path: Path to the note to update
        additional_content: Additional content to add to the note
        
    Returns:
        JSON string containing the updated note information
    """
    async def _update():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Check if this content would actually change the note
        from knowledge.hash_utils import calculate_content_hash, get_hash_tracker
        
        hash_tracker = get_hash_tracker()
        
        # Get current note if it exists
        try:
            current_note = _knowledge_tools_manager.notes_manager.notes_index.get(note_path)
            if current_note:
                # Check if we're trying to add content that would result in the same hash
                test_content = current_note.content + f"\n\n## Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{additional_content}"
                if not current_note.has_content_changed(test_content):
                    return json.dumps({
                        "success": True,
                        "note": current_note.to_dict(),
                        "message": f"No changes needed for note: {current_note.title}",
                        "cached": True
                    }, indent=2)
        except Exception as e:
            print(f"Warning: Could not check for content changes: {e}")
        
        # Update the note
        note = await _knowledge_tools_manager.notes_manager.update_note(
            note_path, additional_content
        )
        
        # Update enhanced knowledge graph
        node_id = await _knowledge_tools_manager.knowledge_graph.add_note_from_content(
            title=note.title,
            content=note.content,
            category=note.category,
            tags=note.tags,
            file_path=note.path
        )
        
        return json.dumps({
            "success": True,
            "note": note.to_dict(),
            "knowledge_node_id": node_id,
            "message": f"Updated note: {note.title}",
            "cached": False
        }, indent=2)
    
    return _run_async_safely(_update())


@tool
def search_knowledge(query: str, limit: int = 10) -> str:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        JSON string containing search results
    """
    async def _search():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Search enhanced knowledge graph
        results = await _knowledge_tools_manager.knowledge_graph.search_semantic(query, limit)
        
        # Convert SearchResult objects to dictionaries
        results_dict = []
        for result in results:
            if hasattr(result, 'model_dump'):
                results_dict.append(result.model_dump())
            elif hasattr(result, 'to_dict'):
                results_dict.append(result.to_dict())
            else:
                # Handle if it's already a dict or create a basic dict
                results_dict.append({
                    "content": getattr(result, 'content', str(result)),
                    "category": getattr(result, 'category', 'Unknown'),
                    "similarity": getattr(result, 'similarity', 1.0),
                    "node_id": getattr(result, 'node_id', ''),
                    "metadata": getattr(result, 'metadata', {})
                })
        
        return json.dumps({
            "query": query,
            "results": results_dict,
            "count": len(results_dict)
        }, indent=2)
    
    return _run_async_safely(_search())


@tool
def find_related_notes(content: str, limit: int = 5) -> str:
    """
    Find notes related to the given content.
    
    Args:
        content: Content to find related notes for
        limit: Maximum number of related notes to return
        
    Returns:
        JSON string containing related notes
    """
    async def _find():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Find related notes
        related_notes = await _knowledge_tools_manager.notes_manager.find_related_notes(
            content, limit
        )
        
        return json.dumps({
            "query_content": content[:100] + "..." if len(content) > 100 else content,
            "related_notes": [note.to_dict() for note in related_notes],
            "count": len(related_notes)
        }, indent=2)
    
    return _run_async_safely(_find())


@tool
def get_knowledge_graph_data() -> str:
    """
    Get the current knowledge graph data structure.
    
    Returns:
        JSON string containing the knowledge graph data
    """
    async def _get_graph():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        graph_data = await _knowledge_tools_manager.knowledge_graph.get_graph_data()
        
        return json.dumps({
            "knowledge_graph": graph_data,
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    
    return _run_async_safely(_get_graph())


@tool
def get_all_notes() -> str:
    """
    Get all notes in the knowledge base.
    
    Returns:
        JSON string containing all notes
    """
    async def _get_all():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        notes = await _knowledge_tools_manager.notes_manager.get_all_notes()
        
        return json.dumps({
            "notes": [note.to_dict() for note in notes],
            "count": len(notes),
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    
    return _run_async_safely(_get_all())


@tool
def search_notes(query: str, limit: int = 10) -> str:
    """
    Search for notes matching the query.
    
    Args:
        query: The search query
        limit: Maximum number of notes to return
        
    Returns:
        JSON string containing matching notes
    """
    async def _search_notes():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        notes = await _knowledge_tools_manager.notes_manager.search_notes(query, limit)
        
        return json.dumps({
            "query": query,
            "notes": [note.to_dict() for note in notes],
            "count": len(notes)
        }, indent=2)
    
    return _run_async_safely(_search_notes())


@tool
def decide_note_action(content: str, category: str) -> str:
    """
    Decide whether to create a new note or update an existing one.
    
    Args:
        content: The content to process
        category: The category for the content
        
    Returns:
        JSON string containing the decision and any existing note information
    """
    async def _decide():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        action, existing_note = await _knowledge_tools_manager.notes_manager.decide_note_action(
            content, category
        )
        
        result = {
            "action": action,
            "existing_note": existing_note.to_dict() if existing_note else None,
            "recommendation": "create" if action == "create" else f"update existing note: {existing_note.title}" if existing_note else "create"
        }
        
        return json.dumps(result, indent=2)
    
    return _run_async_safely(_decide())


@tool
def get_cache_stats() -> str:
    """
    Get statistics about the hash cache and note mappings.
    
    Returns:
        JSON string containing cache statistics and performance metrics
    """
    async def _get_stats():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        from knowledge.hash_utils import get_hash_tracker
        
        hash_tracker = get_hash_tracker()
        cache_stats = hash_tracker.get_cache_stats()
        
        # Get additional statistics
        notes_count = len(_knowledge_tools_manager.notes_manager.notes_index)
        
        # Calculate cache hit rate if possible
        total_requests = cache_stats.get('total_requests', 0)
        cache_hits = cache_stats.get('cache_hits', 0)
        hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "cache_statistics": cache_stats,
            "notes_count": notes_count,
            "cache_hit_rate_percent": round(hit_rate, 2),
            "memory_efficiency": {
                "cached_items_vs_notes_ratio": round(cache_stats['total_cached_items'] / max(notes_count, 1), 2),
                "mapping_coverage_percent": round(cache_stats['total_mapped_notes'] / max(notes_count, 1) * 100, 2)
            },
            "recommendations": []
        }
        
        # Add recommendations based on stats
        if cache_stats['total_mapped_notes'] < notes_count * 0.8:
            stats["recommendations"].append("Consider rebuilding cache - some notes may not be mapped to knowledge nodes")
        
        if cache_stats['total_cached_items'] > notes_count * 2:
            stats["recommendations"].append("Cache cleanup may be beneficial - many stale entries detected")
        
        return json.dumps(stats, indent=2)
    
    return _run_async_safely(_get_stats())


@tool
def clear_cache(confirm: str = "no") -> str:
    """
    Clear the hash cache and note mappings (use with caution).
    
    Args:
        confirm: Must be "yes" to actually clear the cache
        
    Returns:
        JSON string containing the result of the cache clearing operation
    """
    if confirm.lower() != "yes":
        return json.dumps({
            "success": False,
            "message": "Cache not cleared. Use confirm='yes' to actually clear the cache.",
            "warning": "This will remove all cached content hashes and note mappings, requiring full reprocessing on next startup."
        }, indent=2)
    
    async def _clear():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        from knowledge.hash_utils import get_hash_tracker
        
        hash_tracker = get_hash_tracker()
        old_stats = hash_tracker.get_cache_stats()
        
        # Clear the cache
        hash_tracker.clear_cache()
        
        return json.dumps({
            "success": True,
            "message": "Cache cleared successfully",
            "cleared_items": old_stats['total_cached_items'],
            "cleared_mappings": old_stats['total_mapped_notes'],
            "warning": "All cached data has been removed. Next startup will require full reprocessing."
        }, indent=2)
    
    return _run_async_safely(_clear())


@tool
def rebuild_cache() -> str:
    """
    Rebuild the hash cache by reprocessing all notes and content.
    
    Returns:
        JSON string containing the result of the cache rebuilding operation
    """
    async def _rebuild():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        from knowledge.hash_utils import get_hash_tracker
        
        hash_tracker = get_hash_tracker()
        
        print("🔄 Starting cache rebuild...")
        
        # Clear existing cache
        old_stats = hash_tracker.get_cache_stats()
        hash_tracker.clear_cache()
        
        # Reinitialize notes manager to rebuild cache
        notes_manager = _knowledge_tools_manager.notes_manager
        notes_manager.notes_index.clear()
        await notes_manager._scan_existing_notes()
        
        # Get new stats
        new_stats = hash_tracker.get_cache_stats()
        
        return json.dumps({
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
            "notes_processed": len(notes_manager.notes_index)
        }, indent=2)
    
    return _run_async_safely(_rebuild())


# List of all available tools for easy import
KNOWLEDGE_TOOLS = [
    process_and_categorize_content,
    create_knowledge_note,
    update_knowledge_note,
    search_knowledge,
    find_related_notes,
    get_knowledge_graph_data,
    get_all_notes,
    search_notes,
    decide_note_action,
    get_cache_stats,
    clear_cache,
    rebuild_cache
] 